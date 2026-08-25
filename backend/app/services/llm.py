from functools import lru_cache

from langchain_openai import ChatOpenAI

from ..config import settings


@lru_cache
def get_llm(streaming: bool = False) -> ChatOpenAI:
    """DeepSeek 提供 OpenAI 兼容接口，直接用 ChatOpenAI 接入。"""
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        streaming=streaming,
    )
