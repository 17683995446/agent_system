"""
API 数据模型 - Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    ARCHIVED = "archived"

class TenantTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"

class ServiceStatus(str, Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DEGRADED = "degraded"

class ServiceType(str, Enum):
    API_GATEWAY = "api_gateway"
    AUTH_SERVICE = "auth_service"
    AGENT_SERVICE = "agent_service"
    MEMORY_SERVICE = "memory_service"
    EVOLUTION_SERVICE = "evolution_service"
    MONITORING_SERVICE = "monitoring_service"
    ANALYTICS_SERVICE = "analytics_service"
    AI_AGENT_SERVICE = "ai_agent_service"
    TASK_SERVICE = "task_service"

class TenantQuotaBase(BaseModel):
    max_agents: int = 10
    max_storage_mb: int = 1000
    max_requests_per_minute: int = 1000
    max_api_keys: int = 5
    max_users: int = 10
    max_workflows: int = 10
    ai_credit_monthly: int = 1000
    max_concurrent_jobs: int = 5

class TenantQuota(TenantQuotaBase):
    pass

class TenantBase(BaseModel):
    name: str = Field(..., description="租户名称")
    slug: str = Field(..., description="租户唯一标识")
    email: str = Field(..., description="租户管理员邮箱")
    tier: TenantTier = TenantTier.FREE

class TenantCreate(TenantBase):
    owner_id: str = Field(..., description="租户所有者ID")

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[TenantStatus] = None

class Tenant(TenantBase):
    id: str
    owner_id: str
    status: TenantStatus
    quota: TenantQuota
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ServiceInstanceBase(BaseModel):
    service_name: str
    service_type: ServiceType
    version: str
    host: str
    port: int

class ServiceInstanceCreate(ServiceInstanceBase):
    pass

class ServiceInstance(ServiceInstanceBase):
    instance_id: str
    status: ServiceStatus
    health_score: float
    load_factor: float
    started_at: datetime
    last_heartbeat: datetime

    class Config:
        from_attributes = True

class SystemMetrics(BaseModel):
    total_tenants: int
    active_tenants: int
    total_services: int
    healthy_services: int
    evolution_progress: float
    requests_per_second: float
    uptime: str

class LogEntry(BaseModel):
    log_id: str
    level: str
    message: str
    source: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime

class TenantTierUpdate(BaseModel):
    tier: TenantTier

class MessageResponse(BaseModel):
    message: str
