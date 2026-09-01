import time

from app.services.cache import RedisCache, _MemoryCache, cache_key


def test_memory_cache_get_set():
    c = _MemoryCache(ttl_seconds=10)
    c.set("k", "v")
    assert c.get("k") == "v"


def test_memory_cache_miss():
    c = _MemoryCache(ttl_seconds=10)
    assert c.get("missing") is None


def test_memory_cache_expires():
    c = _MemoryCache(ttl_seconds=1)
    c.set("k", "v")
    time.sleep(1.1)
    assert c.get("k") is None


def test_cache_key_deterministic():
    assert cache_key(1, "小米15") == cache_key(1, "小米15")


def test_cache_key_differs_by_question():
    assert cache_key(1, "a") != cache_key(1, "b")


def test_cache_key_differs_by_kb():
    assert cache_key(1, "a") != cache_key(2, "a")


def test_redis_fallback_to_memory_when_unreachable():
    # 用必然连不上的端口，强制降级为内存缓存，验证应用不中断
    c = RedisCache("redis://127.0.0.1:1/0", ttl_seconds=10)
    c.set("k", {"answer": "hi"})
    assert c.get("k") == {"answer": "hi"}
