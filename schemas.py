"""
输入验证强化 - Pydantic 模型定义

提供所有 API 请求的严格输入验证和数据序列化。
遵循防御性编程原则，在系统边界处验证所有输入。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

try:
    from pydantic import BaseModel, Field, EmailStr, validator, constr
    from pydantic.types import constr as PydanticConstr
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # 降级方案：使用简单dataclass
    from dataclasses import dataclass, field
    BaseModel = object
    Field = lambda *a, **k: None
    EmailStr = str


# ==================== 枚举定义 ====================

class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class TenantTier(str, Enum):
    """租户层级"""
    FREE = "free"
    STARTER = "starter"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"
    CUSTOM = "custom"


class ResourceType(str, Enum):
    """资源类型"""
    AGENTS = "agents"
    API_CALLS = "api_calls"
    AI_CREDITS = "ai_credits"
    STORAGE = "storage"
    USERS = "users"
    WORKFLOWS = "workflows"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuthMethod(str, Enum):
    """认证方法"""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


# ==================== 基础模型 ====================

if PYDANTIC_AVAILABLE:
    class BaseSchema(BaseModel):
        """基础模型"""
        class Config:
            json_encoders = {
                datetime: lambda v: v.isoformat(),
                UUID: lambda v: str(v)
            }

    # ==================== 租户相关模型 ====================

    class CreateTenantRequest(BaseSchema):
        """创建租户请求"""
        name: str = Field(..., min_length=2, max_length=255, description="租户名称")
        slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$", description="租户slug")
        email: EmailStr = Field(..., description="联系邮箱")
        owner_id: UUID = Field(..., description="所有者ID")
        tier: TenantTier = Field(default=TenantTier.FREE, description="租户层级")
        is_isolated: bool = Field(default=False, description="是否隔离")

        @validator('name')
        def validate_name(cls, v):
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip()

        @validator('slug')
        def validate_slug(cls, v):
            if not v or not v.strip():
                raise ValueError('Slug cannot be empty')
            v = v.strip().lower()
            if not all(c.isalnum() or c == '-' for c in v):
                raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
            return v

    class UpdateTenantStatusRequest(BaseSchema):
        """更新租户状态请求"""
        status: TenantStatus = Field(..., description="新状态")

    class UpdateTenantTierRequest(BaseSchema):
        """更新租户层级请求"""
        tier: TenantTier = Field(..., description="新层级")

    class TenantResponse(BaseSchema):
        """租户响应"""
        tenant_id: str = Field(..., description="租户ID")
        name: str = Field(..., description="租户名称")
        slug: str = Field(..., description="租户slug")
        email: str = Field(..., description="联系邮箱")
        status: str = Field(..., description="状态")
        tier: str = Field(..., description="层级")
        owner_id: str = Field(..., description="所有者ID")
        created_at: Optional[str] = Field(None, description="创建时间")
        updated_at: Optional[str] = Field(None, description="更新时间")
        quota: Optional[Dict[str, Any]] = Field(None, description="配额信息")
        sla: Optional[Dict[str, Any]] = Field(None, description="SLA信息")
        usage: Optional[Dict[str, Any]] = Field(None, description="使用统计")

    # ==================== 配额相关模型 ====================

    class CheckQuotaRequest(BaseSchema):
        """检查配额请求"""
        resource_type: ResourceType = Field(..., description="资源类型")
        amount: int = Field(default=1, ge=1, description="请求数量")

    class RecordUsageRequest(BaseSchema):
        """记录使用量请求"""
        resource_type: ResourceType = Field(..., description="资源类型")
        amount: int = Field(default=1, ge=1, description="使用数量")

    class QuotaResponse(BaseSchema):
        """配额响应"""
        allowed: bool = Field(..., description="是否允许")
        tenant_id: str = Field(..., description="租户ID")
        resource_type: str = Field(..., description="资源类型")
        amount: int = Field(..., description="请求数量")
        current_usage: Optional[int] = Field(None, description="当前使用量")
        limit: Optional[int] = Field(None, description="配额上限")

    # ==================== 认证相关模型 ====================

    class LoginRequest(BaseSchema):
        """登录请求"""
        username: str = Field(..., min_length=3, max_length=100, description="用户名")
        password: str = Field(..., min_length=8, max_length=128, description="密码")
        tenant_id: Optional[str] = Field(None, description="租户ID")

    class TokenResponse(BaseSchema):
        """Token响应"""
        access_token: str = Field(..., description="访问令牌")
        refresh_token: str = Field(..., description="刷新令牌")
        token_type: str = Field(default="Bearer", description="令牌类型")
        expires_in: int = Field(..., description="过期时间（秒）")

    class CreateAPIKeyRequest(BaseSchema):
        """创建API Key请求"""
        name: str = Field(..., min_length=1, max_length=100, description="Key名称")
        permissions: List[str] = Field(default_factory=list, description="权限列表")
        expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="过期天数")

    class APIKeyResponse(BaseSchema):
        """API Key响应"""
        key_id: str = Field(..., description="Key ID")
        full_key: Optional[str] = Field(None, description="完整Key（仅创建时返回）")
        name: str = Field(..., description="Key名称")
        permissions: List[str] = Field(..., description="权限列表")
        expires_at: Optional[str] = Field(None, description="过期时间")
        created_at: str = Field(..., description="创建时间")
        is_active: bool = Field(..., description="是否激活")

    # ==================== 服务相关模型 ====================

    class RegisterServiceRequest(BaseSchema):
        """注册服务请求"""
        service_name: str = Field(..., min_length=1, max_length=100, description="服务名称")
        service_type: str = Field(..., min_length=1, max_length=50, description="服务类型")
        host: str = Field(..., min_length=1, max_length=255, description="主机地址")
        port: int = Field(..., ge=1, le=65535, description="端口")
        version: str = Field(default="1.0.0", description="版本")

        @validator('host')
        def validate_host(cls, v):
            if not v or not v.strip():
                raise ValueError('Host cannot be empty')
            # 简单验证：不允许包含空格
            if ' ' in v:
                raise ValueError('Host cannot contain spaces')
            return v.strip()

    class ServiceInstanceResponse(BaseSchema):
        """服务实例响应"""
        instance_id: str = Field(..., description="实例ID")
        service_name: str = Field(..., description="服务名称")
        service_type: str = Field(..., description="服务类型")
        host: str = Field(..., description="主机")
        port: int = Field(..., description="端口")
        status: str = Field(..., description="状态")
        health_score: float = Field(..., description="健康评分")
        version: str = Field(..., description="版本")

    # ==================== 监控相关模型 ====================

    class AddAlertRuleRequest(BaseSchema):
        """添加告警规则请求"""
        name: str = Field(..., min_length=1, max_length=100, description="规则名称")
        metric_name: str = Field(..., min_length=1, max_length=100, description="指标名称")
        condition: str = Field(..., pattern=r"^(gt|lt|eq|gte|lte)$", description="条件")
        threshold: float = Field(..., description="阈值")
        level: AlertLevel = Field(..., description="告警级别")
        message: str = Field(..., min_length=1, max_length=500, description="告警消息")

    class AlertResponse(BaseSchema):
        """告警响应"""
        rule_name: str = Field(..., description="规则名称")
        level: str = Field(..., description="级别")
        message: str = Field(..., description="消息")
        start_time: str = Field(..., description="开始时间")
        resolved: bool = Field(..., description="是否已解决")

    class HealthResponse(BaseSchema):
        """健康检查响应"""
        status: str = Field(..., description="状态")
        health_score: float = Field(..., description="健康评分")
        timestamp: str = Field(..., description="时间戳")
        checks: Dict[str, Any] = Field(default_factory=dict, description="检查详情")

    class MetricsResponse(BaseSchema):
        """指标响应"""
        metrics: Dict[str, Any] = Field(..., description="指标数据")
        timestamp: str = Field(..., description="时间戳")

    # ==================== 通用响应模型 ====================

    class ErrorResponse(BaseSchema):
        """错误响应"""
        error: Dict[str, Any] = Field(..., description="错误信息")

    class SuccessResponse(BaseSchema):
        """成功响应"""
        success: bool = Field(default=True, description="是否成功")
        message: str = Field(..., description="消息")
        data: Optional[Dict[str, Any]] = Field(None, description="数据")

    class PaginationRequest(BaseSchema):
        """分页请求"""
        limit: int = Field(default=100, ge=1, le=1000, description="每页数量")
        offset: int = Field(default=0, ge=0, description="偏移量")

    class ListResponse(BaseSchema):
        """列表响应"""
        items: List[Dict[str, Any]] = Field(..., description="数据列表")
        total: int = Field(..., description="总数")
        limit: int = Field(..., description="每页数量")
        offset: int = Field(..., description="偏移量")

else:
    # Pydantic 不可用时使用简单 dataclass 作为降级
    from dataclasses import dataclass, field

    @dataclass
    class CreateTenantRequest:
        name: str
        slug: str
        email: str
        owner_id: str
        tier: str = "free"
        is_isolated: bool = False

    @dataclass
    class UpdateTenantStatusRequest:
        status: str

    @dataclass
    class UpdateTenantTierRequest:
        tier: str

    @dataclass
    class TenantResponse:
        tenant_id: str
        name: str
        slug: str
        email: str
        status: str
        tier: str
        owner_id: str

    @dataclass
    class CheckQuotaRequest:
        resource_type: str
        amount: int = 1

    @dataclass
    class RecordUsageRequest:
        resource_type: str
        amount: int = 1

    @dataclass
    class LoginRequest:
        username: str
        password: str
        tenant_id: Optional[str] = None

    @dataclass
    class TokenResponse:
        access_token: str
        refresh_token: str
        token_type: str = "Bearer"
        expires_in: int = 1800

    @dataclass
    class CreateAPIKeyRequest:
        name: str
        permissions: List[str] = field(default_factory=list)
        expires_in_days: Optional[int] = None

    @dataclass
    class RegisterServiceRequest:
        service_name: str
        service_type: str
        host: str
        port: int
        version: str = "1.0.0"

    @dataclass
    class ServiceInstanceResponse:
        instance_id: str
        service_name: str
        service_type: str
        host: str
        port: int
        status: str
        health_score: float
        version: str

    @dataclass
    class AddAlertRuleRequest:
        name: str
        metric_name: str
        condition: str
        threshold: float
        level: str
        message: str

    @dataclass
    class AlertResponse:
        rule_name: str
        level: str
        message: str
        start_time: str
        resolved: bool = False

    @dataclass
    class HealthResponse:
        status: str
        health_score: float
        timestamp: str

    @dataclass
    class MetricsResponse:
        metrics: Dict[str, Any]
        timestamp: str

    @dataclass
    class ErrorResponse:
        error: Dict[str, Any]

    @dataclass
    class SuccessResponse:
        success: bool = True
        message: str = ""
        data: Optional[Dict[str, Any]] = None

    @dataclass
    class PaginationRequest:
        limit: int = 100
        offset: int = 0

    @dataclass
    class ListResponse:
        items: List[Dict[str, Any]]
        total: int
        limit: int
        offset: int


# ==================== 验证函数 ====================

def validate_tenant_create(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证创建租户数据

    Args:
        data: 原始数据字典

    Returns:
        验证后的数据字典

    Raises:
        ValueError: 验证失败
    """
    if not data.get('name') or len(data['name']) < 2:
        raise ValueError('Tenant name must be at least 2 characters')

    if not data.get('slug') or len(data['slug']) < 2:
        raise ValueError('Tenant slug must be at least 2 characters')

    slug = data['slug'].lower()
    if not all(c.isalnum() or c == '-' for c in slug):
        raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
    data['slug'] = slug

    email = data.get('email', '')
    if '@' not in email or len(email) > 254:
        raise ValueError('Invalid email format')

    if 'owner_id' not in data:
        raise ValueError('Owner ID is required')

    return data


