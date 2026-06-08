"""
缓存模块抽象接口定义

遵循接口隔离原则，为缓存层提供清晰的契约。
所有缓存实现必须遵循此接口，确保可替换性。
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict, Callable


class CacheBackend(ABC):
    """缓存后端抽象接口

    所有缓存实现必须遵循此接口，确保可替换性。
    支持内存缓存、Redis缓存等多种后端。

    Usage:
        cache = RedisCache()  # 或 MemoryCache()
        cache.set("key", {"data": "value"}, ttl=300)
        value = cache.get("key")
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键，建议使用规范化的命名策略

        Returns:
            缓存值，如果不存在返回 None

        Raises:
            CacheException: 缓存服务异常时抛出
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值（必须可JSON序列化）
            ttl: 过期时间（秒），None表示永不过期

        Returns:
            设置是否成功
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            删除是否成功（键不存在也返回True）
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 缓存键

        Returns:
            键是否存在
        """
        pass

    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典，只返回存在的键
        """
        pass

    @abstractmethod
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批量设置缓存

        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒）

        Returns:
            设置是否成功
        """
        pass

    @abstractmethod
    def delete_many(self, keys: List[str]) -> bool:
        """批量删除缓存

        Args:
            keys: 缓存键列表

        Returns:
            删除是否成功
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空所有缓存

        Returns:
            清空是否成功

        Warning:
            生产环境慎用！此操作会删除所有缓存数据。
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查

        Returns:
            缓存服务是否健康
        """
        pass


class CacheManagerInterface(ABC):
    """缓存管理器接口

    提供高级缓存功能，包括自动加载、缓存失效策略等。
    """

    @abstractmethod
    def get(self, key: str, loader: Optional[Callable[[], Any]] = None,
            ttl: Optional[int] = None) -> Optional[Any]:
        """获取缓存，支持自动加载

        Args:
            key: 缓存键
            loader: 数据加载函数，缓存未命中时调用
            ttl: 过期时间（秒）

        Returns:
            缓存值，不存在且无法加载时返回None
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）

        Returns:
            设置是否成功
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            删除是否成功
        """
        pass

    @abstractmethod
    def invalidate_tenant(self, tenant_id: str) -> None:
        """失效租户相关缓存

        Args:
            tenant_id: 租户ID
        """
        pass

    @abstractmethod
    def invalidate_service(self, service_type: Optional[str] = None,
                           instance_id: Optional[str] = None) -> None:
        """失效服务相关缓存

        Args:
            service_type: 服务类型
            instance_id: 实例ID
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典，包含hits、misses、hit_rate等
        """
        pass
