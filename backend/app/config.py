import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding
    embedding_model: str = "BAAI/bge-m3"
    hf_endpoint: str = "https://hf-mirror.com"  # 国内 HuggingFace 镜像，海外可留空
    hf_home: str = "D:\\develop\\huggingface"  # 模型缓存目录（默认 C 盘，改到 D 盘）

    # Storage
    database_url: str = "sqlite:///./data/app.db"
    chroma_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"

    # Cache（Redis 优先，连接失败自动降级为内存缓存）
    redis_url: str = "redis://localhost:6379/0"

    # Security
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Retrieval
    retrieval_top_k: int = 4
    # 检索相关度阈值（L2 距离，越小越相关；None 表示不过滤）。
    # bge-m3 归一化后：命中商品约 0.55-0.75，无关内容约 >0.9。
    retrieval_score_threshold: float | None = 0.75


settings = Settings()

# 国内访问 huggingface.co 慢，自动切到镜像（下载 BGE 模型用）
if settings.hf_endpoint:
    os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)
# 模型缓存放到 D 盘，避免占用 C 盘
if settings.hf_home:
    os.environ.setdefault("HF_HOME", settings.hf_home)
# 禁用 Xet 加速下载（否则会绕过镜像直连 AWS CDN，国内超时）
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
