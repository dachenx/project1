import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.limiter import limiter
from .core.security import hash_password
from .database import Base, SessionLocal, engine
from .models import User
from .routers import auth, chat, conversations, kb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


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

# 限流：按客户端 IP 计数，防止接口被恶意高频调用
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
