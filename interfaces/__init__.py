"""
核心接口定义包

遵循接口隔离原则，为系统各模块提供清晰的抽象接口。
所有实现类必须遵循这些接口定义。
"""

from .cache import CacheBackend, CacheManagerInterface
from .repository import Repository, TenantRepositoryInterface, ServiceRepositoryInterface
from .security import TokenManagerInterface, PermissionCheckerInterface, APIKeyManagerInterface, RateLimiterInterface
from .monitoring import MetricsCollectorInterface, AlertManagerInterface, HealthCheckerInterface
from .config import ConfigManagerInterface, Environment

__all__ = [
    # 缓存接口
    'CacheBackend',
    'CacheManagerInterface',
    # 仓储接口
    'Repository',
    'TenantRepositoryInterface',
    'ServiceRepositoryInterface',
    # 安全接口
    'TokenManagerInterface',
    'PermissionCheckerInterface',
    'APIKeyManagerInterface',
    'RateLimiterInterface',
    # 监控接口
    'MetricsCollectorInterface',
    'AlertManagerInterface',
    'HealthCheckerInterface',
    # 配置接口
    'ConfigManagerInterface',
    'Environment',
]
