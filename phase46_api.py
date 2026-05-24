"""
Phase 46: FastAPI REST API 层
提供完整的租户管理和服务注册 REST 接口
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Set
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_tenant.tenant_core import (
    TenantRegistry, TenantStatus, TenantTier,
    TenantQuota, TenantSLA, TenantBranding,
    tenant_registry as global_tenant_registry
)
from distributed.distributed_core import (
    ServiceRegistry, LoadBalancer, ServiceInstance,
    ServiceStatus, ServiceType
)

# FastAPI 应用
app = FastAPI(
    title="Agent Evolution System API",
    description="企业级多租户管理系统 REST API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 请求/响应模型 ====================

class TenantTierEnum(str, Enum):
    STARTER = "starter"
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"
    CUSTOM = "custom"

class TenantStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    ARCHIVED = "archived"

class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    owner_id: UUID
    tier: TenantTierEnum = TenantTierEnum.FREE
    is_isolated: bool = False

class UpdateTenantStatusRequest(BaseModel):
    status: TenantStatusEnum

class UpdateTenantTierRequest(BaseModel):
    tier: TenantTierEnum

class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    status: str
    tier: str
    email: str
    owner_id: str
    created_at: str
    updated_at: str
    quota: dict
    sla: dict
    branding: dict
    usage: dict

class CheckQuotaRequest(BaseModel):
    resource_type: str
    amount: int = 1

class RecordUsageRequest(BaseModel):
    resource_type: str
    amount: int = 1

class ServiceTypeEnum(str, Enum):
    API_GATEWAY = "api_gateway"
    AUTH_SERVICE = "auth_service"
    AGENT_SERVICE = "agent_service"
    MEMORY_SERVICE = "memory_service"
    EVOLUTION_SERVICE = "evolution_service"
    MONITORING_SERVICE = "monitoring_service"
    ANALYTICS_SERVICE = "analytics_service"
    AI_AGENT_SERVICE = "ai_agent_service"
    TASK_SERVICE = "task_service"
    NOTIFICATION_SERVICE = "notification_service"
    USER_MANAGEMENT = "user_management"
    TASK_EXECUTOR = "task_executor"
    MEMORY_MANAGER = "memory_manager"
    PROXY = "proxy"
    LOGGING = "logging"
    MONITORING = "monitoring"
    CACHE = "cache"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    EVENT_BUS = "event_bus"

class RegisterServiceRequest(BaseModel):
    service_name: str
    service_type: ServiceTypeEnum
    host: str
    port: int

class UpdateHealthRequest(BaseModel):
    health_score: float = Field(..., ge=0.0, le=1.0)

class ServiceInstanceResponse(BaseModel):
    instance_id: str
    service_name: str
    service_type: str
    version: str
    host: str
    port: int
    status: str
    health_score: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# ==================== 健康检查 ====================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# ==================== 租户管理 API ====================

@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED, tags=["Tenants"])
async def create_tenant(request: CreateTenantRequest):
    """创建新租户"""
    try:
        tier_map = {
            TenantTierEnum.STARTER: TenantTier.STARTER,
            TenantTierEnum.FREE: TenantTier.FREE,
            TenantTierEnum.BASIC: TenantTier.BASIC,
            TenantTierEnum.PRO: TenantTier.PRO,
            TenantTierEnum.ENTERPRISE: TenantTier.ENTERPRISE,
            TenantTierEnum.UNLIMITED: TenantTier.UNLIMITED,
            TenantTierEnum.CUSTOM: TenantTier.CUSTOM,
        }
        
        tenant = global_tenant_registry.create_tenant(
            name=request.name,
            slug=request.slug,
            email=request.email,
            owner_id=request.owner_id,
            tier=tier_map[request.tier],
            is_isolated=request.is_isolated
        )
        
        return _tenant_to_response(tenant)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/api/v1/tenants", response_model=List[TenantResponse], tags=["Tenants"])
async def list_tenants(
    status_filter: Optional[TenantStatusEnum] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """列出所有租户"""
    try:
        status_map = {
            TenantStatusEnum.ACTIVE: TenantStatus.ACTIVE,
            TenantStatusEnum.INACTIVE: TenantStatus.INACTIVE,
            TenantStatusEnum.SUSPENDED: TenantStatus.SUSPENDED,
            TenantStatusEnum.TRIAL: TenantStatus.TRIAL,
            TenantStatusEnum.ARCHIVED: TenantStatus.ARCHIVED,
        }
        
        status = status_map.get(status_filter) if status_filter else None
        tenants = global_tenant_registry.list_tenants(status, limit, offset)
        
        return [_tenant_to_response(t) for t in tenants]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse, tags=["Tenants"])
async def get_tenant(tenant_id: UUID):
    """获取租户详情"""
    tenant = global_tenant_registry.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return _tenant_to_response(tenant)

@app.put("/api/v1/tenants/{tenant_id}/status", response_model=dict, tags=["Tenants"])
async def update_tenant_status(tenant_id: UUID, request: UpdateTenantStatusRequest):
    """更新租户状态"""
    status_map = {
        TenantStatusEnum.ACTIVE: TenantStatus.ACTIVE,
        TenantStatusEnum.INACTIVE: TenantStatus.INACTIVE,
        TenantStatusEnum.SUSPENDED: TenantStatus.SUSPENDED,
        TenantStatusEnum.TRIAL: TenantStatus.TRIAL,
        TenantStatusEnum.ARCHIVED: TenantStatus.ARCHIVED,
    }
    
    success = global_tenant_registry.update_tenant_status(tenant_id, status_map[request.status])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return {"message": "Status updated successfully", "tenant_id": str(tenant_id)}

@app.put("/api/v1/tenants/{tenant_id}/tier", response_model=dict, tags=["Tenants"])
async def update_tenant_tier(tenant_id: UUID, request: UpdateTenantTierRequest):
    """更新租户层级"""
    tier_map = {
        TenantTierEnum.STARTER: TenantTier.STARTER,
        TenantTierEnum.FREE: TenantTier.FREE,
        TenantTierEnum.BASIC: TenantTier.BASIC,
        TenantTierEnum.PRO: TenantTier.PRO,
        TenantTierEnum.ENTERPRISE: TenantTier.ENTERPRISE,
        TenantTierEnum.UNLIMITED: TenantTier.UNLIMITED,
        TenantTierEnum.CUSTOM: TenantTier.CUSTOM,
    }
    
    success = global_tenant_registry.update_tier(tenant_id, tier_map[request.tier])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return {"message": "Tier updated successfully", "tenant_id": str(tenant_id)}

@app.delete("/api/v1/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tenants"])
async def delete_tenant(tenant_id: UUID):
    """删除租户"""
    success = global_tenant_registry.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return None

# ==================== 配额与使用量 API ====================

@app.post("/api/v1/tenants/{tenant_id}/quota/check", response_model=dict, tags=["Quota"])
async def check_quota(tenant_id: UUID, request: CheckQuotaRequest):
    """检查配额"""
    result = global_tenant_registry.check_quota(tenant_id, request.resource_type, request.amount)
    return {
        "allowed": result,
        "tenant_id": str(tenant_id),
        "resource_type": request.resource_type,
        "amount": request.amount
    }

@app.post("/api/v1/tenants/{tenant_id}/usage", response_model=dict, tags=["Usage"])
async def record_usage(tenant_id: UUID, request: RecordUsageRequest):
    """记录使用量"""
    if request.amount < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be non-negative")
    
    success = global_tenant_registry.record_usage(tenant_id, request.resource_type, request.amount)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    return {
        "success": True,
        "tenant_id": str(tenant_id),
        "resource_type": request.resource_type,
        "amount": request.amount
    }

# ==================== 服务注册 API ====================

@app.post("/api/v1/services", response_model=ServiceInstanceResponse, status_code=status.HTTP_201_CREATED, tags=["Services"])
async def register_service(request: RegisterServiceRequest):
    """注册服务"""
    try:
        service_type_map = {
            ServiceTypeEnum.API_GATEWAY: ServiceType.API_GATEWAY,
            ServiceTypeEnum.AUTH_SERVICE: ServiceType.AUTH_SERVICE,
            ServiceTypeEnum.AGENT_SERVICE: ServiceType.AGENT_SERVICE,
            ServiceTypeEnum.MEMORY_SERVICE: ServiceType.MEMORY_SERVICE,
            ServiceTypeEnum.EVOLUTION_SERVICE: ServiceType.EVOLUTION_SERVICE,
            ServiceTypeEnum.MONITORING_SERVICE: ServiceType.MONITORING_SERVICE,
            ServiceTypeEnum.ANALYTICS_SERVICE: ServiceType.ANALYTICS_SERVICE,
            ServiceTypeEnum.AI_AGENT_SERVICE: ServiceType.AI_AGENT_SERVICE,
            ServiceTypeEnum.TASK_SERVICE: ServiceType.TASK_SERVICE,
            ServiceTypeEnum.NOTIFICATION_SERVICE: ServiceType.NOTIFICATION_SERVICE,
            ServiceTypeEnum.USER_MANAGEMENT: ServiceType.USER_MANAGEMENT,
            ServiceTypeEnum.TASK_EXECUTOR: ServiceType.TASK_EXECUTOR,
            ServiceTypeEnum.MEMORY_MANAGER: ServiceType.MEMORY_MANAGER,
            ServiceTypeEnum.PROXY: ServiceType.PROXY,
            ServiceTypeEnum.LOGGING: ServiceType.LOGGING,
            ServiceTypeEnum.MONITORING: ServiceType.MONITORING,
            ServiceTypeEnum.CACHE: ServiceType.CACHE,
            ServiceTypeEnum.DATABASE: ServiceType.DATABASE,
            ServiceTypeEnum.MESSAGE_QUEUE: ServiceType.MESSAGE_QUEUE,
            ServiceTypeEnum.EVENT_BUS: ServiceType.EVENT_BUS,
        }
        
        service_registry = ServiceRegistry()
        instance = service_registry.register_service(
            service_name=request.service_name,
            service_type=service_type_map[request.service_type],
            host=request.host,
            port=request.port
        )
        
        return _service_to_response(instance)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/api/v1/services", response_model=List[ServiceInstanceResponse], tags=["Services"])
async def list_services():
    """列出所有服务"""
    service_registry = ServiceRegistry()
    all_services = service_registry._instance_index
    return [_service_to_response(s) for s in all_services.values()]

@app.get("/api/v1/services/{service_type}", response_model=List[ServiceInstanceResponse], tags=["Services"])
async def discover_services(service_type: ServiceTypeEnum):
    """发现指定类型的服务"""
    service_type_map = {
        ServiceTypeEnum.API_GATEWAY: ServiceType.API_GATEWAY,
        ServiceTypeEnum.AUTH_SERVICE: ServiceType.AUTH_SERVICE,
        ServiceTypeEnum.AGENT_SERVICE: ServiceType.AGENT_SERVICE,
        ServiceTypeEnum.MEMORY_SERVICE: ServiceType.MEMORY_SERVICE,
        ServiceTypeEnum.EVOLUTION_SERVICE: ServiceType.EVOLUTION_SERVICE,
        ServiceTypeEnum.MONITORING_SERVICE: ServiceType.MONITORING_SERVICE,
        ServiceTypeEnum.ANALYTICS_SERVICE: ServiceType.ANALYTICS_SERVICE,
        ServiceTypeEnum.AI_AGENT_SERVICE: ServiceType.AI_AGENT_SERVICE,
        ServiceTypeEnum.TASK_SERVICE: ServiceType.TASK_SERVICE,
        ServiceTypeEnum.NOTIFICATION_SERVICE: ServiceType.NOTIFICATION_SERVICE,
        ServiceTypeEnum.USER_MANAGEMENT: ServiceType.USER_MANAGEMENT,
        ServiceTypeEnum.TASK_EXECUTOR: ServiceType.TASK_EXECUTOR,
        ServiceTypeEnum.MEMORY_MANAGER: ServiceType.MEMORY_MANAGER,
        ServiceTypeEnum.PROXY: ServiceType.PROXY,
        ServiceTypeEnum.LOGGING: ServiceType.LOGGING,
        ServiceTypeEnum.MONITORING: ServiceType.MONITORING,
        ServiceTypeEnum.CACHE: ServiceType.CACHE,
        ServiceTypeEnum.DATABASE: ServiceType.DATABASE,
        ServiceTypeEnum.MESSAGE_QUEUE: ServiceType.MESSAGE_QUEUE,
        ServiceTypeEnum.EVENT_BUS: ServiceType.EVENT_BUS,
    }
    
    service_registry = ServiceRegistry()
    instances = service_registry.discover_service(service_type_map[service_type])
    return [_service_to_response(i) for i in instances]

@app.put("/api/v1/services/{instance_id}/health", response_model=dict, tags=["Services"])
async def update_service_health(instance_id: str, request: UpdateHealthRequest):
    """更新服务健康状态"""
    service_registry = ServiceRegistry()
    success = service_registry.update_service_health(instance_id, request.health_score)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service instance not found")
    
    return {
        "success": True,
        "instance_id": instance_id,
        "health_score": request.health_score
    }

@app.delete("/api/v1/services/{instance_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Services"])
async def unregister_service(instance_id: str):
    """注销服务"""
    service_registry = ServiceRegistry()
    success = service_registry.unregister_service(instance_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service instance not found")
    
    return None

# ==================== 辅助函数 ====================

def _tenant_to_response(tenant) -> dict:
    """将租户对象转换为响应格式"""
    return {
        "tenant_id": str(tenant.tenant_id),
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status.value,
        "tier": tenant.tier.value,
        "email": tenant.email,
        "owner_id": str(tenant.owner_id),
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
        "quota": {
            "max_agents": tenant.quota.max_agents,
            "max_storage_mb": tenant.quota.max_storage_mb,
            "max_requests_per_minute": tenant.quota.max_requests_per_minute,
            "max_api_keys": tenant.quota.max_api_keys,
            "max_users": tenant.quota.max_users,
            "ai_credit_monthly": tenant.quota.ai_credit_monthly
        },
        "sla": {
            "uptime_percentage": tenant.sla.uptime_percentage,
            "response_time_ms": tenant.sla.response_time_ms,
            "support_level": tenant.sla.support_level
        },
        "branding": {
            "company_name": tenant.branding.company_name,
            "logo_url": tenant.branding.logo_url,
            "primary_color": tenant.branding.primary_color
        },
        "usage": {
            "agents_created": tenant.usage.agents_created,
            "storage_used_mb": tenant.usage.storage_used_mb,
            "requests_this_minute": tenant.usage.requests_this_minute,
            "ai_credits_used": tenant.usage.ai_credits_used,
            "total_api_calls": tenant.usage.total_api_calls
        }
    }

def _service_to_response(instance) -> dict:
    """将服务实例转换为响应格式"""
    return {
        "instance_id": instance.instance_id,
        "service_name": instance.service_name,
        "service_type": instance.service_type.name,
        "version": instance.version,
        "host": instance.host,
        "port": instance.port,
        "status": instance.status.name,
        "health_score": instance.health_score
    }

# ==================== 运行服务器 ====================

if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print("启动 Phase 46 REST API 服务器...")
    print("Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=8000)
