"""Chat API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.chat import ChatMessage, ChatSession
from ...models.strategy import Strategy
from ...models.strategy_version import StrategyVersion
from ...schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatReplyResponse,
    ChatSessionResponse,
)
from ...services.agent_service import generate_strategy_from_prompt

router = APIRouter()


def _assistant_reply_for_prompt(db: Session, prompt: str) -> tuple[str, dict, int | None]:
    normalized = (prompt or "").strip()
    if not normalized:
        return "请输入有效问题。", {}, None

    lower = normalized.lower()
    if any(token in lower for token in ["生成策略", "strategy", "rsi", "均线", "momentum"]):
        generated = generate_strategy_from_prompt(normalized)
        strategy = Strategy(
            name=f"Chat {generated.strategy_type} strategy",
            description=f"Generated from chat prompt: {normalized[:120]}",
            strategy_type=generated.strategy_type,
            parameters=generated.parameters,
            code=generated.code,
            created_from_chat=True,
        )
        db.add(strategy)
        db.flush()

        version = StrategyVersion(
            strategy_id=strategy.id,
            version_no=1,
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type,
            parameters=strategy.parameters,
            code=strategy.code,
            note="initial from chat",
            created_by="chat",
        )
        db.add(version)
        db.flush()

        content = (
            f"已生成策略 `{strategy.name}`（type={generated.strategy_type}）。\n"
            "你可以在策略页直接运行回测，或用 Agent 调参接口继续优化。"
        )
        meta = {
            "intent": "generate_strategy",
            "strategy_type": generated.strategy_type,
            "parameters": generated.parameters,
        }
        return content, meta, strategy.id

    return "我可以帮你生成策略、调参和复盘报告。请描述你的策略想法。", {"intent": "general"}, None


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(db: Session = Depends(get_db)):
    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def list_messages(
    session_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .limit(limit)
        .all()
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatReplyResponse)
async def post_message(
    session_id: int,
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.content.strip(),
    )
    db.add(user_message)
    db.flush()

    reply_content, metadata, created_strategy_id = _assistant_reply_for_prompt(db, payload.content)
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply_content,
        message_metadata=metadata,
        created_strategy_id=created_strategy_id,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(session)
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ChatReplyResponse(
        session=ChatSessionResponse.model_validate(session),
        user_message=ChatMessageResponse.model_validate(user_message),
        assistant_message=ChatMessageResponse.model_validate(assistant_message),
    )
