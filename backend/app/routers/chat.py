import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.limiter import limiter
from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..models import Conversation, Message, User
from ..services import rag
from ..services.cache import answer_cache, cache_key
from ..services.llm import get_llm

logger = logging.getLogger("rag.chat")

router = APIRouter()


class ChatIn(BaseModel):
    question: str
    kb_id: int | None = None


@router.post("/{conversation_id}")
@limiter.limit("10/minute")
async def chat(
    conversation_id: int,
    body: ChatIn,
    request: Request,
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

    ckey = cache_key(body.kb_id, body.question)
    cached = answer_cache.get(ckey)

    async def event_stream():
        full_answer = ""
        citations = []
        try:
            if cached is not None:
                # 命中缓存：直接返回上次的检索结果与回答
                citations = cached["citations"]
                full_answer = cached["answer"]
                yield _sse({"type": "citations", "data": citations})
                if full_answer:
                    yield _sse({"type": "token", "data": full_answer})
                logger.info("缓存命中 kb=%s q=%r", body.kb_id, body.question)
            else:
                # 3. 检索 + 构建 prompt（计时观测）
                t0 = time.time()
                citations = rag.retrieve(body.question, body.kb_id)
                t_retrieve = time.time() - t0
                prompt = rag.build_prompt(body.question, citations, history)
                llm = get_llm(streaming=True)
                yield _sse({"type": "citations", "data": citations})

                t1 = time.time()
                async for chunk in llm.astream(prompt):
                    token = getattr(chunk, "content", "") or ""
                    if token:
                        full_answer += token
                        yield _sse({"type": "token", "data": token})
                t_gen = time.time() - t1

                answer_cache.set(ckey, {"citations": citations, "answer": full_answer})
                logger.info(
                    "chat kb=%s q=%r 检索=%.3fs 生成=%.3fs 引用=%d",
                    body.kb_id, body.question, t_retrieve, t_gen, len(citations),
                )

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
