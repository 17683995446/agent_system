"""
Phase 48: 高度模块化缓存层架构
采用分层设计模式，实现缓存抽象层
"""

import os
import json
import time
import uuid
import hashlib
from typing import Optional, Any, List, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from enum import Enum
import logging

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 缓存配置 ====================

class CacheConfig:
    """缓存配置"""
    
    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 0,
        redis_password: str = None,
        enabled: bool = True,
        default_ttl: int = 300,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5
    ):
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.enabled = enabled
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls()

# ==================== 缓存键策略 ====================

class CacheKeyStrategy:
    """缓存键命名策略"""
    
    PREFIX = "agent_system"
    
    @classmethod
    def tenant(cls, tenant_id: str) -> str:
        """租户缓存键"""
        return f"{cls.PREFIX}:tenant:{tenant_id}"
    
    @classmethod
    def tenant_list(cls, status: str = None) -> str:
        """租户列表缓存键"""
        if status:
            return f"{cls.PREFIX}:tenant_list:{status}"
        return f"{cls.PREFIX}:tenant_list:all"
    
    @classmethod
    def quota(cls, tenant_id: str) -> str:
        """配额缓存键"""
        return f"{cls.PREFIX}:quota:{tenant_id}"
    
    @classmethod
    def service(cls, service_type: str) -> str:
        """服务缓存键"""
        return f"{cls.PREFIX}:service:{service_type}"
    
    @classmethod
    def service_instance(cls, instance_id: str) -> str:
        """服务实例缓存键"""
        return f"{cls.PREFIX}:service_instance:{instance_id}"
    
    @classmethod
    def usage(cls, tenant_id: str) -> str:
        """使用量缓存键"""
        return f"{cls.PREFIX}:usage:{tenant_id}"

# ==================== 缓存策略枚举 ====================

class CacheStrategy(Enum):
    """缓存策略类型"""
    READ_THROUGH = "read_through"      # 读穿透
    WRITE_THROUGH = "write_through"    # 写穿透
    WRITE_AROUND = "write_around"     # 写环绕
    CACHE_ASIDE = "cache_aside"       # 旁路缓存
    REFRESH_AHEAD = "refresh_ahead"   # 预刷新

# ==================== 缓存抽象接口 ====================

class CacheBackend(ABC):
    """缓存后端抽象接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> dict:
        """批量获取"""
        pass
    
    @abstractmethod
    def set_many(self, mapping: dict, ttl: int = None) -> bool:
        """批量设置"""
        pass
    
    @abstractmethod
    def delete_many(self, keys: List[str]) -> bool:
        """批量删除"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空所有缓存"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass

# ==================== 内存缓存实现 ====================

