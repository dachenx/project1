from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.security import hash_password
from .database import Base, SessionLocal, engine
from .models import User
from .routers import auth, chat, conversations, kb


def seed_admin() -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first() is None:
            db.add(
                User(username="admin", password_hash=hash_password("123456"), role="admin")
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin()
    yield


app = FastAPI(title="RAG 企业级知识库问答系统", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发期放开，生产需收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(kb.router, prefix="/api/kb", tags=["knowledge-base"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
