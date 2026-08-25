import hashlib
import json
import logging
import threading
import time

import redis as redis_lib

from ..config import settings

logger = logging.getLogger("rag.cache")


class _MemoryCache:
    """内存缓存（Redis 不可用时的降级实现）。"""

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[object, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expires = item
            if time.time() > expires:
                self._data.pop(key, None)
                return None
            return value

    def set(self, key: str, value, ttl: int | None = None) -> None:
        with self._lock:
            self._data[key] = (value, time.time() + (ttl or self._ttl))


class RedisCache:
    """Redis 缓存，连接失败时自动降级为内存缓存，保证应用不中断。"""

    def __init__(self, url: str, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._fallback = _MemoryCache(ttl_seconds)
        self._redis: redis_lib.Redis | None = None
        try:
            self._redis = redis_lib.from_url(
                url, decode_responses=True, socket_connect_timeout=1
            )
            self._redis.ping()
            logger.info("Redis 缓存已连接: %s", url)
        except Exception as e:  # noqa: BLE001
            self._redis = None
            logger.warning("Redis 不可用，降级为内存缓存: %s", e)

    def get(self, key: str):
        if self._redis is not None:
            try:
                raw = self._redis.get(key)
                return json.loads(raw) if raw is not None else None
            except Exception as e:  # noqa: BLE001
                logger.warning("Redis 读取失败，回退内存: %s", e)
        return self._fallback.get(key)

    def set(self, key: str, value) -> None:
        if self._redis is not None:
            try:
                self._redis.set(key, json.dumps(value, ensure_ascii=False), ex=self._ttl)
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("Redis 写入失败，回退内存: %s", e)
        self._fallback.set(key, value)


# 问答结果缓存：相同问题（同知识库）5 分钟内直接命中，省 DeepSeek 调用与耗时
answer_cache = RedisCache(settings.redis_url, ttl_seconds=300)


def cache_key(kb_id: int | None, question: str) -> str:
    raw = f"{kb_id}:{question.strip()}"
    return "rag:answer:" + hashlib.md5(raw.encode("utf-8")).hexdigest()
