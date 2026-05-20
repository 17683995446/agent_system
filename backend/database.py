"""
数据库模块 - SQLite + SQLAlchemy 2.0
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, Text
from datetime import datetime, timezone
from typing import List, Optional
import uuid
import os

DATABASE_URL = "sqlite+aiosqlite:///./agent_system.db"

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class TenantDB(Base):
    __tablename__ = "tenants"
    
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", index=True)
    tier: Mapped[str] = mapped_column(String, nullable=False, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_isolated_database: Mapped[bool] = mapped_column(Boolean, default=False)
    
    quotas: Mapped[List["TenantQuotaDB"]] = relationship("TenantQuotaDB", back_populates="tenant", uselist=False, cascade="all, delete-orphan")

class TenantQuotaDB(Base):
    __tablename__ = "tenant_quotas"
    
    quota_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    max_agents: Mapped[int] = mapped_column(Integer, default=10)
    max_storage_mb: Mapped[int] = mapped_column(Integer, default=1000)
    max_requests_per_minute: Mapped[int] = mapped_column(Integer, default=1000)
    max_api_keys: Mapped[int] = mapped_column(Integer, default=5)
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_workflows: Mapped[int] = mapped_column(Integer, default=10)
    ai_credit_monthly: Mapped[int] = mapped_column(Integer, default=1000)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=5)
    
    tenant: Mapped["TenantDB"] = relationship("TenantDB", back_populates="quotas")

class ServiceInstanceDB(Base):
    __tablename__ = "service_instances"
    
    instance_id: Mapped[str] = mapped_column(String, primary_key=True)
    service_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="starting", index=True)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    load_factor: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemMetricDB(Base):
    __tablename__ = "system_metrics"
    
    metric_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class LogEntryDB(Base):
    __tablename__ = "logs"
    
    log_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
