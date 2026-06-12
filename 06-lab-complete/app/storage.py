"""
Redis Storage — Stateless-compatible session & conversation management.

Production: PHẢI có Redis, fail nếu thiếu.
Development/Test: cho phép fallback in-memory (có warning).

Tất cả state (conversation, rate limit, cost) đều qua module này.
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# ── Redis Client ──────────────────────────────────────────

_redis_client = None
_use_redis = False


def init_redis():
    """
    Khởi tạo Redis connection.
    Gọi trong lifespan startup.
    """
    global _redis_client, _use_redis

    try:
        import redis
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        _redis_client.ping()
        _use_redis = True
        logger.info(json.dumps({
            "event": "redis_connected",
            "url": settings.redis_url.split("@")[-1],  # ẩn password
        }))
    except Exception as e:
        if settings.environment == "production":
            logger.error(json.dumps({
                "event": "redis_failed",
                "error": str(e),
            }))
            raise RuntimeError(
                f"Redis REQUIRED in production but unavailable: {e}"
            )
        else:
            _use_redis = False
            logger.warning(json.dumps({
                "event": "redis_fallback",
                "message": "Redis not available — using in-memory (NOT scalable!)",
            }))


def close_redis():
    """Đóng Redis connection khi shutdown."""
    global _redis_client, _use_redis
    if _redis_client and _use_redis:
        try:
            _redis_client.close()
            logger.info(json.dumps({"event": "redis_closed"}))
        except Exception:
            pass
    _redis_client = None
    _use_redis = False


def get_redis():
    """Lấy Redis client. Trả None nếu không có Redis."""
    return _redis_client if _use_redis else None


def redis_healthy() -> bool:
    """Check xem Redis có hoạt động không."""
    if not _use_redis or not _redis_client:
        return False
    try:
        _redis_client.ping()
        return True
    except Exception:
        return False


# ── In-memory fallback (chỉ cho dev/test) ─────────────────

_memory_store: Dict[str, list] = {}


# ── Conversation History ──────────────────────────────────

HISTORY_TTL = 86400  # 24 giờ
MAX_MESSAGES = 50    # tối đa 50 messages (25 turns)


def save_message(user_id: str, role: str, content: str):
    """Lưu một message vào conversation history."""
    message = json.dumps({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    key = f"history:{user_id}"

    if _use_redis and _redis_client:
        pipe = _redis_client.pipeline()
        pipe.rpush(key, message)
        pipe.ltrim(key, -MAX_MESSAGES, -1)  # giữ MAX_MESSAGES gần nhất
        pipe.expire(key, HISTORY_TTL)
        pipe.execute()
    else:
        if key not in _memory_store:
            _memory_store[key] = []
        _memory_store[key].append(message)
        if len(_memory_store[key]) > MAX_MESSAGES:
            _memory_store[key] = _memory_store[key][-MAX_MESSAGES:]


def get_history(user_id: str) -> List[dict]:
    """Lấy toàn bộ conversation history của user."""
    key = f"history:{user_id}"

    if _use_redis and _redis_client:
        raw_messages = _redis_client.lrange(key, 0, -1)
    else:
        raw_messages = _memory_store.get(key, [])

    return [json.loads(m) for m in raw_messages]


def delete_history(user_id: str) -> bool:
    """Xóa conversation history của user."""
    key = f"history:{user_id}"

    if _use_redis and _redis_client:
        deleted = _redis_client.delete(key)
        return deleted > 0
    else:
        return _memory_store.pop(key, None) is not None


def get_history_length(user_id: str) -> int:
    """Đếm số messages trong history."""
    key = f"history:{user_id}"

    if _use_redis and _redis_client:
        return _redis_client.llen(key)
    else:
        return len(_memory_store.get(key, []))
