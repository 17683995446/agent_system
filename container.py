"""
依赖注入容器

实现控制反转(IoC)模式，统一管理系统中所有组件的创建和依赖关系。
遵循依赖倒置原则，所有服务通过接口注入，不依赖具体实现。
"""

import logging
from typing import Dict, Any, Optional, Type, Callable
from functools import lru_cache

from interfaces import (
    CacheBackend,
    CacheManagerInterface,
    TenantRepositoryInterface,
    ServiceRepositoryInterface,
    TokenManagerInterface,
    APIKeyManagerInterface,
    PermissionCheckerInterface,
    RateLimiterInterface,
    MetricsCollectorInterface,
    AlertManagerInterface,
    HealthCheckerInterface,
    ConfigManagerInterface,
    Environment
)

from services.tenant_service import TenantService
from services.auth_service import AuthService
from services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)


class Container:
    """依赖注入容器

    管理所有组件的生命周期和依赖关系。
    支持单例模式和工厂模式。

    Attributes:
        _registry: 组件注册表
        _singletons: 单例实例缓存
        _factories: 工厂函数注册表
    """

    def __init__(self):
        self._registry: Dict[str, Type] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._initialized = False

    def register(self, name: str, cls: Type, singleton: bool = True) -> None:
        """注册组件类型

        Args:
            name: 组件名称
            cls: 组件类
            singleton: 是否单例
        """
        self._registry[name] = cls
        if singleton:
            self._singletons[name] = None
        logger.debug(f"[Container] 注册组件: {name} -> {cls.__name__}")

    def register_factory(self, name: str, factory: Callable, singleton: bool = True) -> None:
        """注册工厂函数

        Args:
            name: 组件名称
            factory: 工厂函数
            singleton: 是否单例
        """
        self._factories[name] = factory
        if singleton:
            self._singletons[name] = None
        logger.debug(f"[Container] 注册工厂: {name}")

    def resolve(self, name: str) -> Any:
        """解析组件实例

        Args:
            name: 组件名称

        Returns:
            组件实例

        Raises:
            KeyError: 组件未注册
        """
        # 检查单例缓存
        if name in self._singletons and self._singletons[name] is not None:
            return self._singletons[name]

        # 通过工厂创建
        if name in self._factories:
            instance = self._factories[name](self)
            if name in self._singletons:
                self._singletons[name] = instance
            return instance

        # 通过类型创建
        if name in self._registry:
            cls = self._registry[name]
            instance = cls()
            if name in self._singletons:
                self._singletons[name] = instance
            return instance

        raise KeyError(f"Component '{name}' not registered in container")

    def has(self, name: str) -> bool:
        """检查组件是否已注册

        Args:
            name: 组件名称

        Returns:
            是否已注册
        """
        return name in self._registry or name in self._factories

    def reset(self) -> None:
        """重置容器，清除所有单例实例"""
        for name in self._singletons:
            self._singletons[name] = None
        logger.info("[Container] 容器已重置")


# ==================== 默认工厂函数 ====================

def _create_memory_cache_backend(container: Container) -> CacheBackend:
    """创建内存缓存后端"""
    from phase48_cache import MemoryCache
    return MemoryCache()


def _create_cache_manager(container: Container) -> CacheManagerInterface:
    """创建缓存管理器"""
    from phase48_cache import CacheManager
    backend = container.resolve("cache_backend")
    return CacheManager(backend=backend)


def _create_tenant_repository(container: Container) -> TenantRepositoryInterface:
    """创建租户仓储"""
    from phase47_repository import TenantRepository
    from phase47_database import SessionLocal
    db = SessionLocal()
    return TenantRepository(db)


def _create_token_manager(container: Container) -> TokenManagerInterface:
    """创建Token管理器"""
    from phase49_security import TokenManager
    return TokenManager()


def _create_api_key_manager(container: Container) -> APIKeyManagerInterface:
    """创建API Key管理器"""
    from phase49_security import APIKeyManager
    return APIKeyManager()


def _create_permission_checker(container: Container) -> PermissionCheckerInterface:
    """创建权限检查器"""
    from phase49_security import PermissionManager
    return PermissionManager()


def _create_rate_limiter(container: Container) -> RateLimiterInterface:
    """创建速率限制器"""
    from phase49_security import RateLimiter
    return RateLimiter()


def _create_metrics_collector(container: Container) -> MetricsCollectorInterface:
    """创建指标收集器"""
    from phase50_monitoring import PrometheusMetrics
    return PrometheusMetrics()


def _create_alert_manager(container: Container) -> AlertManagerInterface:
    """创建告警管理器"""
    from phase50_monitoring import AlertManager
    metrics = container.resolve("metrics")
    return AlertManager(metrics)


