"""
数据种子脚本
"""
import asyncio
import uuid
from datetime import datetime, timezone

from backend.database import async_session_maker, init_db, TenantDB, TenantQuotaDB, ServiceInstanceDB, LogEntryDB
from backend.schemas import TenantStatus, TenantTier, ServiceStatus, ServiceType

async def seed_data():
    await init_db()
    
    async with async_session_maker() as session:
        system_tenant_id = str(uuid.uuid4())
        system_tenant = TenantDB(
            tenant_id=system_tenant_id,
            name="System Tenant",
            slug="system",
            email="system@example.com",
            owner_id="00000000-0000-0000-0000-000000000000",
            status=TenantStatus.ACTIVE.value,
            tier=TenantTier.UNLIMITED.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_isolated_database=False
        )
        session.add(system_tenant)
        
        system_quota = TenantQuotaDB(
            quota_id=str(uuid.uuid4()),
            tenant_id=system_tenant_id,
            max_agents=99999,
            max_storage_mb=999999,
            max_requests_per_minute=999999,
            max_api_keys=999,
            max_users=9999,
            max_workflows=9999,
            ai_credit_monthly=999999,
            max_concurrent_jobs=9999
        )
        session.add(system_quota)
        
        tenants_data = [
            ("Acme Corp", "acme", "admin@acme.com", TenantTier.PRO),
            ("Tech Startup", "techstartup", "hello@techstartup.io", TenantTier.BASIC),
            ("Data Labs", "datalabs", "contact@datalabs.ai", TenantTier.ENTERPRISE),
            ("Dev Studio", "devstudio", "info@devstudio.dev", TenantTier.FREE)
        ]
        
        for name, slug, email, tier in tenants_data:
            tenant_id = str(uuid.uuid4())
            tenant = TenantDB(
                tenant_id=tenant_id,
                name=name,
                slug=slug,
                email=email,
                owner_id=str(uuid.uuid4()),
                status=TenantStatus.ACTIVE.value,
                tier=tier.value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.add(tenant)
            
            if tier == TenantTier.FREE:
                quota = TenantQuotaDB(
                    quota_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    max_agents=5,
                    max_storage_mb=500,
                    max_requests_per_minute=100,
                    max_api_keys=2,
                    max_users=2,
                    max_workflows=10,
                    ai_credit_monthly=100,
                    max_concurrent_jobs=5
                )
            elif tier == TenantTier.BASIC:
                quota = TenantQuotaDB(
                    quota_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    max_agents=20,
                    max_storage_mb=5000,
                    max_requests_per_minute=1000,
                    max_api_keys=5,
                    max_users=10,
                    max_workflows=10,
                    ai_credit_monthly=1000,
                    max_concurrent_jobs=5
                )
            elif tier == TenantTier.PRO:
                quota = TenantQuotaDB(
                    quota_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    max_agents=100,
                    max_storage_mb=50000,
                    max_requests_per_minute=5000,
                    max_api_keys=20,
                    max_users=50,
                    max_workflows=10,
                    ai_credit_monthly=10000,
                    max_concurrent_jobs=5
                )
            else:
                quota = TenantQuotaDB(
                    quota_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    max_agents=1000,
                    max_storage_mb=500000,
                    max_requests_per_minute=50000,
                    max_api_keys=100,
                    max_users=500,
                    max_workflows=10,
                    ai_credit_monthly=100000,
                    max_concurrent_jobs=5
                )
            session.add(quota)
        
        services_data = [
            ("api-gateway", ServiceType.API_GATEWAY, "1.0.0", "localhost", 8000),
            ("auth-service", ServiceType.AUTH_SERVICE, "1.2.0", "localhost", 8001),
            ("agent-service", ServiceType.AGENT_SERVICE, "2.1.0", "localhost", 8002),
            ("memory-service", ServiceType.MEMORY_SERVICE, "1.5.0", "localhost", 8003),
            ("evolution-service", ServiceType.EVOLUTION_SERVICE, "3.0.0", "localhost", 8004),
            ("monitoring-service", ServiceType.MONITORING_SERVICE, "1.1.0", "localhost", 8005),
            ("analytics-service", ServiceType.ANALYTICS_SERVICE, "1.3.0", "localhost", 8006)
        ]
        
        for name, service_type, version, host, port in services_data:
            service = ServiceInstanceDB(
                instance_id=f"{name}-{uuid.uuid4().hex[:8]}",
                service_name=name,
                service_type=service_type.value,
                version=version,
                host=host,
                port=port,
                status=ServiceStatus.HEALTHY.value,
                health_score=1.0,
                load_factor=0.0,
                started_at=datetime.now(timezone.utc),
                last_heartbeat=datetime.now(timezone.utc)
            )
            session.add(service)
        
        logs_data = [
            ("INFO", "系统启动成功", "system"),
            ("INFO", "数据库连接已建立", "database"),
            ("INFO", "服务注册中心已就绪", "service-registry"),
            ("DEBUG", "租户管理模块已加载", "tenant-module"),
            ("INFO", "AI 进化引擎初始化完成", "evolution-engine")
        ]
        
        for level, message, source in logs_data:
            log = LogEntryDB(
                log_id=str(uuid.uuid4()),
                level=level,
                message=message,
                source=source,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(log)
        
        await session.commit()
        print("数据种子已成功加载！")

if __name__ == "__main__":
    asyncio.run(seed_data())
