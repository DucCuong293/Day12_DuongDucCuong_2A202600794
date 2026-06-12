"""
Redis-backed Sliding Window Rate Limiter.

Algorithm: Sorted Set sliding window
- Key:    rate:{user_id}
- Score:  timestamp (epoch seconds)
- Member: unique request id (timestamp + random)

Mỗi request:
1. ZREMRANGEBYSCORE — xóa entries cũ hơn 60s
2. ZCARD — đếm entries còn lại
3. Nếu >= limit → reject 429
4. ZADD — thêm entry mới
"""
import time
import json
import uuid
import logging
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings
from app import storage

logger = logging.getLogger(__name__)


# In-memory fallback (chỉ cho dev/test khi không có Redis)
_memory_windows: dict = defaultdict(deque)


def check_rate_limit(user_id: str):
    """
    Kiểm tra rate limit cho user.

    Raises:
        HTTPException 429: nếu vượt limit.
    """
    redis_client = storage.get_redis()

    if redis_client:
        _check_redis(redis_client, user_id)
    else:
        _check_memory(user_id)


def _check_redis(redis_client, user_id: str):
    """Sliding window rate limit dùng Redis Sorted Set."""
    key = f"rate:{user_id}"
    now = time.time()
    window_start = now - 60  # 60-second window

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # xóa entries cũ
    pipe.zcard(key)                                # đếm entries
    pipe.zadd(key, {f"{now}:{uuid.uuid4().hex[:8]}": now})  # thêm mới
    pipe.expire(key, 120)                          # TTL 2 phút (safety)
    results = pipe.execute()

    current_count = results[1]  # kết quả ZCARD

    if current_count >= settings.rate_limit_per_minute:
        # Xóa entry vừa thêm vì request bị reject
        redis_client.zrem(key, f"{now}:{uuid.uuid4().hex[:8]}")
        logger.warning(json.dumps({
            "event": "rate_limit_exceeded",
            "user_id": user_id,
            "count": current_count,
            "limit": settings.rate_limit_per_minute,
        }))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests/minute. Try again later.",
            headers={"Retry-After": "60"},
        )


def _check_memory(user_id: str):
    """Fallback in-memory sliding window (không scalable)."""
    now = time.time()
    window = _memory_windows[user_id]

    # Xóa entries cũ hơn 60s
    while window and window[0] < now - 60:
        window.popleft()

    if len(window) >= settings.rate_limit_per_minute:
        logger.warning(json.dumps({
            "event": "rate_limit_exceeded",
            "user_id": user_id,
            "count": len(window),
            "limit": settings.rate_limit_per_minute,
            "backend": "memory",
        }))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests/minute.",
            headers={"Retry-After": "60"},
        )

    window.append(now)
