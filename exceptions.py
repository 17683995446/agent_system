"""
系统异常定义模块

提供统一的异常层次结构，所有模块必须使用此模块定义的异常。
遵循"一个模块，一种异常"的原则，确保错误处理的一致性。
"""

from typing import Optional, Dict, Any


class SystemException(Exception):
    """系统基础异常

    所有系统异常的基类，提供统一的错误信息格式。

    Attributes:
        code: 错误代码
        message: 错误消息
        details: 错误详情
        status_code: HTTP状态码（用于API层）
    """

    def __init__(
        self,
        message: str,
        code: str = "SYSTEM_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            包含错误信息的字典
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "status_code": self.status_code
            }
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ValidationError(SystemException):
    """数据验证错误

    当输入数据不符合要求时抛出。
    对应HTTP 400错误。
    """

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )


class NotFoundError(SystemException):
    """资源不存在错误

    当请求的资源不存在时抛出。
    对应HTTP 404错误。
    """

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Optional[str] = None
    ):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"

        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )


class DuplicateError(SystemException):
    """资源重复错误

    当创建的资源已存在时抛出。
    对应HTTP 409错误。
    """

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Optional[str] = None
    ):
        message = f"{resource} already exists"
        if identifier:
            message = f"{resource} '{identifier}' already exists"

        super().__init__(
            message=message,
            code="DUPLICATE_ERROR",
            details={"resource": resource, "identifier": identifier},
            status_code=409
        )


class PermissionDeniedError(SystemException):
    """权限不足错误

    当用户没有足够权限时抛出。
    对应HTTP 403错误。
    """

    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            details=details,
            status_code=403
        )


class AuthenticationError(SystemException):
    """认证错误

    当认证失败时抛出（Token无效、过期等）。
    对应HTTP 401错误。
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        auth_type: Optional[str] = None
    ):
        details = {}
        if auth_type:
            details["auth_type"] = auth_type

        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401
        )


class RateLimitError(SystemException):
    """速率限制错误

    当请求超过速率限制时抛出。
    对应HTTP 429错误。
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=429
        )


class CacheException(SystemException):
    """缓存异常

    当缓存操作失败时抛出。
    """

    def __init__(
        self,
        message: str = "Cache operation failed",
        operation: Optional[str] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details=details,
            status_code=500
        )


class DatabaseError(SystemException):
    """数据库错误

    当数据库操作失败时抛出。
    """

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details,
            status_code=500
        )


class ServiceUnavailableError(SystemException):
    """服务不可用错误

    当依赖的服务不可用时抛出。
    对应HTTP 503错误。
    """

    def __init__(
        self,
        message: str = "Service unavailable",
        service: Optional[str] = None
    ):
        details = {}
        if service:
            details["service"] = service

        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            details=details,
            status_code=503
        )


class ConfigurationError(SystemException):
    """配置错误

    当配置无效或缺失时抛出。
    """

    def __init__(
        self,
        message: str = "Invalid configuration",
        config_key: Optional[str] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            status_code=500
        )


class TenantError(SystemException):
    """租户相关错误

    当租户操作失败时抛出。
    """

    def __init__(
        self,
        message: str = "Tenant operation failed",
        tenant_id: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if tenant_id:
            details["tenant_id"] = tenant_id
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code="TENANT_ERROR",
            details=details,
            status_code=400
        )


class QuotaExceededError(SystemException):
    """配额超限错误

    当租户使用超出配额时抛出。
    对应HTTP 429错误。
    """

    def __init__(
        self,
        message: str = "Quota exceeded",
        resource_type: Optional[str] = None,
        current: Optional[int] = None,
        limit: Optional[int] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if current is not None:
            details["current_usage"] = current
        if limit is not None:
            details["quota_limit"] = limit

        super().__init__(
            message=message,
            code="QUOTA_EXCEEDED",
            details=details,
            status_code=429
        )
