import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# 确保 SQLite 数据目录存在
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
