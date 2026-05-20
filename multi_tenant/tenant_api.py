"""
多租户 API 端点
包含租户管理、配额检查、计费、SLA 等 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any, Set
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from .tenant_core import (
    Tenant, TenantStatus, TenantTier, TenantRegistry,
    TenantQuota, TenantSLA, TenantBranding, TenantAPIKey
)
import enum


router = APIRouter(prefix="/api/v1/tenants", tags=["Multi-Tenant"])


# 数据模型
class TenantCreate(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    email: EmailStr
    tier: TenantTier = TenantTier.FREE
    is_isolated: bool = False


class TenantUpdate(BaseModel):
    """更新租户请求"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[TenantStatus] = None
    tier: Optional[TenantTier] = None


class TenantQuotaUpdate(BaseModel):
    """更新租户配额请求"""
    max_agents: Optional[int] = None
    max_storage_mb: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_api_keys: Optional[int] = None
    max_users: Optional[int] = None
    ai_credit_monthly: Optional[int] = None


class TenantBrandingUpdate(BaseModel):
    """更新租户品牌请求"""
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    email_sender: Optional[str] = None


class APIKeyCreate(BaseModel):
    """创建 API 密钥请求"""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=list)
    expires_days: int = 90


class TenantResponse(BaseModel):
    """租户响应"""
    tenant_id: UUID
    name: str
    slug: str
    status: TenantStatus
    tier: TenantTier
    email: str
    created_at: datetime
    updated_at: datetime
    is_isolated_database: bool
    
    class Config:
        from_attributes = True


class TenantDetailResponse(TenantResponse):
    """租户详情响应"""
    quota: TenantQuota
    sla: TenantSLA
    branding: TenantBranding
    usage: Dict[str, Any]


class APIKeyResponse(BaseModel):
    """API 密钥响应"""
    key_id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool


# 依赖注入
def get_tenant_registry() -> TenantRegistry:
    """获取租户注册表"""
    from .tenant_core import tenant_registry
    return tenant_registry


async def get_current_tenant(
    x_tenant_id: Optional[str] = Header(None),
    x_tenant_slug: Optional[str] = Header(None),
    registry: TenantRegistry = Depends(get_tenant_registry)
) -> Tenant:
    """获取当前租户"""
    tenant: Optional[Tenant] = None
    
    if x_tenant_id:
        try:
            tenant = registry.get_tenant(UUID(x_tenant_id))
        except ValueError:
            pass
    
    if not tenant and x_tenant_slug:
        tenant = registry.get_tenant_by_slug(x_tenant_slug)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is {tenant.status.value}"
        )
    
    return tenant


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    创建新租户
    """
    # 检查 slug 是否已存在
    existing = registry.get_tenant_by_slug(tenant_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant slug already exists"
        )
    
    # 创建租户
    tenant = registry.create_tenant(
        name=tenant_data.name,
        slug=tenant_data.slug,
        email=tenant_data.email,
        owner_id=uuid4(),
        tier=tenant_data.tier,
        is_isolated=tenant_data.is_isolated
    )
    
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        tier=tenant.tier,
        email=tenant.email,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        is_isolated_database=tenant.is_isolated_database
    )


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant(
    tenant_id: UUID,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    获取租户详情
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantDetailResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        tier=tenant.tier,
        email=tenant.email,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        is_isolated_database=tenant.is_isolated_database,
        quota=tenant.quota,
        sla=tenant.sla,
        branding=tenant.branding,
        usage={
            "agents_created": tenant.usage.agents_created,
            "storage_used_mb": tenant.usage.storage_used_mb,
            "ai_credits_used": tenant.usage.ai_credits_used,
            "total_api_calls": tenant.usage.total_api_calls,
            "active_users": tenant.usage.active_users,
            "last_activity_at": tenant.usage.last_activity_at
        }
    )


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    列出所有租户
    """
    tenants = registry.list_tenants(status=status)
    return [
        TenantResponse(
            tenant_id=t.tenant_id,
            name=t.name,
            slug=t.slug,
            status=t.status,
            tier=t.tier,
            email=t.email,
            created_at=t.created_at,
            updated_at=t.updated_at,
            is_isolated_database=t.is_isolated_database
        )
        for t in tenants
    ]


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    update_data: TenantUpdate,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    更新租户信息
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if update_data.name:
        tenant.name = update_data.name
    if update_data.email:
        tenant.email = update_data.email
    if update_data.status:
        registry.update_tenant_status(tenant_id, update_data.status)
    if update_data.tier:
        from .tenant_core import tenant_migrator
        await tenant_migrator.upgrade_tenant_tier(tenant_id, update_data.tier)
    
    tenant.updated_at = datetime.utcnow()
    
    return TenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        tier=tenant.tier,
        email=tenant.email,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        is_isolated_database=tenant.is_isolated_database
    )


