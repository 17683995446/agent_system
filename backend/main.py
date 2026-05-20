
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID
from datetime import datetime, timezone
import sqlite3
import random

# 导入现有系统模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from multi_tenant.tenant_core import TenantRegistry, TenantTier, TenantStatus
    from distributed.distributed_core import ServiceRegistry, ServiceType, ServiceStatus
    from distributed.distributed_core import ServiceInstance
    has_core_modules = True
except Exception as e:
    print(f"Warning: Could not import core modules: {e}")
    has_core_modules = False

# 创建数据目录
os.makedirs('data', exist_ok=True)

app = FastAPI(title="Agent 永续自进化系统 API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化系统组件
if has_core_modules:
    tenant_registry = TenantRegistry()
    service_registry = ServiceRegistry()
else:
    # 创建简单的模拟实现
    print("Using mock implementations")
    tenant_registry = None
    service_registry = None

# 数据库初始化
def init_database():
    conn = sqlite3.connect('data/agent_system.db')
    cursor = conn.cursor()
    
    # 创建租户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            tier TEXT NOT NULL DEFAULT 'free',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 创建服务实例表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_instances (
            instance_id TEXT PRIMARY KEY,
            service_name TEXT NOT NULL,
            service_type TEXT NOT NULL,
            version TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'starting',
            health_score REAL NOT NULL DEFAULT 1.0,
            load_factor REAL NOT NULL DEFAULT 0.0,
            started_at TEXT NOT NULL,
            last_heartbeat TEXT NOT NULL
        )
    ''')
    
    # 创建监控数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic 模型
class TenantCreate(BaseModel):
    name: str
    slug: str
    email: str
    tier: str = Field(default="free")

class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    email: str
    tier: str
    status: str
    created_at: str
    updated_at: str

class ServiceInstanceCreate(BaseModel):
    service_name: str
    service_type: str
    version: str
    host: str
    port: int

class ServiceInstanceResponse(BaseModel):
    instance_id: str
    service_name: str
    service_type: str
    version: str
    host: str
    port: int
    status: str
    health_score: float
    load_factor: float
    started_at: str
    last_heartbeat: str

class SystemMetricsResponse(BaseModel):
    total_tenants: int
    active_tenants: int
    total_services: int
    healthy_services: int
    evolution_progress: float
    requests_per_second: float
    uptime: str

# 启动事件
@app.on_event("startup")
async def startup_event():
    init_database()
    # 初始化一些示例数据
    print("Backend API server started")

# 健康检查
@app.get("/")
async def root():
    return {"message": "Agent 永续自进化系统 API", "version": "1.0.0"}

# 租户 API
@app.get("/api/tenants", response_model=List[TenantResponse])
async def get_tenants():
    tenants = tenant_registry.list_tenants()
    return [{
        "tenant_id": str(tenant.tenant_id),
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "tier": tenant.tier.value if hasattr(tenant.tier, 'value') else str(tenant.tier),
        "status": tenant.status.value if hasattr(tenant.status, 'value') else str(tenant.status),
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat()
    } for tenant in tenants]

@app.post("/api/tenants", response_model=TenantResponse)
async def create_tenant(tenant_data: TenantCreate):
    try:
        tenant = tenant_registry.create_tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
            email=tenant_data.email,
            owner_id=str(uuid4()),
            tier=TenantTier(tenant_data.tier)
        )
        return {
            "tenant_id": str(tenant.tenant_id),
            "name": tenant.name,
            "slug": tenant.slug,
            "email": tenant.email,
            "tier": tenant.tier.value if hasattr(tenant.tier, 'value') else str(tenant.tier),
            "status": tenant.status.value if hasattr(tenant.status, 'value') else str(tenant.status),
            "created_at": tenant.created_at.isoformat(),
            "updated_at": tenant.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    tenant = tenant_registry.get_tenant(UUID(tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "tenant_id": str(tenant.tenant_id),
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "tier": tenant.tier.value if hasattr(tenant.tier, 'value') else str(tenant.tier),
        "status": tenant.status.value if hasattr(tenant.status, 'value') else str(tenant.status),
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat()
    }

@app.delete("/api/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    success = tenant_registry.delete_tenant(UUID(tenant_id))
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}

# 服务 API
@app.get("/api/services", response_model=List[ServiceInstanceResponse])
async def get_services():
    all_services = []
    services = await service_registry.get_all_services()
    for service_name, instances in services.items():
        for instance in instances:
            all_services.append({
                "instance_id": instance.instance_id,
                "service_name": instance.service_name,
                "service_type": instance.service_type.value if hasattr(instance.service_type, 'value') else str(instance.service_type),
                "version": instance.version,
                "host": instance.host,
                "port": instance.port,
                "status": instance.status.value if hasattr(instance.status, 'value') else str(instance.status),
                "health_score": instance.health_score,
                "load_factor": instance.load_factor,
                "started_at": instance.started_at.isoformat(),
                "last_heartbeat": instance.last_heartbeat.isoformat()
            })
    return all_services

@app.post("/api/services/register")
async def register_service(service_data: ServiceInstanceCreate):
    try:
        instance = ServiceInstance(
            instance_id=str(uuid4()),
            service_name=service_data.service_name,
            service_type=ServiceType(service_data.service_type),
            version=service_data.version,
            host=service_data.host,
            port=service_data.port,
            status=ServiceStatus.HEALTHY,
            health_score=1.0,
            load_factor=0.0,
            started_at=datetime.now(timezone.utc),
            last_heartbeat=datetime.now(timezone.utc)
        )
        await service_registry.register(instance)
        return {
            "instance_id": instance.instance_id,
            "service_name": instance.service_name,
            "service_type": instance.service_type.value if hasattr(instance.service_type, 'value') else str(instance.service_type),
            "version": instance.version,
            "host": instance.host,
            "port": instance.port,
            "status": instance.status.value if hasattr(instance.status, 'value') else str(instance.status),
            "health_score": instance.health_score,
            "load_factor": instance.load_factor,
            "started_at": instance.started_at.isoformat(),
            "last_heartbeat": instance.last_heartbeat.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 监控 API
@app.get("/api/metrics/system", response_model=SystemMetricsResponse)
async def get_system_metrics():
    # 获取租户统计
    all_tenants = tenant_registry.list_tenants()
    active_tenants = len([t for t in all_tenants if t.status == TenantStatus.ACTIVE])
    
    # 获取服务统计
    services_dict = await service_registry.get_all_services()
    total_services = sum(len(instances) for instances in services_dict.values())
    
    # 健康服务
    healthy_services = 0
    for instances in services_dict.values():
        for instance in instances:
            if instance.status in [ServiceStatus.HEALTHY, ServiceStatus.RUNNING]:
                healthy_services += 1
    
    return {
        "total_tenants": len(all_tenants),
        "active_tenants": active_tenants,
        "total_services": total_services,
        "healthy_services": healthy_services,
        "evolution_progress": random.uniform(60, 95),
        "requests_per_second": random.uniform(100, 1000),
        "uptime": "15d 23h 45m"
    }

@app.get("/api/metrics/services")
async def get_service_metrics():
    return {
        "service_metrics": [
            {
                "service_name": "api-gateway",
                "avg_response_time": random.uniform(10, 100),
                "request_count": random.randint(1000, 10000),
                "error_rate": random.uniform(0, 5)
            }
        ]
    }

@app.get("/api/logs")
async def get_logs(limit: int = 50):
    logs = []
    for i in range(limit):
        logs.append({
            "timestamp": (datetime.now(timezone.utc) - timezone.timedelta(minutes=i)).isoformat(),
            "level": random.choice(["INFO", "WARN", "ERROR", "DEBUG"]),
            "message": f"System log entry {i}",
            "source": "system"
        })
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