def _create_health_checker(container: Container) -> HealthCheckerInterface:
    """创建健康检查器"""
    from phase51_ha_base import get_health_checker
    return get_health_checker()


def _create_tenant_service(container: Container) -> TenantService:
    """创建租户服务"""
    tenant_repo = container.resolve("tenant_repository")
    cache_manager = container.resolve("cache_manager")
    return TenantService(tenant_repo=tenant_repo, cache_manager=cache_manager)


def _create_auth_service(container: Container) -> AuthService:
    """创建认证服务"""
    token_manager = container.resolve("token_manager")
    api_key_manager = container.resolve("api_key_manager")
    permission_checker = container.resolve("permission_checker")
    rate_limiter = container.resolve("rate_limiter")
    return AuthService(
        token_manager=token_manager,
        api_key_manager=api_key_manager,
        permission_checker=permission_checker,
        rate_limiter=rate_limiter
    )


def _create_monitoring_service(container: Container) -> MonitoringService:
    """创建监控服务"""
    metrics = container.resolve("metrics")
    alert_manager = container.resolve("alert_manager")
    health_checker = container.resolve("health_checker")
    return MonitoringService(
        metrics=metrics,
        alert_manager=alert_manager,
        health_checker=health_checker
    )


# ==================== 全局容器实例 ====================

_default_container: Optional[Container] = None


def get_container() -> Container:
    """获取全局容器实例（懒加载）"""
    global _default_container
    if _default_container is None:
        _default_container = create_default_container()
    return _default_container


def create_default_container() -> Container:
    """创建默认配置的容器

    注册所有系统组件的工厂函数。
    """
    container = Container()

    # 基础设施层
    container.register_factory("cache_backend", _create_memory_cache_backend, singleton=True)
    container.register_factory("cache_manager", _create_cache_manager, singleton=True)

    # 数据访问层
    container.register_factory("tenant_repository", _create_tenant_repository, singleton=False)

    # 安全层
    container.register_factory("token_manager", _create_token_manager, singleton=True)
    container.register_factory("api_key_manager", _create_api_key_manager, singleton=True)
    container.register_factory("permission_checker", _create_permission_checker, singleton=True)
    container.register_factory("rate_limiter", _create_rate_limiter, singleton=True)

    # 监控层
    container.register_factory("metrics", _create_metrics_collector, singleton=True)
    container.register_factory("alert_manager", _create_alert_manager, singleton=True)
    container.register_factory("health_checker", _create_health_checker, singleton=True)

    # 应用服务层
    container.register_factory("tenant_service", _create_tenant_service, singleton=True)
    container.register_factory("auth_service", _create_auth_service, singleton=True)
    container.register_factory("monitoring_service", _create_monitoring_service, singleton=True)

    logger.info("[Container] 默认容器初始化完成")
    return container


def reset_container() -> None:
    """重置全局容器"""
    global _default_container
    if _default_container:
        _default_container.reset()
    _default_container = None
    logger.info("[Container] 全局容器已重置")


# ==================== 便捷函数 ====================

def get_tenant_service() -> TenantService:
    """获取租户服务"""
    return get_container().resolve("tenant_service")


def get_auth_service() -> AuthService:
    """获取认证服务"""
    return get_container().resolve("auth_service")


def get_monitoring_service() -> MonitoringService:
    """获取监控服务"""
    return get_container().resolve("monitoring_service")


def get_cache_manager() -> CacheManagerInterface:
    """获取缓存管理器"""
    return get_container().resolve("cache_manager")


if __name__ == "__main__":
    print("=" * 80)
    print("依赖注入容器测试")
    print("=" * 80)

    # 创建容器
    container = create_default_container()

    # 测试解析各组件
    print("\n--- 测试组件解析 ---")

    cache = container.resolve("cache_manager")
    print(f"缓存管理器: {type(cache).__name__}")

    tenant_repo = container.resolve("tenant_repository")
    print(f"租户仓储: {type(tenant_repo).__name__}")

    token_mgr = container.resolve("token_manager")
    print(f"Token管理器: {type(token_mgr).__name__}")

    auth_service = container.resolve("auth_service")
    print(f"认证服务: {type(auth_service).__name__}")

    monitoring_service = container.resolve("monitoring_service")
    print(f"监控服务: {type(monitoring_service).__name__}")

    # 测试单例
    print("\n--- 测试单例模式 ---")
    cache2 = container.resolve("cache_manager")
    print(f"缓存管理器单例: {cache is cache2}")

    auth2 = container.resolve("auth_service")
    print(f"认证服务单例: {auth_service is auth2}")

    # 测试便捷函数
    print("\n--- 测试便捷函数 ---")
    ts = get_tenant_service()
    print(f"通过便捷函数获取租户服务: {type(ts).__name__}")

    print("\n" + "=" * 80)
    print("依赖注入容器测试通过！")
    print("=" * 80)
