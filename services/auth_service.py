"""
认证应用服务

提供身份认证和授权的业务逻辑，包括Token管理、API Key管理、权限检查等。
"""

import logging
from typing import Optional, Dict, Any, List

from interfaces.security import (
    TokenManagerInterface,
    APIKeyManagerInterface,
    PermissionCheckerInterface,
    RateLimiterInterface
)
from exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ValidationError
)

logger = logging.getLogger(__name__)


class AuthService:
    """认证应用服务

    提供身份认证和授权的业务逻辑，包括：
    - Token生成和验证
    - API Key管理
    - 权限检查
    - 速率限制

    Attributes:
        token_manager: Token管理器接口
        api_key_manager: API Key管理器接口
        permission_checker: 权限检查器接口
        rate_limiter: 速率限制器接口
    """

    def __init__(
        self,
        token_manager: TokenManagerInterface,
        api_key_manager: APIKeyManagerInterface,
        permission_checker: PermissionCheckerInterface,
        rate_limiter: RateLimiterInterface
    ):
        self.token_manager = token_manager
        self.api_key_manager = api_key_manager
        self.permission_checker = permission_checker
        self.rate_limiter = rate_limiter
        logger.info("[AuthService] 初始化完成")

    def authenticate_with_token(self, token: str) -> Dict[str, Any]:
        """使用Token认证

        Args:
            token: JWT Token

        Returns:
            认证信息，包含用户ID、租户ID、权限等

        Raises:
            AuthenticationError: Token无效或过期
        """
        if not token:
            raise AuthenticationError("Token is required")

        # 验证Token
        payload = self.token_manager.verify_token(token)
        if not payload:
            raise AuthenticationError("Invalid or expired token")

        # 检查是否已撤销
        token_id = payload.get("jti")
        if token_id and self.token_manager.is_token_blacklisted(token_id):
            raise AuthenticationError("Token has been revoked")

        logger.debug(f"[AuthService] Token认证成功: {payload.get('sub')}")
        return payload

    def authenticate_with_api_key(self, api_key: str) -> Dict[str, Any]:
        """使用API Key认证

        Args:
            api_key: API Key

        Returns:
            API Key信息

        Raises:
            AuthenticationError: API Key无效
        """
        if not api_key:
            raise AuthenticationError("API Key is required", auth_type="api_key")

        # 验证API Key
        key_info = self.api_key_manager.verify_api_key(api_key)
        if not key_info:
            raise AuthenticationError("Invalid API Key", auth_type="api_key")

        logger.debug(f"[AuthService] API Key认证成功: {key_info.get('key_id')}")
        return key_info

    def check_permission(
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

        Raises:
            PermissionDeniedError: 权限不足
        """
        if self.permission_checker.has_permission(user_permissions, required):
            return True

        raise PermissionDeniedError(required_permission=required)

    def check_tenant_access(
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
            是否可以访问

        Raises:
            PermissionDeniedError: 无权访问
        """
        if self.permission_checker.has_tenant_access(
            user_tenant_id, target_tenant_id, permissions
        ):
            return True

        raise PermissionDeniedError(
            message=f"Access to tenant {target_tenant_id} denied"
        )

    def check_rate_limit(self, identifier: str) -> None:
        """检查速率限制

        Args:
            identifier: 请求标识

        Raises:
            RateLimitError: 超过速率限制
        """
        if not self.rate_limiter.is_allowed(identifier):
            remaining = self.rate_limiter.get_remaining(identifier)
            raise RateLimitError(retry_after=remaining)

    def generate_token(
        self,
        user_id: str,
        tenant_id: str,
        permissions: List[str]
    ) -> Dict[str, str]:
        """生成Token

        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            permissions: 权限列表

        Returns:
            包含access_token和refresh_token的字典
        """
        access_token = self.token_manager.generate_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=permissions
        )
        refresh_token = self.token_manager.generate_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }

    def revoke_token(self, token: str) -> bool:
        """撤销Token

        Args:
            token: 要撤销的Token

        Returns:
            撤销是否成功
        """
        return self.token_manager.revoke_token(token)

    def create_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """创建API Key

        Args:
            tenant_id: 租户ID
            name: Key名称
            permissions: 权限列表
            expires_in_days: 过期天数

        Returns:
            API Key信息
        """
        return self.api_key_manager.generate_api_key(
            tenant_id=tenant_id,
            name=name,
            permissions=permissions,
            expires_in_days=expires_in_days
        )

    def revoke_api_key(self, key_id: str) -> bool:
        """撤销API Key

        Args:
            key_id: Key ID

        Returns:
            撤销是否成功
        """
        return self.api_key_manager.revoke_api_key(key_id)

    def list_api_keys(self, tenant_id: str) -> List[Dict[str, Any]]:
        """列出租户的API Keys

        Args:
            tenant_id: 租户ID

        Returns:
            API Key列表
        """
        return self.api_key_manager.list_keys(tenant_id)
