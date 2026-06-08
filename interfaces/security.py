"""
安全模块抽象接口定义

提供身份认证、权限控制和API密钥管理的标准接口。
所有安全相关实现必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class TokenManagerInterface(ABC):
    """Token管理接口

    提供JWT Token的生成、验证和撤销功能。
    支持访问令牌和刷新令牌。
    """

    @abstractmethod
    def generate_access_token(
        self,
        user_id: str,
        tenant_id: str,
        permissions: List[str],
        expires_in: int = 1800
    ) -> str:
        """生成访问令牌

        Args:
            user_id: 用户唯一标识
            tenant_id: 租户ID
            permissions: 权限列表
            expires_in: 过期时间（秒，默认30分钟）

        Returns:
            JWT Token字符串
        """
        pass

    @abstractmethod
    def generate_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        expires_in: int = 604800
    ) -> str:
        """生成刷新令牌

        Args:
            user_id: 用户唯一标识
            tenant_id: 租户ID
            expires_in: 过期时间（秒，默认7天）

        Returns:
            JWT Refresh Token字符串
        """
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证Token

        Args:
            token: JWT Token

        Returns:
            Token payload字典，无效返回None
        """
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """撤销Token

        Args:
            token: 要撤销的Token

        Returns:
            撤销是否成功
        """
        pass

    @abstractmethod
    def is_token_revoked(self, token_id: str) -> bool:
        """检查Token是否已撤销

        Args:
            token_id: Token唯一标识（jti）

        Returns:
            是否已撤销
        """
        pass


class APIKeyManagerInterface(ABC):
    """API Key管理接口

    提供API Key的生成、验证和管理功能。
    """

    @abstractmethod
    def generate_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """生成API Key

        Args:
            tenant_id: 租户ID
            name: Key名称
            permissions: 权限列表
            expires_in_days: 过期天数，None表示永不过期

        Returns:
            API Key信息字典，包含key_id和full_key
        """
        pass

    @abstractmethod
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API Key

        Args:
            api_key: 完整的API Key

        Returns:
            API Key信息，无效返回None
        """
        pass

    @abstractmethod
    def revoke_api_key(self, key_id: str) -> bool:
        """撤销API Key

        Args:
            key_id: Key ID

        Returns:
            撤销是否成功
        """
        pass

    @abstractmethod
    def list_keys(self, tenant_id: str) -> List[Dict[str, Any]]:
        """列出租户的所有API Keys

        Args:
            tenant_id: 租户ID

        Returns:
            API Key列表
        """
        pass


class PermissionCheckerInterface(ABC):
    """权限检查接口

    提供基于角色的权限检查功能。
    """

    @abstractmethod
    def has_permission(
        self,
        user_permissions: List[str],
        required: str
    ) -> bool:
        """检查权限

        Args:
            user_permissions: 用户拥有的权限列表
            required: 需要的权限

        Returns:
            是否有权限
        """
        pass

    @abstractmethod
    def has_any_permission(
        self,
        user_permissions: List[str],
        required_list: List[str]
    ) -> bool:
        """检查是否有任意一个权限

        Args:
            user_permissions: 用户拥有的权限列表
            required_list: 需要的权限列表

        Returns:
            是否有任意一个权限
        """
        pass

    @abstractmethod
    def has_all_permissions(
        self,
        user_permissions: List[str],
        required_list: List[str]
    ) -> bool:
        """检查是否拥有所有权限

        Args:
            user_permissions: 用户拥有的权限列表
            required_list: 需要的权限列表

        Returns:
            是否拥有所有权限
        """
        pass

    @abstractmethod
    def has_tenant_access(
        self,
        user_tenant_id: str,
        target_tenant_id: str,
        permissions: List[str]
    ) -> bool:
        """检查租户访问权限

        Args:
            user_tenant_id: 用户所属租户
            target_tenant_id: 目标租户
            permissions: 用户权限

        Returns:
            是否可以访问目标租户
        """
        pass


class RateLimiterInterface(ABC):
    """速率限制器接口

    提供请求速率限制功能，防止暴力攻击。
    """

    @abstractmethod
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求

        Args:
            identifier: 请求标识（如IP地址、用户ID）

        Returns:
            是否允许请求
        """
        pass

    @abstractmethod
    def get_remaining(self, identifier: str) -> int:
        """获取剩余请求次数

        Args:
            identifier: 请求标识

        Returns:
            剩余请求次数
        """
        pass

    @abstractmethod
    def reset(self, identifier: str) -> None:
        """重置限制

        Args:
            identifier: 请求标识
        """
        pass