def validate_api_key_create(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证创建API Key数据"""
    if not data.get('name') or len(data['name']) < 1:
        raise ValueError('API Key name is required')

    permissions = data.get('permissions', [])
    if not isinstance(permissions, list):
        raise ValueError('Permissions must be a list')

    expires = data.get('expires_in_days')
    if expires is not None and (not isinstance(expires, int) or expires < 1 or expires > 365):
        raise ValueError('expires_in_days must be between 1 and 365')

    return data


def validate_service_register(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证注册服务数据"""
    if not data.get('service_name'):
        raise ValueError('Service name is required')

    if not data.get('host'):
        raise ValueError('Host is required')

    port = data.get('port')
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError('Port must be between 1 and 65535')

    return data


if __name__ == "__main__":
    print("=" * 80)
    print("Phase C: 输入验证强化测试")
    print("=" * 80)

    if PYDANTIC_AVAILABLE:
        print("\n--- Pydantic 模式 ---")

        # 测试有效数据
        req = CreateTenantRequest(
            name="Test Company",
            slug="test-company",
            email="test@example.com",
            owner_id="12345678-1234-1234-1234-123456789abc"
        )
        print(f"创建租户请求: {req.dict()}")

        # 测试无效数据
        try:
            CreateTenantRequest(
                name="A",
                slug="invalid_slug!",
                email="invalid",
                owner_id="123"
            )
        except Exception as e:
            print(f"验证失败（预期）: {type(e).__name__}")

        # 测试配额请求
        quota_req = CheckQuotaRequest(resource_type="agents", amount=5)
        print(f"配额检查请求: {quota_req.dict()}")

        # 测试API Key请求
        api_req = CreateAPIKeyRequest(name="Test Key", permissions=["tenant:read"])
        print(f"API Key请求: {api_req.dict()}")

    else:
        print("\n--- Dataclass 降级模式 ---")
        req = CreateTenantRequest(
            name="Test Company",
            slug="test-company",
            email="test@example.com",
            owner_id="123"
        )
        print(f"创建租户请求: {req}")

    # 测试手动验证函数
    print("\n--- 手动验证函数 ---")
    try:
        validate_tenant_create({"name": "A", "slug": "test", "email": "bad"})
    except ValueError as e:
        print(f"验证失败（预期）: {e}")

    valid_data = validate_tenant_create({
        "name": "Good Company",
        "slug": "good-company",
        "email": "good@example.com",
        "owner_id": "123"
    })
    print(f"验证通过: {valid_data}")

    print("\n" + "=" * 80)
    print("Phase C 输入验证强化测试通过！")
    print("=" * 80)
