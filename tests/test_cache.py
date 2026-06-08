"""
缓存模块单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase48_cache import MemoryCache, CacheManager, CacheKeyStrategy


def test_memory_cache_basic():
    """测试内存缓存基本操作"""
    cache = MemoryCache()

    # set and get
    assert cache.set("key1", "value1") is True
    assert cache.get("key1") == "value1"

    # non-existent key
    assert cache.get("nonexistent") is None
    print("test_memory_cache_basic PASSED")


def test_memory_cache_ttl():
    """测试缓存过期"""
    cache = MemoryCache()

    # 设置1秒过期
    cache.set("key1", "value1", ttl=1)
    assert cache.get("key1") == "value1"

    # 等待过期
    import time
    time.sleep(1.5)
    assert cache.get("key1") is None
    print("test_memory_cache_ttl PASSED")


def test_memory_cache_delete():
    """测试删除"""
    cache = MemoryCache()
    cache.set("key1", "value1")
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert cache.delete("nonexistent") is False
    print("test_memory_cache_delete PASSED")


def test_memory_cache_exists():
    """测试存在检查"""
    cache = MemoryCache()
    cache.set("key1", "value1")
    assert cache.exists("key1") is True
    assert cache.exists("nonexistent") is False
    print("test_memory_cache_exists PASSED")


def test_memory_cache_batch():
    """测试批量操作"""
    cache = MemoryCache()

    # set_many
    cache.set_many({"a": 1, "b": 2, "c": 3})

    # get_many
    result = cache.get_many(["a", "b", "nonexistent"])
    assert result["a"] == 1
    assert result["b"] == 2
    assert "nonexistent" not in result

    # delete_many
    cache.delete_many(["a", "b"])
    assert cache.get("a") is None
    assert cache.get("b") is None
    assert cache.get("c") == 3
    print("test_memory_cache_batch PASSED")


def test_cache_manager():
    """测试缓存管理器"""
    backend = MemoryCache()
    manager = CacheManager(backend=backend)

    # basic
    manager.set("key1", "value1")
    assert manager.get("key1") == "value1"

    # loader
    def load_data():
        return "loaded"

    value = manager.get("lazy_key", loader=load_data)
    assert value == "loaded"

    # stats
    stats = manager.get_stats()
    assert "hits" in stats
    assert "misses" in stats
    print("test_cache_manager PASSED")


def test_cache_key_strategy():
    """测试缓存键策略"""
    assert CacheKeyStrategy.tenant("123") == "agent_system:tenant:123"
    assert CacheKeyStrategy.quota("456") == "agent_system:quota:456"
    assert CacheKeyStrategy.service("api_gateway") == "agent_system:service:api_gateway"
    print("test_cache_key_strategy PASSED")


if __name__ == "__main__":
    print("=" * 80)
    print("缓存模块单元测试")
    print("=" * 80)

    test_memory_cache_basic()
    test_memory_cache_ttl()
    test_memory_cache_delete()
    test_memory_cache_exists()
    test_memory_cache_batch()
    test_cache_manager()
    test_cache_key_strategy()

    print("\n" + "=" * 80)
    print("所有缓存模块测试通过！")
    print("=" * 80)
