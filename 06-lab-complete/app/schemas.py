"""
Pydantic request/response models.

Tách riêng schemas để code gọn, dễ test, dễ generate docs.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ── Request Models ─────────────────────────────────────────

class AskRequest(BaseModel):
    """Request body cho POST /ask."""
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID người dùng — dùng để track conversation, rate limit, budget",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Câu hỏi gửi tới AI agent",
    )


# ── Response Models ────────────────────────────────────────

class AskResponse(BaseModel):
    """Response cho POST /ask."""
    user_id: str
    question: str
    answer: str
    model: str
    timestamp: str
    conversation_length: int


class HealthResponse(BaseModel):
    """Response cho GET /health."""
    status: str
    version: str
    environment: str
    uptime_seconds: float
    redis_status: str
    timestamp: str


class ReadyResponse(BaseModel):
    """Response cho GET /ready."""
    ready: bool
    redis: str


class MessageItem(BaseModel):
    """Một message trong conversation history."""
    role: str
    content: str
    timestamp: str


class HistoryResponse(BaseModel):
    """Response cho GET /users/{user_id}/history."""
    user_id: str
    messages: List[MessageItem]
    count: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str


class ServiceInfoResponse(BaseModel):
    """Response cho GET /."""
    app: str
    version: str
    environment: str
    endpoints: dict
