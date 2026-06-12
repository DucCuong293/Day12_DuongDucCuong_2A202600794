"""
Redis-backed Monthly Cost Guard.

Theo dõi chi phí LLM hàng tháng cho mỗi user.
- Key:    budget:{user_id}:{YYYY-MM}
- Value:  tổng chi phí USD (float)
- TTL:    32 ngày (tự hết hạn sau khi qua tháng)

Mỗi request:
1. Tính estimated cost
2. Check current spending + estimated <= budget
3. Nếu vượt → reject 402
4. Nếu OK → INCRBYFLOAT thêm cost
"""
import json
import time
import logging
from datetime import datetime

from fastapi import HTTPException

from app.config import settings
from app import storage

logger = logging.getLogger(__name__)

# In-memory fallback
_memory_budgets: dict = {}

# Cost per token (giả lập giá GPT-4o-mini)
INPUT_COST_PER_1K = 0.00015   # $0.15 / 1M input tokens
OUTPUT_COST_PER_1K = 0.0006   # $0.60 / 1M output tokens
BUDGET_TTL = 32 * 24 * 3600   # 32 ngày


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Tính chi phí ước tính cho một request."""
    return (input_tokens / 1000) * INPUT_COST_PER_1K + \
           (output_tokens / 1000) * OUTPUT_COST_PER_1K


def check_budget(user_id: str, estimated_cost: float):
    """
    Kiểm tra và ghi nhận chi phí cho user.

    Raises:
        HTTPException 402: nếu vượt monthly budget.
    """
    redis_client = storage.get_redis()

    if redis_client:
        _check_redis(redis_client, user_id, estimated_cost)
    else:
        _check_memory(user_id, estimated_cost)


def record_cost(user_id: str, actual_cost: float):
    """Ghi nhận chi phí thực tế sau khi LLM response."""
    redis_client = storage.get_redis()

    if redis_client:
        month_key = datetime.now().strftime("%Y-%m")
        key = f"budget:{user_id}:{month_key}"
        redis_client.incrbyfloat(key, actual_cost)
        redis_client.expire(key, BUDGET_TTL)
    else:
        month_key = datetime.now().strftime("%Y-%m")
        mem_key = f"budget:{user_id}:{month_key}"
        _memory_budgets[mem_key] = _memory_budgets.get(mem_key, 0.0) + actual_cost


def get_current_spending(user_id: str) -> float:
    """Lấy tổng chi phí tháng hiện tại của user."""
    month_key = datetime.now().strftime("%Y-%m")
    redis_client = storage.get_redis()

    if redis_client:
        key = f"budget:{user_id}:{month_key}"
        val = redis_client.get(key)
        return float(val) if val else 0.0
    else:
        mem_key = f"budget:{user_id}:{month_key}"
        return _memory_budgets.get(mem_key, 0.0)


def _check_redis(redis_client, user_id: str, estimated_cost: float):
    """Check budget dùng Redis."""
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = redis_client.get(key)
    current_cost = float(current) if current else 0.0

    if current_cost + estimated_cost > settings.monthly_budget_usd:
        logger.warning(json.dumps({
            "event": "budget_exceeded",
            "user_id": user_id,
            "current_usd": round(current_cost, 4),
            "estimated_usd": round(estimated_cost, 6),
            "budget_usd": settings.monthly_budget_usd,
            "month": month_key,
        }))
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget exceeded: ${current_cost:.4f} / ${settings.monthly_budget_usd:.2f}. Resets next month.",
        )

    # Ghi nhận cost
    redis_client.incrbyfloat(key, estimated_cost)
    redis_client.expire(key, BUDGET_TTL)


def _check_memory(user_id: str, estimated_cost: float):
    """Fallback in-memory budget check."""
    month_key = datetime.now().strftime("%Y-%m")
    mem_key = f"budget:{user_id}:{month_key}"

    current_cost = _memory_budgets.get(mem_key, 0.0)

    if current_cost + estimated_cost > settings.monthly_budget_usd:
        logger.warning(json.dumps({
            "event": "budget_exceeded",
            "user_id": user_id,
            "current_usd": round(current_cost, 4),
            "budget_usd": settings.monthly_budget_usd,
            "backend": "memory",
        }))
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget exceeded: ${current_cost:.4f} / ${settings.monthly_budget_usd:.2f}.",
        )

    _memory_budgets[mem_key] = current_cost + estimated_cost