@router.patch("/{tenant_id}/quota", response_model=TenantDetailResponse)
async def update_tenant_quota(
    tenant_id: UUID,
    quota_data: TenantQuotaUpdate,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    更新租户配额
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    new_quota = TenantQuota(
        max_agents=quota_data.max_agents or tenant.quota.max_agents,
        max_storage_mb=quota_data.max_storage_mb or tenant.quota.max_storage_mb,
        max_requests_per_minute=quota_data.max_requests_per_minute or tenant.quota.max_requests_per_minute,
        max_api_keys=quota_data.max_api_keys or tenant.quota.max_api_keys,
        max_users=quota_data.max_users or tenant.quota.max_users,
        ai_credit_monthly=quota_data.ai_credit_monthly or tenant.quota.ai_credit_monthly
    )
    
    registry.update_tenant_quota(tenant_id, new_quota)
    
    return await get_tenant(tenant_id, registry)


@router.patch("/{tenant_id}/branding", response_model=TenantDetailResponse)
async def update_tenant_branding(
    tenant_id: UUID,
    branding_data: TenantBrandingUpdate,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    更新租户品牌定制
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    new_branding = TenantBranding(
        company_name=branding_data.company_name or tenant.branding.company_name,
        logo_url=branding_data.logo_url or tenant.branding.logo_url,
        primary_color=branding_data.primary_color or tenant.branding.primary_color,
        secondary_color=branding_data.secondary_color or tenant.branding.secondary_color,
        custom_domain=branding_data.custom_domain or tenant.branding.custom_domain,
        email_sender=branding_data.email_sender or tenant.branding.email_sender
    )
    
    registry.update_tenant_branding(tenant_id, new_branding)
    
    return await get_tenant(tenant_id, registry)


@router.post("/{tenant_id}/api-keys", response_model=APIKeyResponse, status_code=201)
async def generate_api_key(
    tenant_id: UUID,
    key_data: APIKeyCreate,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    生成租户 API 密钥
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    api_key = registry.generate_api_key(
        tenant_id=tenant_id,
        name=key_data.name,
        scopes=set(key_data.scopes),
        expires_days=key_data.expires_days
    )
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Could not generate API key")
    
    return APIKeyResponse(
        key_id=api_key.key_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=list(api_key.scopes),
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active
    )


@router.get("/{tenant_id}/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    tenant_id: UUID,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    列出租户的 API 密钥
    """
    tenant = registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return [
        APIKeyResponse(
            key_id=k.key_id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=list(k.scopes),
            created_at=k.created_at,
            expires_at=k.expires_at,
            is_active=k.is_active
        )
        for k in tenant.api_keys
    ]


@router.post("/{tenant_id}/check-quota")
async def check_tenant_quota(
    tenant_id: UUID,
    resource_type: str,
    amount: int = 1,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    检查租户配额
    """
    is_allowed = registry.check_quota(tenant_id, resource_type, amount)
    return {"allowed": is_allowed, "resource_type": resource_type, "amount": amount}


@router.post("/{tenant_id}/record-usage")
async def record_tenant_usage(
    tenant_id: UUID,
    resource_type: str,
    amount: int = 1,
    registry: TenantRegistry = Depends(get_tenant_registry)
):
    """
    记录租户使用量
    """
    success = registry.record_usage(tenant_id, resource_type, amount)
    return {"success": success, "resource_type": resource_type, "amount": amount}
