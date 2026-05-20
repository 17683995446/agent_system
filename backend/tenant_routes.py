"""
租户管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime, timezone

from backend.database import get_db, TenantDB, TenantQuotaDB
from backend.schemas import (
    Tenant, TenantCreate, TenantUpdate, TenantQuota, 
    TenantStatus, TenantTier, TenantTierUpdate, MessageResponse
)

router = APIRouter(prefix="/api/tenants", tags=["租户管理"])

def get_default_quota(tier: TenantTier) -> TenantQuota:
    quotas = {
        TenantTier.FREE: TenantQuota(
            max_agents=5,
            max_storage_mb=500,
            max_requests_per_minute=100,
            max_api_keys=2,
            max_users=2,
            ai_credit_monthly=100
        ),
        TenantTier.BASIC: TenantQuota(
            max_agents=20,
            max_storage_mb=5000,
            max_requests_per_minute=1000,
            max_api_keys=5,
            max_users=10,
            ai_credit_monthly=1000
        ),
        TenantTier.PRO: TenantQuota(
            max_agents=100,
            max_storage_mb=50000,
            max_requests_per_minute=5000,
            max_api_keys=20,
            max_users=50,
            ai_credit_monthly=10000
        ),
        TenantTier.ENTERPRISE: TenantQuota(
            max_agents=1000,
            max_storage_mb=500000,
            max_requests_per_minute=50000,
            max_api_keys=100,
            max_users=500,
            ai_credit_monthly=100000
        ),
        TenantTier.UNLIMITED: TenantQuota(
            max_agents=99999,
            max_storage_mb=999999,
            max_requests_per_minute=999999,
            max_api_keys=999,
            max_users=9999,
            ai_credit_monthly=999999
        )
    }
    return quotas.get(tier, TenantQuota())

@router.get("", response_model=List[Tenant])
async def get_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantDB))
    tenants = result.scalars().all()
    
    tenant_responses = []
    for tenant_db in tenants:
        quota_result = await db.execute(select(TenantQuotaDB).where(TenantQuotaDB.tenant_id == tenant_db.tenant_id))
        quota_db = quota_result.scalar_one_or_none()
        
        quota = TenantQuota(
            max_agents=quota_db.max_agents if quota_db else 10,
            max_storage_mb=quota_db.max_storage_mb if quota_db else 1000,
            max_requests_per_minute=quota_db.max_requests_per_minute if quota_db else 1000,
            max_api_keys=quota_db.max_api_keys if quota_db else 5,
            max_users=quota_db.max_users if quota_db else 10,
            max_workflows=quota_db.max_workflows if quota_db else 10,
            ai_credit_monthly=quota_db.ai_credit_monthly if quota_db else 1000,
            max_concurrent_jobs=quota_db.max_concurrent_jobs if quota_db else 5
        )
        
        tenant_responses.append(Tenant(
            id=tenant_db.tenant_id,
            name=tenant_db.name,
            slug=tenant_db.slug,
            email=tenant_db.email,
            owner_id=tenant_db.owner_id,
            status=TenantStatus(tenant_db.status),
            tier=TenantTier(tenant_db.tier),
            quota=quota,
            created_at=tenant_db.created_at,
            updated_at=tenant_db.updated_at
        ))
    
    return tenant_responses

@router.post("", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_in: TenantCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(TenantDB).where(TenantDB.slug == tenant_in.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="租户标识已存在")
    
    tenant_id = str(uuid.uuid4())
    tenant_db = TenantDB(
        tenant_id=tenant_id,
        name=tenant_in.name,
        slug=tenant_in.slug,
        email=tenant_in.email,
        owner_id=tenant_in.owner_id,
        status=TenantStatus.ACTIVE.value,
        tier=tenant_in.tier.value
    )
    db.add(tenant_db)
    
    quota = get_default_quota(tenant_in.tier)
    quota_db = TenantQuotaDB(
        tenant_id=tenant_id,
        max_agents=quota.max_agents,
        max_storage_mb=quota.max_storage_mb,
        max_requests_per_minute=quota.max_requests_per_minute,
        max_api_keys=quota.max_api_keys,
        max_users=quota.max_users,
        max_workflows=quota.max_workflows,
        ai_credit_monthly=quota.ai_credit_monthly,
        max_concurrent_jobs=quota.max_concurrent_jobs
    )
    db.add(quota_db)
    
    await db.commit()
    await db.refresh(tenant_db)
    
    return Tenant(
        id=tenant_db.tenant_id,
        name=tenant_db.name,
        slug=tenant_db.slug,
        email=tenant_db.email,
        owner_id=tenant_db.owner_id,
        status=TenantStatus(tenant_db.status),
        tier=TenantTier(tenant_db.tier),
        quota=quota,
        created_at=tenant_db.created_at,
        updated_at=tenant_db.updated_at
    )

@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantDB).where(TenantDB.tenant_id == tenant_id))
    tenant_db = result.scalar_one_or_none()
    
    if not tenant_db:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    quota_result = await db.execute(select(TenantQuotaDB).where(TenantQuotaDB.tenant_id == tenant_id))
    quota_db = quota_result.scalar_one_or_none()
    
    quota = TenantQuota(
        max_agents=quota_db.max_agents if quota_db else 10,
        max_storage_mb=quota_db.max_storage_mb if quota_db else 1000,
        max_requests_per_minute=quota_db.max_requests_per_minute if quota_db else 1000,
        max_api_keys=quota_db.max_api_keys if quota_db else 5,
        max_users=quota_db.max_users if quota_db else 10,
        max_workflows=quota_db.max_workflows if quota_db else 10,
        ai_credit_monthly=quota_db.ai_credit_monthly if quota_db else 1000,
        max_concurrent_jobs=quota_db.max_concurrent_jobs if quota_db else 5
    )
    
    return Tenant(
        id=tenant_db.tenant_id,
        name=tenant_db.name,
        slug=tenant_db.slug,
        email=tenant_db.email,
        owner_id=tenant_db.owner_id,
        status=TenantStatus(tenant_db.status),
        tier=TenantTier(tenant_db.tier),
        quota=quota,
        created_at=tenant_db.created_at,
        updated_at=tenant_db.updated_at
    )

@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(tenant_id: str, tenant_in: TenantUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantDB).where(TenantDB.tenant_id == tenant_id))
    tenant_db = result.scalar_one_or_none()
    
    if not tenant_db:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    if tenant_in.name is not None:
        tenant_db.name = tenant_in.name
    if tenant_in.email is not None:
        tenant_db.email = tenant_in.email
    if tenant_in.status is not None:
        tenant_db.status = tenant_in.status.value
    
    tenant_db.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(tenant_db)
    
    quota_result = await db.execute(select(TenantQuotaDB).where(TenantQuotaDB.tenant_id == tenant_id))
    quota_db = quota_result.scalar_one_or_none()
    
    quota = TenantQuota(
        max_agents=quota_db.max_agents if quota_db else 10,
        max_storage_mb=quota_db.max_storage_mb if quota_db else 1000,
        max_requests_per_minute=quota_db.max_requests_per_minute if quota_db else 1000,
        max_api_keys=quota_db.max_api_keys if quota_db else 5,
        max_users=quota_db.max_users if quota_db else 10,
        max_workflows=quota_db.max_workflows if quota_db else 10,
        ai_credit_monthly=quota_db.ai_credit_monthly if quota_db else 1000,
        max_concurrent_jobs=quota_db.max_concurrent_jobs if quota_db else 5
    )
    
    return Tenant(
        id=tenant_db.tenant_id,
        name=tenant_db.name,
        slug=tenant_db.slug,
        email=tenant_db.email,
        owner_id=tenant_db.owner_id,
        status=TenantStatus(tenant_db.status),
        tier=TenantTier(tenant_db.tier),
        quota=quota,
        created_at=tenant_db.created_at,
        updated_at=tenant_db.updated_at
    )

@router.delete("/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(tenant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantDB).where(TenantDB.tenant_id == tenant_id))
    tenant_db = result.scalar_one_or_none()
    
    if not tenant_db:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    await db.delete(tenant_db)
    await db.commit()
    
    return MessageResponse(message="租户已删除")

@router.put("/{tenant_id}/tier", response_model=Tenant)
async def update_tenant_tier(tenant_id: str, tier_in: TenantTierUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantDB).where(TenantDB.tenant_id == tenant_id))
    tenant_db = result.scalar_one_or_none()
    
    if not tenant_db:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    tenant_db.tier = tier_in.tier.value
    tenant_db.updated_at = datetime.now(timezone.utc)
    
    quota_result = await db.execute(select(TenantQuotaDB).where(TenantQuotaDB.tenant_id == tenant_id))
    quota_db = quota_result.scalar_one_or_none()
    
    new_quota = get_default_quota(tier_in.tier)
    if quota_db:
        quota_db.max_agents = new_quota.max_agents
        quota_db.max_storage_mb = new_quota.max_storage_mb
        quota_db.max_requests_per_minute = new_quota.max_requests_per_minute
        quota_db.max_api_keys = new_quota.max_api_keys
        quota_db.max_users = new_quota.max_users
        quota_db.max_workflows = new_quota.max_workflows
        quota_db.ai_credit_monthly = new_quota.ai_credit_monthly
        quota_db.max_concurrent_jobs = new_quota.max_concurrent_jobs
    else:
        quota_db = TenantQuotaDB(
            tenant_id=tenant_id,
            **new_quota.model_dump()
        )
        db.add(quota_db)
    
    await db.commit()
    await db.refresh(tenant_db)
    
    return Tenant(
        id=tenant_db.tenant_id,
        name=tenant_db.name,
        slug=tenant_db.slug,
        email=tenant_db.email,
        owner_id=tenant_db.owner_id,
        status=TenantStatus(tenant_db.status),
        tier=TenantTier(tenant_db.tier),
        quota=new_quota,
        created_at=tenant_db.created_at,
        updated_at=tenant_db.updated_at
    )
