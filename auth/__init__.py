"""
认证模块 - JWT认证和授权
"""
from .jwt_auth_service import (
    JWTAuthService,
    get_auth_service,
    TokenType,
    UserRole,
    TokenPayload,
    AuthToken,
    User
)

from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_optional_user,
    require_roles,
    require_permissions,
    AuthenticationError,
    AuthorizationError,
    APIKeyAuth
)

__all__ = [
    "JWTAuthService",
    "get_auth_service",
    "TokenType",
    "UserRole",
    "TokenPayload",
    "AuthToken",
    "User",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_optional_user",
    "require_roles",
    "require_permissions",
    "AuthenticationError",
    "AuthorizationError",
    "APIKeyAuth"
]
