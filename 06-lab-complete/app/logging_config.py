"""
Structured JSON Logging Configuration.

Tất cả log đều ở dạng JSON để dễ parse bằng ELK, CloudWatch, etc.
"""
import logging
import json
import sys
from datetime import datetime, timezone

from app.config import settings


class JSONFormatter(logging.Formatter):
    """Format log records thành JSON structured."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Thêm exception info nếu có
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging():
    """Cấu hình structured JSON logging cho toàn app."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Xóa handlers cũ
    root_logger.handlers.clear()

    # Console handler với JSON format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Giảm noise từ uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger
