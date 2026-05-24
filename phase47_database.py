"""
Phase 47: 数据库模型与持久化层
实现完整的 SQLAlchemy ORM 数据模型和 Repository 模式
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, DateTime, Enum, ForeignKey, Text, UUID as SQLAlchemyUUID
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from datetime import datetime, UTC
from enum import Enum as PyEnum
import uuid

# ==================== 配置 ====================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./agent_evolution.db"
)

# 引擎配置
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()

# ==================== 枚举定义 ====================

class TenantStatusDB(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    ARCHIVED = "archived"

class TenantTierDB(PyEnum):
    STARTER = "starter"
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"
    CUSTOM = "custom"

class ServiceTypeDB(PyEnum):
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

class ServiceStatusDB(PyEnum):
    REGISTERED = "registered"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNREGISTERED = "unregistered"

# ==================== 租户表 ====================

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(SQLAlchemyUUID(as_uuid=True), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    owner_id = Column(SQLAlchemyUUID(as_uuid=True), nullable=False, index=True)
    status = Column(Enum(TenantStatusDB), default=TenantStatusDB.ACTIVE, nullable=False)
    tier = Column(Enum(TenantTierDB), default=TenantTierDB.FREE, nullable=False)
    is_isolated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关系
    quota = relationship("TenantQuota", uselist=False, back_populates="tenant", cascade="all, delete-orphan")
    sla = relationship("TenantSLA", uselist=False, back_populates="tenant", cascade="all, delete-orphan")
    branding = relationship("TenantBranding", uselist=False, back_populates="tenant", cascade="all, delete-orphan")
    usage = relationship("TenantUsage", uselist=False, back_populates="tenant", cascade="all, delete-orphan")

# ==================== 租户配额表 ====================

class TenantQuota(Base):
    __tablename__ = "tenant_quotas"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    max_agents = Column(Integer, default=10)
    max_storage_mb = Column(Float, default=1000.0)
    max_requests_per_minute = Column(Integer, default=1000)
    max_api_keys = Column(Integer, default=5)
    max_users = Column(Integer, default=10)
    ai_credit_monthly = Column(Float, default=1000.0)
    custom_limits = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    tenant = relationship("Tenant", back_populates="quota")

# ==================== 租户 SLA 表 ====================

class TenantSLA(Base):
    __tablename__ = "tenant_slas"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    uptime_percentage = Column(Float, default=99.0)
    response_time_ms = Column(Integer, default=1000)
    support_level = Column(String(50), default="basic")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    tenant = relationship("Tenant", back_populates="sla")

# ==================== 租户品牌表 ====================

class TenantBranding(Base):
    __tablename__ = "tenant_brandings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    company_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), nullable=True)
    custom_domain = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    tenant = relationship("Tenant", back_populates="branding")

# ==================== 租户使用量表 ====================

class TenantUsage(Base):
    __tablename__ = "tenant_usages"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False, unique=True)
    
    agents_created = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0.0)
    requests_this_minute = Column(Integer, default=0)
    ai_credits_used = Column(Float, default=0.0)
    total_api_calls = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    tenant = relationship("Tenant", back_populates="usage")

# ==================== 服务实例表 ====================

class ServiceInstanceDB(Base):
    __tablename__ = "service_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(100), unique=True, nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    service_type = Column(Enum(ServiceTypeDB), nullable=False, index=True)
    version = Column(String(50), default="1.0.0")
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    status = Column(Enum(ServiceStatusDB), default=ServiceStatusDB.REGISTERED)
    health_score = Column(Float, default=0.0)
    instance_metadata = Column(Text, nullable=True)
    
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_heartbeat = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

# ==================== 初始化函数 ====================

def init_db():
    """初始化数据库 - 创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")

def get_db():
    """获取数据库 Session（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_db():
    """重置数据库 - 用于测试"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库已重置")

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 47: 数据库初始化")
    print("=" * 80)
    init_db()
    print("\n数据库地址:", DATABASE_URL)
    print("\n已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
