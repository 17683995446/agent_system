"""
基础设施 - 缓存系统（增强版）
基于cachetools的内存缓存，支持多种策略
"""
import time
import hashlib
import pickle
from typing import Any, Callable, Dict, Optional, Union
from functools import wraps
from cachetools import LRUCache, TTLCache, LFUCache
from cachetools.keys import hashkey
from datetime import datetime, timezone
import json


class CacheEntry:
    """缓存条目"""
    def __init__(self, value: Any, expire_time: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.expire_time = expire_time
        self.hits = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_time is None:
            return False
        return time.time() > self.expire_time
    
    def increment_hits(self):
        """增加命中次数"""
        self.hits += 1


class CacheManager:
    """缓存管理器"""
    
    _instances: Dict[str, "CacheManager"] = {}
    
    def __init__(self, cache_type: str = "lru", maxsize: int = 1000, ttl: int = 3600):
        """初始化缓存管理器"""
        if cache_type == "lru":
            self.cache = LRUCache(maxsize=maxsize)
        elif cache_type == "ttl":
            self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        elif cache_type == "lfu":
            self.cache = LFUCache(maxsize=maxsize)
        else:
            self.cache = LRUCache(maxsize=maxsize)
        
        self.cache_type = cache_type
        self.hits = 0
        self.misses = 0
        self.default_ttl = ttl
        self.evictions = 0
        self.sets = 0
        self.deletes = 0
    
    @classmethod
    def get_instance(cls, name: str = "default", **kwargs) -> "CacheManager":
        """获取缓存管理器单例"""
        if name not in cls._instances:
            cls._instances[name] = cls(**kwargs)
        return cls._instances[name]
    
    def get(self, key: Any, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            value = self.cache[key]
            self.hits += 1
            return value
        except KeyError:
            self.misses += 1
            return default
    
    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        # 检查是否会导致淘汰
        if hasattr(self.cache, 'maxsize') and len(self.cache) >= self.cache.maxsize:
            self.evictions += 1
        
        self.cache[key] = value
        self.sets += 1
    
    def delete(self, key: Any) -> bool:
        """删除缓存"""
        try:
            del self.cache[key]
            self.deletes += 1
            return True
        except KeyError:
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.sets = 0
        self.deletes = 0
    
    def get_many(self, keys: list, default: Any = None) -> Dict[Any, Any]:
        """批量获取缓存"""
        result = {}
        for key in keys:
            result[key] = self.get(key, default)
        return result
    
    def set_many(self, items: Dict[Any, Any], ttl: Optional[int] = None) -> None:
        """批量设置缓存"""
        for key, value in items.items():
            self.set(key, value, ttl)
    
    def delete_many(self, keys: list) -> int:
        """批量删除缓存"""
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count
    
    def exists(self, key: Any) -> bool:
        """检查键是否存在"""
        return key in self.cache
    
    def get_all_keys(self) -> list:
        """获取所有键"""
        return list(self.cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        miss_rate = self.misses / total if total > 0 else 0.0
        
        return {
            "type": self.cache_type,
            "current_size": len(self.cache),
            "max_size": self.cache.maxsize if hasattr(self.cache, "maxsize") else "unlimited",
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "miss_rate": miss_rate,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "default_ttl": self.default_ttl,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def warm_up(self, warmup_data: Dict[Any, Any]) -> None:
        """预热缓存"""
        self.set_many(warmup_data)


def cached(cache: CacheManager, key_func: Callable = hashkey, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            key = key_func(*args, **kwargs)
            value = cache.get(key)
            if value is not None:
                return value
            
            value = await func(*args, **kwargs)
            cache.set(key, value, ttl)
            return value
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            key = key_func(*args, **kwargs)
            value = cache.get(key)
            if value is not None:
                return value
            
            value = func(*args, **kwargs)
            cache.set(key, value, ttl)
            return value
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = []
    for arg in args:
        key_parts.append(str(arg))
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")
    key_string = "_".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def serialize(obj: Any) -> str:
    """序列化对象"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return pickle.dumps(obj).hex()


def deserialize(data: str) -> Any:
    """反序列化对象"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        try:
            return pickle.loads(bytes.fromhex(data))
        except Exception:
            return data


default_cache = CacheManager.get_instance("default", cache_type="ttl", maxsize=1000, ttl=300)
task_cache = CacheManager.get_instance("tasks", cache_type="lru", maxsize=500)
memory_cache = CacheManager.get_instance("memory", cache_type="ttl", maxsize=200, ttl=1800)
api_response_cache = CacheManager.get_instance("api_responses", cache_type="ttl", maxsize=2000, ttl=60)
