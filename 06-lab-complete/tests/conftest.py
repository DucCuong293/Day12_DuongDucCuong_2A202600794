"""
Pytest fixtures cho Day 12 Lab tests.

Dùng fakeredis để test Redis operations mà không cần Redis server thật.
Override storage module để inject fakeredis.
"""
import os
import sys
import pytest
from unittest.mock import patch
from pathlib import Path

# Đảm bảo project root (06-lab-complete/) nằm trong sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set env vars TRƯỚC khi import app modules
os.environ["AGENT_API_KEY"] = "test-secret-key-12345"
os.environ["ENVIRONMENT"] = "test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["RATE_LIMIT_PER_MINUTE"] = "10"
os.environ["MONTHLY_BUDGET_USD"] = "10"
os.environ["LOG_LEVEL"] = "WARNING"

import fakeredis
from fastapi.testclient import TestClient

from app import storage
from app.rate_limiter import _memory_windows
from app.cost_guard import _memory_budgets


@pytest.fixture(autouse=True)
def setup_fakeredis():
    """
    Trước mỗi test:
    - Tạo fakeredis instance
    - Inject vào storage module
    - Sau test: cleanup
    """
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    # Inject fakeredis
    storage._redis_client = fake_redis
    storage._use_redis = True

    # Clear in-memory fallbacks
    storage._memory_store.clear()
    _memory_windows.clear()
    _memory_budgets.clear()

    yield fake_redis

    # Cleanup
    fake_redis.flushall()
    storage._redis_client = None
    storage._use_redis = False


@pytest.fixture
def client(setup_fakeredis):
    """FastAPI TestClient với fakeredis đã inject."""
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api_key():
    """API key cho testing."""
    return "test-secret-key-12345"


@pytest.fixture
def auth_headers(api_key):
    """Headers có API key."""
    return {"X-API-Key": api_key}
