"""
Production AI Agent — Kết hợp tất cả Day 12 concepts.

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Redis-backed Rate limiting (sliding window)
  ✅ Redis-backed Cost guard (monthly per user)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown (lifespan + SIGTERM)
  ✅ Security headers
  ✅ CORS from env
  ✅ Stateless design — tất cả state trong Redis
  ✅ Conversation history (Redis)
  ✅ Docs disabled in production
"""
import time
import signal
import json
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.logging_config import setup_logging
from app.auth import verify_api_key
from app.schemas import (
    AskRequest, AskResponse,
    HealthResponse, ReadyResponse,
    HistoryResponse, MessageItem,
)
from app import storage
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_budget, estimate_cost, record_cost, get_current_spending

# Structured logging — phải setup trước khi dùng
setup_logging()
logger = logging.getLogger(__name__)

# Mock LLM (thay bằng OpenAI/Anthropic khi có API key)
from utils.mock_llm import ask as llm_ask

# ─────────────────────────────────────────────────────────
# Globals (read-only hoặc process-level — không phải user state)
# ─────────────────────────────────────────────────────────
START_TIME = time.time()


# ─────────────────────────────────────────────────────────
# Lifespan — startup & shutdown
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle:
    - Startup: init Redis, log service info
    - Shutdown: close Redis, log graceful exit
    """
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "rate_limit": settings.rate_limit_per_minute,
        "monthly_budget": settings.monthly_budget_usd,
    }))

    # Init Redis
    storage.init_redis()
    logger.info(json.dumps({"event": "ready", "redis": storage.redis_healthy()}))

    yield

    # Shutdown — đóng Redis sạch sẽ
    logger.info(json.dumps({"event": "shutdown", "uptime_seconds": round(time.time() - START_TIME, 1)}))
    storage.close_redis()


# ─────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

# CORS — từ env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


# ─────────────────────────────────────────────────────────
# Middleware — Security headers + Request logging
# ─────────────────────────────────────────────────────────
@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    start = time.time()
    try:
        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if "server" in response.headers:
            del response.headers["server"]

        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        logger.error(json.dumps({
            "event": "request_error",
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
        }))
        raise


# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    """Service info — không cần authentication."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "history": "GET /users/{user_id}/history",
        },
    }


@app.get("/health", tags=["Operations"])
def health():
    """
    Liveness probe — platform restarts container nếu endpoint này fail.

    Trả về: uptime, version, environment, Redis status.
    """
    redis_ok = storage.redis_healthy()
    redis_status = "connected" if redis_ok else "disconnected"

    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "redis_status": redis_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """
    Readiness probe — load balancer ngừng route traffic nếu not ready.

    Trả 200 khi Redis OK, 503 khi dependency fail.
    """
    redis_ok = storage.redis_healthy()

    if not redis_ok:
        # Trong dev mode cho phép chạy không Redis
        if settings.environment in ("development", "test"):
            return {"ready": True, "redis": "fallback_memory"}
        raise HTTPException(
            status_code=503,
            detail="Not ready: Redis unavailable",
        )

    return {"ready": True, "redis": "connected"}


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Gửi câu hỏi tới AI agent.

    **Authentication:** Header `X-API-Key: <your-key>`
    **Body:** `{"user_id": "...", "question": "..."}`

    Rate limit: 10 req/min per user.
    Budget: $10/month per user.
    """
    user_id = body.user_id

    # 1. Rate limit check (Redis-backed)
    check_rate_limit(user_id)

    # 2. Budget check (Redis-backed)
    input_tokens = len(body.question.split()) * 2  # rough estimate
    estimated = estimate_cost(input_tokens, 100)     # estimate output
    check_budget(user_id, estimated)

    # 3. Log request
    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": user_id,
        "q_len": len(body.question),
        "client": str(request.client.host) if request.client else "unknown",
    }))

    # 4. Lưu câu hỏi vào conversation history
    storage.save_message(user_id, "user", body.question)

    # 5. Gọi LLM (mock)
    answer = llm_ask(body.question)

    # 6. Lưu câu trả lời vào history
    storage.save_message(user_id, "assistant", answer)

    # 7. Ghi nhận cost thực tế
    output_tokens = len(answer.split()) * 2
    actual_cost = estimate_cost(input_tokens, output_tokens)
    record_cost(user_id, actual_cost)

    return AskResponse(
        user_id=user_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        conversation_length=storage.get_history_length(user_id),
    )


@app.get("/users/{user_id}/history", tags=["Agent"])
def get_user_history(
    user_id: str,
    _key: str = Depends(verify_api_key),
):
    """Xem conversation history của user. Yêu cầu authentication."""
    messages = storage.get_history(user_id)
    return {
        "user_id": user_id,
        "messages": messages,
        "count": len(messages),
    }


@app.delete("/users/{user_id}/history", tags=["Agent"])
def delete_user_history(
    user_id: str,
    _key: str = Depends(verify_api_key),
):
    """Xóa conversation history của user. Yêu cầu authentication."""
    deleted = storage.delete_history(user_id)
    return {
        "user_id": user_id,
        "deleted": deleted,
    }


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Basic metrics (protected). Cần API key."""
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "redis_connected": storage.redis_healthy(),
        "environment": settings.environment,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "monthly_budget_usd": settings.monthly_budget_usd,
    }


# ─────────────────────────────────────────────────────────
# Graceful Shutdown — handle SIGTERM from container orchestrator
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    """Handle SIGTERM — log và để uvicorn graceful shutdown."""
    logger.info(json.dumps({
        "event": "signal_received",
        "signal": "SIGTERM" if signum == signal.SIGTERM else str(signum),
        "uptime_seconds": round(time.time() - START_TIME, 1),
    }))

signal.signal(signal.SIGTERM, _handle_signal)


# ─────────────────────────────────────────────────────────
# Direct run
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