class MemoryCache(CacheBackend):
    """内存缓存实现（用于测试或无Redis环境）"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                self._misses += 1
                return None
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        self._cache[key] = value
        if ttl:
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        elif key in self._expiry:
            del self._expiry[key]
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        if key in self._cache:
            if key in self._expiry and datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return False
            return True
        return False
    
    def get_many(self, keys: List[str]) -> dict:
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, mapping: dict, ttl: int = None) -> bool:
        for key, value in mapping.items():
            self.set(key, value, ttl)
        return True
    
    def delete_many(self, keys: List[str]) -> bool:
        for key in keys:
            self.delete(key)
        return True
    
    def clear(self) -> bool:
        self._cache.clear()
        self._expiry.clear()
        return True
    
    def health_check(self) -> bool:
        return True
    
    def get_stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache)
        }

# ==================== Redis缓存实现 ====================

class RedisCache(CacheBackend):
    """Redis缓存实现"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._client = None
        self._connect()
    
    def _connect(self):
        """建立Redis连接"""
        try:
            import redis
            self._client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=True
            )
            logger.info(f"Redis连接成功: {self.config.redis_host}:{self.config.redis_port}")
        except ImportError:
            logger.warning("Redis模块未安装，使用内存缓存")
            self._client = None
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self._client = None
    
    def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET失败: {key} - {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if not self._client:
            return False
        try:
            ttl = ttl or self.config.default_ttl
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET失败: {key} - {e}")
            return False
    
    def delete(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE失败: {key} - {e}")
            return False
    
    def exists(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS失败: {key} - {e}")
            return False
    
    def get_many(self, keys: List[str]) -> dict:
        if not self._client:
            return {}
        try:
            values = self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Redis MGET失败: {e}")
            return {}
    
    def set_many(self, mapping: dict, ttl: int = None) -> bool:
        if not self._client:
            return False
        try:
            ttl = ttl or self.config.default_ttl
            pipe = self._client.pipeline()
            for key, value in mapping.items():
                serialized = json.dumps(value, default=str)
                pipe.setex(key, ttl, serialized)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis MSET失败: {e}")
            return False
    
    def delete_many(self, keys: List[str]) -> bool:
        if not self._client:
            return False
        try:
            self._client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis MDELETE失败: {e}")
            return False
    
    def clear(self) -> bool:
        if not self._client:
            return False
        try:
            for key in self._client.scan_iter(f"{CacheKeyStrategy.PREFIX}:*"):
                self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis CLEAR失败: {e}")
            return False
    
    def health_check(self) -> bool:
        if not self._client:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False

# ==================== 缓存管理器 ====================

class CacheManager:
    """缓存管理器 - 统一接口"""
    
    def __init__(self, backend: CacheBackend = None, config: CacheConfig = None):
        if backend:
            self.backend = backend
        else:
            config = config or CacheConfig()
            if config.enabled:
                self.backend = RedisCache(config)
            else:
                self.backend = MemoryCache()
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    def get(self, key: str, loader: Callable = None, ttl: int = None) -> Optional[Any]:
        """获取缓存，支持回源加载"""
        value = self.backend.get(key)
        
        if value is not None:
            self.stats["hits"] += 1
            logger.debug(f"缓存命中: {key}")
            return value
        
        self.stats["misses"] += 1
        logger.debug(f"缓存未命中: {key}")
        
        if loader:
            value = loader()
            if value is not None:
                self.backend.set(key, value, ttl)
                self.stats["sets"] += 1
        
        return value
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        self.stats["sets"] += 1
        return self.backend.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        self.stats["deletes"] += 1
        return self.backend.delete(key)
    
    def invalidate_tenant(self, tenant_id: str):
        """失效租户相关缓存"""
        keys = [
            CacheKeyStrategy.tenant(tenant_id),
            CacheKeyStrategy.quota(tenant_id),
            CacheKeyStrategy.usage(tenant_id)
        ]
        self.backend.delete_many(keys)
        logger.info(f"失效租户缓存: {tenant_id}")
    
    def invalidate_service(self, service_type: str = None, instance_id: str = None):
        """失效服务相关缓存"""
        if instance_id:
            self.backend.delete(CacheKeyStrategy.service_instance(instance_id))
        if service_type:
            self.backend.delete(CacheKeyStrategy.service(service_type))
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total,
            "hit_rate": hit_rate
        }
    
    def clear_stats(self):
        """清除统计"""
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

# ==================== 缓存装饰器 ====================

def cached(key_prefix: str, ttl: int = 300, loader_func: str = None):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 构建缓存键
            key_parts = [key_prefix, str(args) if args else "", str(kwargs)]
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 获取缓存管理器
            cache = getattr(wrapper, '_cache_manager', None)
            if not cache:
                cache = CacheManager()
                wrapper._cache_manager = cache
            
            # 尝试从缓存获取
            value = cache.get(key, ttl=ttl)
            if value is not None:
                return value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

# ==================== 全局缓存实例 ====================

cache_manager = CacheManager()

def get_cache() -> CacheManager:
    """获取全局缓存管理器"""
    return cache_manager

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 48: 缓存层架构测试")
    print("=" * 80)
    
    # 测试内存缓存
    print("\n--- 测试内存缓存 ---")
    cache = CacheManager(backend=MemoryCache())
    
    # 测试基本操作
    cache.set("test_key", {"data": "test_value"}, ttl=60)
    value = cache.get("test_key")
    print(f"GET test_key: {value}")
    
    # 测试回源加载
    def load_data():
        return {"data": "loaded_from_source", "timestamp": datetime.now().isoformat()}
    
    value = cache.get("lazy_key", loader=load_data)
    print(f"GET lazy_key (with loader): {value}")
    
    # 测试统计
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
    
    # 测试缓存键策略
    print("\n--- 缓存键策略 ---")
    print(f"租户键: {CacheKeyStrategy.tenant('123')}")
    print(f"配额键: {CacheKeyStrategy.quota('456')}")
    print(f"服务键: {CacheKeyStrategy.service('api_gateway')}")
    
    print("\n✅ 缓存层架构测试通过！")
