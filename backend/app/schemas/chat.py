"""Schemas for chat assistant APIs."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionResponse(BaseModel):
    id: int
    started_at: datetime | None = None
    last_activity: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    message_metadata: dict[str, Any] | None = None
    created_strategy_id: int | None = None
    timestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatReplyResponse(BaseModel):
    session: ChatSessionResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
