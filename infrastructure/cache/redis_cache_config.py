"""
Redis缓存配置
Agent永续自进化系统 - 缓存层
"""
from typing import Optional, Any
import json
from datetime import timedelta

import redis.asyncio as redis

from infrastructure.logging.logging_system import get_logger


class RedisCacheConfig:
    """Redis缓存配置"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        decode_responses: bool = True,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5
    ):
        self.logger = get_logger("RedisCacheConfig")
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        
        self._redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """连接Redis"""
        try:
            self._redis_client = redis.Redis(
                from_url=self.redis_url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout
            )
            
            await self._redis_client.ping()
            self.logger.info("Connected to Redis successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            self._redis_client = None
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._redis_client:
            await self._redis_client.close()
            self.logger.info("Disconnected from Redis")
    
    def get_client(self) -> Optional[redis.Redis]:
        """获取Redis客户端"""
        return self._redis_client
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        expire_timedelta: Optional[timedelta] = None
    ) -> bool:
        """设置缓存"""
        if not self._redis_client:
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire_timedelta:
                await self._redis_client.setex(key, expire_timedelta, value)
            elif expire:
                await self._redis_client.setex(key, expire, value)
            else:
                await self._redis_client.set(key, value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set cache: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._redis_client:
            return None
        
        try:
            value = await self._redis_client.get(key)
            
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            self.logger.error(f"Failed to get cache: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._redis_client:
            return False
        
        try:
            result = await self._redis_client.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Failed to delete cache: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._redis_client:
            return False
        
        try:
            return await self._redis_client.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Failed to check existence: {str(e)}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._redis_client:
            return False
        
        try:
            return await self._redis_client.expire(key, seconds)
        except Exception as e:
            self.logger.error(f"Failed to set expire: {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取剩余生存时间"""
        if not self._redis_client:
            return -1
        
        try:
            return await self._redis_client.ttl(key)
        except Exception as e:
            self.logger.error(f"Failed to get TTL: {str(e)}")
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增"""
        if not self._redis_client:
            return None
        
        try:
            return await self._redis_client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Failed to increment: {str(e)}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """递减"""
        if not self._redis_client:
            return None
        
        try:
            return await self._redis_client.decrby(key, amount)
        except Exception as e:
            self.logger.error(f"Failed to decrement: {str(e)}")
            return None
    
    async def keys(self, pattern: str) -> list:
        """获取匹配的键"""
        if not self._redis_client:
            return []
        
        try:
            return await self._redis_client.keys(pattern)
        except Exception as e:
            self.logger.error(f"Failed to get keys: {str(e)}")
            return []
    
    async def flush_db(self) -> bool:
        """清空当前数据库"""
        if not self._redis_client:
            return False
        
        try:
            await self._redis_client.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Failed to flush DB: {str(e)}")
            return False


_cache_config: Optional[RedisCacheConfig] = None


def get_cache_config() -> RedisCacheConfig:
    """获取缓存配置单例"""
    global _cache_config
    if _cache_config is None:
        _cache_config = RedisCacheConfig()
    return _cache_config


async def get_cache() -> RedisCacheConfig:
    """获取缓存配置"""
    config = get_cache_config()
    if not config.get_client():
        await config.connect()
    return config
