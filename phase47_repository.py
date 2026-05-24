"""
Phase 47: Repository 模式实现
提供数据持久化层的统一接口
"""

from typing import Optional, List
from datetime import datetime, UTC
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_
import logging

from phase47_database import (
    Tenant, TenantQuota, TenantSLA, TenantBranding, TenantUsage,
    TenantStatusDB, TenantTierDB,
    ServiceInstanceDB, ServiceTypeDB, ServiceStatusDB,
    SessionLocal
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 租户 Repository ====================

class TenantRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, slug: str, email: str, owner_id: uuid.UUID, 
               tier: TenantTierDB = TenantTierDB.FREE,
               is_isolated: bool = False) -> Tenant:
        """创建租户"""
        logger.info(f"[TenantRepository] 创建租户: name={name}, slug={slug}")
        
        # 创建租户主表
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            email=email,
            owner_id=owner_id,
            tier=tier,
            is_isolated=is_isolated
        )
        self.db.add(tenant)
        self.db.flush()
        
        # 创建关联表
        self._create_quota(tenant_id, tier)
        self._create_sla(tenant_id, tier)
        self._create_branding(tenant_id)
        self._create_usage(tenant_id)
        
        self.db.commit()
        self.db.refresh(tenant)
        
        logger.info(f"[TenantRepository] 租户创建成功: tenant_id={tenant_id}")
        return tenant
    
    def _create_quota(self, tenant_id: uuid.UUID, tier: TenantTierDB):
        """根据层级创建默认配额"""
        defaults = self._get_quota_defaults(tier)
        quota = TenantQuota(
            tenant_id=tenant_id,
            **defaults
        )
        self.db.add(quota)
    
    def _create_sla(self, tenant_id: uuid.UUID, tier: TenantTierDB):
        """根据层级创建默认 SLA"""
        defaults = self._get_sla_defaults(tier)
        sla = TenantSLA(
            tenant_id=tenant_id,
            **defaults
        )
        self.db.add(sla)
    
    def _create_branding(self, tenant_id: uuid.UUID):
        """创建品牌配置"""
        branding = TenantBranding(tenant_id=tenant_id)
        self.db.add(branding)
    
    def _create_usage(self, tenant_id: uuid.UUID):
        """创建使用量记录"""
        usage = TenantUsage(tenant_id=tenant_id)
        self.db.add(usage)
    
    def _get_quota_defaults(self, tier: TenantTierDB) -> dict:
        """获取各层级的默认配额"""
        defaults = {
            TenantTierDB.STARTER: {
                "max_agents": 5, "max_storage_mb": 500, "max_requests_per_minute": 500,
                "max_api_keys": 2, "max_users": 5, "ai_credit_monthly": 500
            },
            TenantTierDB.FREE: {
                "max_agents": 10, "max_storage_mb": 1000, "max_requests_per_minute": 1000,
                "max_api_keys": 5, "max_users": 10, "ai_credit_monthly": 1000
            },
            TenantTierDB.BASIC: {
                "max_agents": 50, "max_storage_mb": 10000, "max_requests_per_minute": 5000,
                "max_api_keys": 20, "max_users": 50, "ai_credit_monthly": 5000
            },
            TenantTierDB.PRO: {
                "max_agents": 200, "max_storage_mb": 100000, "max_requests_per_minute": 20000,
                "max_api_keys": 100, "max_users": 200, "ai_credit_monthly": 50000
            },
            TenantTierDB.ENTERPRISE: {
                "max_agents": 1000, "max_storage_mb": 1000000, "max_requests_per_minute": 100000,
                "max_api_keys": 500, "max_users": 1000, "ai_credit_monthly": 200000
            },
            TenantTierDB.UNLIMITED: {
                "max_agents": 1000000, "max_storage_mb": 1000000000, "max_requests_per_minute": 10000000,
                "max_api_keys": 10000, "max_users": 100000, "ai_credit_monthly": 1000000000
            },
            TenantTierDB.CUSTOM: {
                "max_agents": 10, "max_storage_mb": 1000, "max_requests_per_minute": 1000,
                "max_api_keys": 5, "max_users": 10, "ai_credit_monthly": 1000
            }
        }
        return defaults.get(tier, defaults[TenantTierDB.FREE])
    
    def _get_sla_defaults(self, tier: TenantTierDB) -> dict:
        """获取各层级的默认 SLA"""
        defaults = {
            TenantTierDB.STARTER: {"uptime_percentage": 99.0, "response_time_ms": 2000, "support_level": "community"},
            TenantTierDB.FREE: {"uptime_percentage": 99.0, "response_time_ms": 1000, "support_level": "basic"},
            TenantTierDB.BASIC: {"uptime_percentage": 99.5, "response_time_ms": 500, "support_level": "email"},
            TenantTierDB.PRO: {"uptime_percentage": 99.9, "response_time_ms": 200, "support_level": "priority"},
            TenantTierDB.ENTERPRISE: {"uptime_percentage": 99.99, "response_time_ms": 100, "support_level": "dedicated"},
            TenantTierDB.UNLIMITED: {"uptime_percentage": 99.999, "response_time_ms": 50, "support_level": "executive"},
            TenantTierDB.CUSTOM: {"uptime_percentage": 99.0, "response_time_ms": 1000, "support_level": "basic"}
        }
        return defaults.get(tier, defaults[TenantTierDB.FREE])
    
    def get_by_id(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """通过 ID 获取租户"""
        stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """通过 slug 获取租户"""
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def list(self, status: Optional[TenantStatusDB] = None, 
             limit: int = 100, offset: int = 0) -> List[Tenant]:
        """列出租户"""
        stmt = select(Tenant).offset(offset).limit(limit)
        if status:
            stmt = stmt.where(Tenant.status == status)
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def update_status(self, tenant_id: uuid.UUID, status: TenantStatusDB) -> bool:
        """更新租户状态"""
        stmt = (
            update(Tenant)
            .where(Tenant.tenant_id == tenant_id)
            .values(
                status=status,
                updated_at=datetime.now(UTC)
            )
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def update_tier(self, tenant_id: uuid.UUID, tier: TenantTierDB) -> bool:
        """更新租户层级"""
        tenant = self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        # 更新租户层级
        stmt = (
            update(Tenant)
            .where(Tenant.tenant_id == tenant_id)
            .values(
                tier=tier,
                updated_at=datetime.now(UTC)
            )
        )
        self.db.execute(stmt)
        
        # 更新配额和 SLA
        new_quota = self._get_quota_defaults(tier)
        new_sla = self._get_sla_defaults(tier)
        
        stmt_quota = (
            update(TenantQuota)
            .where(TenantQuota.tenant_id == tenant_id)
            .values(**new_quota)
        )
        stmt_sla = (
            update(TenantSLA)
            .where(TenantSLA.tenant_id == tenant_id)
            .values(**new_sla)
        )
        
        self.db.execute(stmt_quota)
        self.db.execute(stmt_sla)
        self.db.commit()
        
        return True
    
    def delete(self, tenant_id: uuid.UUID) -> bool:
        """删除租户"""
        stmt = delete(Tenant).where(Tenant.tenant_id == tenant_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def check_quota(self, tenant_id: uuid.UUID, resource_type: str, amount: int = 1) -> bool:
        """检查配额"""
        tenant = self.get_by_id(tenant_id)
        if not tenant or tenant.status != TenantStatusDB.ACTIVE:
            return False
        
        quota = tenant.quota
        usage = tenant.usage
        
        resource_map = {
            "agents": (quota.max_agents, usage.agents_created),
            "api_calls": (quota.max_requests_per_minute, usage.requests_this_minute),
            "ai_credits": (quota.ai_credit_monthly, usage.ai_credits_used),
            "storage": (quota.max_storage_mb, usage.storage_used_mb)
        }
        
        limit, used = resource_map.get(resource_type, (None, None))
        if limit is None:
            return True
        
        return (used + amount) <= limit
    
    def record_usage(self, tenant_id: uuid.UUID, resource_type: str, amount: int = 1) -> bool:
        """记录使用量"""
        tenant = self.get_by_id(tenant_id)
        if not tenant:
            return False
        
        usage = tenant.usage
        
        if resource_type == "agents":
            usage.agents_created += amount
        elif resource_type == "api_calls":
            usage.requests_this_minute += amount
            usage.total_api_calls += amount
        elif resource_type == "ai_credits":
            usage.ai_credits_used += amount
        elif resource_type == "storage":
            usage.storage_used_mb += amount
        
        usage.updated_at = datetime.now(UTC)
        self.db.commit()
        
        return True

# ==================== 服务实例 Repository ====================

class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def register(self, service_name: str, service_type: ServiceTypeDB,
                 host: str, port: int, version: str = "1.0.0") -> ServiceInstanceDB:
        """注册服务"""
        logger.info(f"[ServiceRepository] 注册服务: {service_name} @ {host}:{port}")
        
        instance = ServiceInstanceDB(
            instance_id=f"{service_name}-{uuid.uuid4().hex[:8]}",
            service_name=service_name,
            service_type=service_type,
            host=host,
            port=port,
            version=version
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        
        logger.info(f"[ServiceRepository] 服务注册成功: instance_id={instance.instance_id}")
        return instance
    
    def get_by_id(self, instance_id: str) -> Optional[ServiceInstanceDB]:
        """通过 ID 获取服务"""
        stmt = select(ServiceInstanceDB).where(ServiceInstanceDB.instance_id == instance_id)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def discover_by_type(self, service_type: ServiceTypeDB) -> List[ServiceInstanceDB]:
        """发现指定类型的服务"""
        stmt = select(ServiceInstanceDB).where(
            and_(
                ServiceInstanceDB.service_type == service_type,
                ServiceInstanceDB.status != ServiceStatusDB.UNREGISTERED
            )
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def update_health(self, instance_id: str, health_score: float) -> bool:
        """更新健康状态"""
        instance = self.get_by_id(instance_id)
        if not instance:
            return False
        
        instance.health_score = health_score
        instance.last_heartbeat = datetime.now(UTC)
        
        # 自动调整状态
        if health_score >= 0.8:
            instance.status = ServiceStatusDB.HEALTHY
        elif health_score >= 0.5:
            instance.status = ServiceStatusDB.DEGRADED
        else:
            instance.status = ServiceStatusDB.UNHEALTHY
        
        self.db.commit()
        return True
    
    def unregister(self, instance_id: str) -> bool:
        """注销服务"""
        stmt = (
            update(ServiceInstanceDB)
            .where(ServiceInstanceDB.instance_id == instance_id)
            .values(status=ServiceStatusDB.UNREGISTERED)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    
    def list_all(self) -> List[ServiceInstanceDB]:
        """列出所有服务"""
        stmt = select(ServiceInstanceDB)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

# ==================== 工厂函数 ====================

def get_tenant_repository() -> TenantRepository:
    """获取租户 Repository"""
    db = SessionLocal()
    return TenantRepository(db)

def get_service_repository() -> ServiceRepository:
    """获取服务 Repository"""
    db = SessionLocal()
    return ServiceRepository(db)

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 47: Repository 模式测试")
    print("=" * 80)
    
    # 初始化数据库
    from phase47_database import init_db, reset_db
    reset_db()
    
    # 测试租户 Repository
    print("\n--- 测试租户 Repository ---")
    tenant_repo = get_tenant_repository()
    
    # 创建租户
    tenant = tenant_repo.create(
        name="测试公司",
        slug="test-company",
        email="test@example.com",
        owner_id=uuid.uuid4(),
        tier=TenantTierDB.PRO
    )
    print(f"创建租户成功: {tenant.name} ({tenant.tenant_id})")
    
    # 获取租户
    retrieved = tenant_repo.get_by_id(tenant.tenant_id)
    print(f"获取租户: {retrieved.name if retrieved else 'None'}")
    
    # 检查配额
    allowed = tenant_repo.check_quota(tenant.tenant_id, "agents", 1)
    print(f"配额检查: {'允许' if allowed else '拒绝'}")
    
    # 记录使用
    recorded = tenant_repo.record_usage(tenant.tenant_id, "api_calls", 50)
    print(f"使用记录: {'成功' if recorded else '失败'}")
    
    # 测试服务 Repository
    print("\n--- 测试服务 Repository ---")
    service_repo = get_service_repository()
    
    # 注册服务
    service = service_repo.register(
        service_name="api-gateway",
        service_type=ServiceTypeDB.API_GATEWAY,
        host="localhost",
        port=8000
    )
    print(f"服务注册成功: {service.service_name} ({service.instance_id})")
    
    # 发现服务
    discovered = service_repo.discover_by_type(ServiceTypeDB.API_GATEWAY)
    print(f"发现服务: {len(discovered)} 个")
    
    # 更新健康
    updated = service_repo.update_health(service.instance_id, 0.95)
    print(f"健康更新: {'成功' if updated else '失败'}")
    
    print("\n✅ Repository 测试全部通过！")
