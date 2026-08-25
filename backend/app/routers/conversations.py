from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Conversation, Message, User
from ..schemas import ConversationCreate, ConversationOut, MessageOut

router = APIRouter()


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(desc(Conversation.updated_at))
        .all()
    )


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(user_id=user.id, title=(body.title or "新会话").strip() or "新会话")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_conv(db, conversation_id, user.id)
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id)
        .all()
    )


@router.patch("/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_conv(db, conversation_id, user.id)
    if body.title and body.title.strip():
        conv.title = body.title.strip()
        db.commit()
    return {"detail": "ok"}


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_conv(db, conversation_id, user.id)
    db.delete(conv)
    db.commit()
    return {"detail": "ok"}


def _get_conv(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv
