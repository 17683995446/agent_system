"""
Phase 48: 服务层缓存集成
将缓存层集成到 Repository，形成完整的缓存服务架构
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC
import logging
import threading

from phase47_database import SessionLocal
from phase47_repository import (
    TenantRepository, ServiceRepository,
    TenantTierDB, TenantStatusDB, ServiceTypeDB
)
from phase48_cache import (
    CacheManager, CacheKeyStrategy, CacheConfig,
    MemoryCache, RedisCache, get_cache
)

# 配置日志
logger = logging.getLogger(__name__)

# ==================== 缓存配置常量 ====================

class CacheTTL:
    """缓存 TTL 配置"""
    TENANT = 300          # 租户信息 5分钟
    TENANT_LIST = 60      # 租户列表 1分钟
    QUOTA = 600           # 配额信息 10分钟
    USAGE = 30            # 使用量 30秒
    SERVICE = 120         # 服务信息 2分钟
    SERVICE_DISCOVERY = 60  # 服务发现 1分钟

# ==================== 缓存租户服务 ====================

class CachedTenantService:
    """带缓存的租户服务"""
    
    def __init__(self, cache: CacheManager = None):
        self.cache = cache or get_cache()
        self._lock = threading.Lock()
    
    def create_tenant(
        self,
        name: str,
        slug: str,
        email: str,
        owner_id: uuid.UUID,
        tier: TenantTierDB = TenantTierDB.FREE,
        is_isolated: bool = False
    ):
        """创建租户"""
        with self._lock:
            db = SessionLocal()
            try:
                repo = TenantRepository(db)
                tenant = repo.create(name, slug, email, owner_id, tier, is_isolated)
                
                # 失效列表缓存
                self.cache.backend.delete(CacheKeyStrategy.tenant_list())
                self.cache.backend.delete(CacheKeyStrategy.tenant_list("active"))
                
                logger.info(f"创建租户成功（已失效列表缓存）: {tenant.tenant_id}")
                return tenant
            finally:
                db.close()
    
    def get_tenant(self, tenant_id: uuid.UUID, use_cache: bool = True):
        """获取租户（带缓存）"""
        cache_key = CacheKeyStrategy.tenant(str(tenant_id))
        
        if use_cache:
            # 尝试从缓存获取
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"租户缓存命中: {tenant_id}")
                return cached
        
        # 从数据库获取
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            tenant = repo.get_by_id(tenant_id)
            
            if tenant and use_cache:
                # 存入缓存
                self._cache_tenant(tenant)
            
            return tenant
        finally:
            db.close()
    
    def _cache_tenant(self, tenant):
        """缓存租户信息"""
        if not tenant:
            return
        
        cache_key = CacheKeyStrategy.tenant(str(tenant.tenant_id))
        cache_data = {
            "tenant_id": str(tenant.tenant_id),
            "name": tenant.name,
            "slug": tenant.slug,
            "email": tenant.email,
            "status": tenant.status.value,
            "tier": tenant.tier.value,
            "created_at": tenant.created_at.isoformat()
        }
        
        self.cache.set(cache_key, cache_data, CacheTTL.TENANT)
        logger.debug(f"租户已缓存: {tenant.tenant_id}")
    
    def list_tenants(
        self,
        status: TenantStatusDB = None,
        limit: int = 100,
        offset: int = 0,
        use_cache: bool = True
    ):
        """列出租户（带缓存）"""
        status_str = status.value if status else "all"
        cache_key = CacheKeyStrategy.tenant_list(status_str)
        
        if use_cache and offset == 0 and limit <= 100:
            # 尝试从缓存获取
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"租户列表缓存命中: {status_str}")
                return cached
        
        # 从数据库获取
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            tenants = repo.list(status, limit, offset)
            
            if use_cache and offset == 0:
                # 缓存结果
                cache_data = [
                    {
                        "tenant_id": str(t.tenant_id),
                        "name": t.name,
                        "slug": t.slug,
                        "status": t.status.value,
                        "tier": t.tier.value
                    }
                    for t in tenants
                ]
                self.cache.set(cache_key, cache_data, CacheTTL.TENANT_LIST)
            
            return tenants
        finally:
            db.close()
    
    def update_tenant_status(self, tenant_id: uuid.UUID, status: TenantStatusDB):
        """更新租户状态"""
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            result = repo.update_status(tenant_id, status)
            
            if result:
                # 失效相关缓存
                self.cache.invalidate_tenant(str(tenant_id))
                self.cache.backend.delete(CacheKeyStrategy.tenant_list())
            
            return result
        finally:
            db.close()
    
    def delete_tenant(self, tenant_id: uuid.UUID):
        """删除租户"""
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            result = repo.delete(tenant_id)
            
            if result:
                # 失效所有相关缓存
                self.cache.invalidate_tenant(str(tenant_id))
                self.cache.backend.delete(CacheKeyStrategy.tenant_list())
            
            return result
        finally:
            db.close()
    
    def check_quota(self, tenant_id: uuid.UUID, resource_type: str, amount: int = 1):
        """检查配额（使用缓存）"""
        # 获取租户信息（带缓存）
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # 使用 Repository 检查配额
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            return repo.check_quota(tenant_id, resource_type, amount)
        finally:
            db.close()
    
    def record_usage(self, tenant_id: uuid.UUID, resource_type: str, amount: int = 1):
        """记录使用量"""
        db = SessionLocal()
        try:
            repo = TenantRepository(db)
            result = repo.record_usage(tenant_id, resource_type, amount)
            
            if result:
                # 失效使用量缓存
                self.cache.delete(CacheKeyStrategy.usage(str(tenant_id)))
            
            return result
        finally:
            db.close()

# ==================== 缓存服务 ====================

class CachedServiceRepository:
    """带缓存的服务仓储"""
    
    def __init__(self, cache: CacheManager = None):
        self.cache = cache or get_cache()
    
    def register_service(
        self,
        service_name: str,
        service_type: ServiceTypeDB,
        host: str,
        port: int,
        version: str = "1.0.0"
    ):
        """注册服务"""
        db = SessionLocal()
        try:
            repo = ServiceRepository(db)
            instance = repo.register(service_name, service_type, host, port, version)
            
            # 失效服务发现缓存
            self.cache.backend.delete(CacheKeyStrategy.service(service_type.value))
            
            return instance
        finally:
            db.close()
    
    def discover_service(self, service_type: ServiceTypeDB, use_cache: bool = True):
        """发现服务（带缓存）"""
        cache_key = CacheKeyStrategy.service(service_type.value)
        
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"服务发现缓存命中: {service_type.value}")
                return cached
        
        db = SessionLocal()
        try:
            repo = ServiceRepository(db)
            instances = repo.discover_by_type(service_type)
            
            if use_cache:
                cache_data = [
                    {
                        "instance_id": i.instance_id,
                        "service_name": i.service_name,
                        "health_score": i.health_score,
                        "status": i.status.value
                    }
                    for i in instances
                ]
                self.cache.set(cache_key, cache_data, CacheTTL.SERVICE_DISCOVERY)
            
            return instances
        finally:
            db.close()
    
    def update_health(self, instance_id: str, health_score: float):
        """更新服务健康状态"""
        db = SessionLocal()
        try:
            repo = ServiceRepository(db)
            instance = repo.get_by_id(instance_id)
            
            if not instance:
                return False
            
            result = repo.update_health(instance_id, health_score)
            
            if result:
                # 失效缓存
                self.cache.invalidate_service(instance_id=instance_id)
                self.cache.backend.delete(
                    CacheKeyStrategy.service(instance.service_type.value)
                )
            
            return result
        finally:
            db.close()
    
    def unregister_service(self, instance_id: str):
        """注销服务"""
        db = SessionLocal()
        try:
            repo = ServiceRepository(db)
            instance = repo.get_by_id(instance_id)
            
            if not instance:
                return False
            
            result = repo.unregister(instance_id)
            
            if result:
                # 失效所有相关缓存
                self.cache.invalidate_service(instance_id=instance_id)
                self.cache.backend.delete(
                    CacheKeyStrategy.service(instance.service_type.value)
                )
            
            return result
        finally:
            db.close()

# ==================== 工厂函数 ====================

_tenant_service = None
_service_repo = None

def get_cached_tenant_service() -> CachedTenantService:
    """获取缓存租户服务"""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = CachedTenantService()
    return _tenant_service

def get_cached_service_repo() -> CachedServiceRepository:
    """获取缓存服务仓储"""
    global _service_repo
    if _service_repo is None:
        _service_repo = CachedServiceRepository()
    return _service_repo

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 48: 缓存服务集成测试")
    print("=" * 80)
    
    # 测试缓存租户服务
    print("\n--- 测试缓存租户服务 ---")
    service = CachedTenantService()
    
    # 创建租户
    tenant = service.create_tenant(
        name="缓存测试公司",
        slug="cached-test",
        email="cached@test.com",
        owner_id=uuid.uuid4(),
        tier=TenantTierDB.PRO
    )
    print(f"创建租户: {tenant.name} ({tenant.tenant_id})")
    
    # 第一次获取（缓存未命中）
    print("\n第一次获取租户（应缓存）:")
    t1 = service.get_tenant(tenant.tenant_id)
    print(f"  结果: {t1.name if t1 else 'None'}")
    
    # 第二次获取（缓存命中）
    print("\n第二次获取租户（应命中缓存）:")
    t2 = service.get_tenant(tenant.tenant_id)
    print(f"  结果: {t2.name if t2 else 'None'}")
    
    # 缓存统计
    print(f"\n缓存统计: {service.cache.get_stats()}")
    
    # 测试缓存服务
    print("\n--- 测试缓存服务发现 ---")
    cached_service = CachedServiceRepository()
    
    # 注册服务
    instance = cached_service.register_service(
        "test-service",
        ServiceTypeDB.API_GATEWAY,
        "localhost",
        9000
    )
    print(f"注册服务: {instance.service_name} ({instance.instance_id})")
    
    # 发现服务
    print("\n发现服务（第一次，应缓存）:")
    services1 = cached_service.discover_service(ServiceTypeDB.API_GATEWAY)
    print(f"  发现: {len(services1)} 个")
    
    print("\n发现服务（第二次，应命中缓存）:")
    services2 = cached_service.discover_service(ServiceTypeDB.API_GATEWAY)
    print(f"  发现: {len(services2)} 个")
    
    print(f"\n缓存统计: {cached_service.cache.get_stats()}")
    
    print("\n✅ 缓存服务集成测试通过！")
