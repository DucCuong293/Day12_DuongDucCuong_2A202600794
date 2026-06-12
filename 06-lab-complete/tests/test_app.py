"""
Test suite cho Production AI Agent — Day 12 Lab.

Bao gồm:
  1. Health check returns 200
  2. Ready returns 200 khi Redis OK
  3. Ask without API key returns 401
  4. Ask with wrong key returns 401
  5. Ask with correct key returns 200
  6. Invalid body returns 422
  7. Conversation history persists
  8. Rate limit returns 429 after threshold
  9. Cost guard returns 402 when budget exceeded
"""
import time


class TestHealth:
    """Test /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "redis_status" in data

    def test_health_has_timestamp(self, client):
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data


class TestReady:
    """Test /ready endpoint."""

    def test_ready_returns_200_when_redis_ok(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True


class TestAuthentication:
    """Test API key authentication."""

    def test_ask_without_key_returns_401(self, client):
        response = client.post(
            "/ask",
            json={"user_id": "test", "question": "Hello"},
        )
        assert response.status_code == 401

    def test_ask_with_wrong_key_returns_401(self, client):
        response = client.post(
            "/ask",
            headers={"X-API-Key": "wrong-key-12345"},
            json={"user_id": "test", "question": "Hello"},
        )
        assert response.status_code == 401

    def test_ask_with_correct_key_returns_200(self, client, auth_headers):
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": "test_user", "question": "Hello agent!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["user_id"] == "test_user"
        assert data["question"] == "Hello agent!"
        assert "timestamp" in data
        assert "model" in data

    def test_history_without_key_returns_401(self, client):
        response = client.get("/users/test/history")
        assert response.status_code == 401


class TestValidation:
    """Test input validation."""

    def test_missing_user_id_returns_422(self, client, auth_headers):
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"question": "Hello"},
        )
        assert response.status_code == 422

    def test_missing_question_returns_422(self, client, auth_headers):
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": "test"},
        )
        assert response.status_code == 422

    def test_empty_question_returns_422(self, client, auth_headers):
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": "test", "question": ""},
        )
        assert response.status_code == 422

    def test_invalid_body_returns_422(self, client, auth_headers):
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"invalid": "data"},
        )
        assert response.status_code == 422


class TestConversationHistory:
    """Test conversation history persistence."""

    def test_conversation_history_persists(self, client, auth_headers):
        user_id = "history_test_user"

        # Gửi 2 messages
        client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": user_id, "question": "My name is Alice"},
        )
        client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": user_id, "question": "What is Docker?"},
        )

        # Kiểm tra history
        response = client.get(
            f"/users/{user_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["count"] == 4  # 2 user + 2 assistant messages
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "My name is Alice"
        assert data["messages"][1]["role"] == "assistant"

    def test_delete_history(self, client, auth_headers):
        user_id = "delete_test_user"

        # Tạo history
        client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": user_id, "question": "Hello"},
        )

        # Xóa
        response = client.delete(
            f"/users/{user_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify đã xóa
        response = client.get(
            f"/users/{user_id}/history",
            headers=auth_headers,
        )
        assert response.json()["count"] == 0


class TestRateLimit:
    """Test rate limiting."""

    def test_rate_limit_returns_429_after_threshold(self, client, auth_headers):
        user_id = "rate_limit_test"

        # Gửi đúng limit (10 requests)
        for i in range(10):
            response = client.post(
                "/ask",
                headers=auth_headers,
                json={"user_id": user_id, "question": f"Test {i}"},
            )
            assert response.status_code == 200, f"Request {i} failed: {response.status_code}"

        # Request thứ 11 phải bị reject
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": user_id, "question": "This should be rate limited"},
        )
        assert response.status_code == 429
        assert "Rate limit" in response.json()["detail"]


class TestCostGuard:
    """Test cost guard (budget limit)."""

    def test_cost_guard_returns_402_when_budget_exceeded(self, client, auth_headers):
        user_id = "budget_test_user"

        # Giả lập budget đã gần hết bằng cách set qua storage module
        from datetime import datetime
        from app.cost_guard import _memory_budgets
        from app import storage

        month_key = datetime.now().strftime("%Y-%m")
        budget_key = f"budget:{user_id}:{month_key}"

        # Set budget gần hết qua cả Redis (nếu có) và memory fallback
        redis_client = storage.get_redis()
        if redis_client:
            redis_client.set(budget_key, "10.0")
        else:
            _memory_budgets[budget_key] = 10.0

        # Request tiếp theo sẽ vượt budget
        response = client.post(
            "/ask",
            headers=auth_headers,
            json={"user_id": user_id, "question": "This should exceed budget"},
        )
        assert response.status_code == 402
        assert "budget" in response.json()["detail"].lower()


class TestServiceInfo:
    """Test root endpoint."""

    def test_root_returns_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "endpoints" in data


class TestMetrics:
    """Test metrics endpoint."""

    def test_metrics_requires_auth(self, client):
        response = client.get("/metrics")
        assert response.status_code == 401

    def test_metrics_with_auth(self, client, auth_headers):
        response = client.get("/metrics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "redis_connected" in data
