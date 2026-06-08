"""
单元测试 - 缓存系统
"""
import pytest
import time

from infrastructure.cache.cache_manager import (
    CacheManager,
    cached,
    generate_cache_key,
    default_cache,
    task_cache
)


class TestCacheManager:
    """测试缓存管理器"""
    
    def test_cache_creation_lru(self):
        """测试LRU缓存创建"""
        cache = CacheManager(cache_type="lru", maxsize=100)
        assert cache is not None
        assert cache.cache_type == "lru"
    
    def test_cache_creation_ttl(self):
        """测试TTL缓存创建"""
        cache = CacheManager(cache_type="ttl", maxsize=100, ttl=60)
        assert cache is not None
        assert cache.cache_type == "ttl"
    
    def test_cache_creation_lfu(self):
        """测试LFU缓存创建"""
        cache = CacheManager(cache_type="lfu", maxsize=100)
        assert cache is not None
        assert cache.cache_type == "lfu"
    
    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = CacheManager(maxsize=10)
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_cache_get_default(self):
        """测试缓存默认值"""
        cache = CacheManager(maxsize=10)
        assert cache.get("nonexistent", "default") == "default"
    
    def test_cache_delete(self):
        """测试缓存删除"""
        cache = CacheManager(maxsize=10)
        cache.set("key1", "value1")
        
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
    
    def test_cache_delete_nonexistent(self):
        """测试删除不存在的键"""
        cache = CacheManager(maxsize=10)
        assert cache.delete("nonexistent") is False
    
    def test_cache_clear(self):
        """测试缓存清空"""
        cache = CacheManager(maxsize=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        # 先检查缓存清空
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
        
        # 现在检查获取不存在的键（这会增加miss计数，但这是预期行为）
        result = cache.get("key1")
        assert result is None
        assert cache.misses == 1
    
    def test_cache_stats(self):
        """测试缓存统计"""
        cache = CacheManager(maxsize=10)
        cache.set("key1", "value1")
        
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats
    
    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        cache = CacheManager(maxsize=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # hit
        cache.get("nonexistent")  # miss
        
        stats = cache.get_stats()
        assert stats["total"] == 4
        assert stats["hits"] == 3
        assert stats["misses"] == 1
    
    def test_cache_singleton(self):
        """测试缓存单例模式"""
        cache1 = CacheManager.get_instance("test_singleton")
        cache2 = CacheManager.get_instance("test_singleton")
        assert cache1 is cache2


class TestCacheHelperFunctions:
    """测试缓存辅助函数"""
    
    def test_generate_cache_key(self):
        """测试缓存键生成"""
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key3 = generate_cache_key("arg1", "arg3", kwarg1="value1")
        
        assert key1 == key2
        assert key1 != key3
    
    def test_cache_decorator(self):
        """测试缓存装饰器"""
        cache = CacheManager(maxsize=100)
        call_count = 0
        
        @cached(cache)
        def test_func(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        result1 = test_func(1, 2)
        result2 = test_func(1, 2)
        result3 = test_func(3, 4)
        
        assert result1 == 3
        assert result2 == 3
        assert result3 == 7
        assert call_count == 2


class TestDefaultCaches:
    """测试默认缓存"""
    
    def test_default_cache_exists(self):
        """测试默认缓存存在"""
        assert default_cache is not None
        assert default_cache.cache_type == "ttl"
    
    def test_task_cache_exists(self):
        """测试任务缓存存在"""
        assert task_cache is not None
        assert task_cache.cache_type == "lru"
