from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from ..config import settings


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """懒加载本地 BGE 向量模型（首次调用会下载模型，之后走缓存）。"""
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
