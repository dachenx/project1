import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import Conversation, Message, User
from ..services import rag
from ..services.llm import get_llm

router = APIRouter()


class ChatIn(BaseModel):
    question: str
    kb_id: int | None = None


@router.post("/{conversation_id}")
async def chat(
    conversation_id: int,
    body: ChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 1. 保存用户消息
    db.add(Message(conversation_id=conversation_id, role="user", content=body.question))
    if conv.title == "新会话":
        conv.title = body.question[:30]
    db.commit()

    # 2. 取最近历史（供多轮对话）
    recent = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(6)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(recent)][:-1]

    # 3. 检索 + 构建 prompt
    citations = rag.retrieve(body.question, body.kb_id)
    prompt = rag.build_prompt(body.question, citations, history)
    llm = get_llm(streaming=True)

    async def event_stream():
        full_answer = ""
        try:
            yield _sse({"type": "citations", "data": citations})
            async for chunk in llm.astream(prompt):
                token = getattr(chunk, "content", "") or ""
                if token:
                    full_answer += token
                    yield _sse({"type": "token", "data": token})

            s = SessionLocal()
            try:
                msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_answer,
                    citations=citations,
                )
                s.add(msg)
                s.commit()
                s.refresh(msg)
                message_id = msg.id
            finally:
                s.close()
            yield _sse({"type": "done", "data": {"message_id": message_id}})
        except Exception as e:  # noqa: BLE001
            yield _sse({"type": "error", "data": str(e)})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


def _sse(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False) + "\n"
