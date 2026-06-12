"""
API Key Authentication.

Xác thực qua header X-API-Key.
Dùng hmac.compare_digest để tránh timing attack.
"""
import hmac
import json
import logging

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

logger = logging.getLogger(__name__)

# Header name cho API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key từ header X-API-Key.

    Returns:
        API key string nếu hợp lệ.

    Raises:
        HTTPException 401: nếu key thiếu hoặc sai.
    """
    if not api_key:
        logger.warning(json.dumps({
            "event": "auth_failed",
            "reason": "missing_api_key",
        }))
        raise HTTPException(
            status_code=401,
            detail="API key required. Include header: X-API-Key: <your-key>",
        )

    # Constant-time comparison để tránh timing attack
    if not hmac.compare_digest(api_key, settings.agent_api_key):
        logger.warning(json.dumps({
            "event": "auth_failed",
            "reason": "invalid_api_key",
        }))
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return api_key
