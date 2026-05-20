"""
监控指标 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import time
from datetime import datetime, timedelta, timezone

from backend.database import get_db, TenantDB, ServiceInstanceDB, LogEntryDB
from backend.schemas import SystemMetrics, LogEntry, ServiceStatus, TenantStatus

router = APIRouter(prefix="/api", tags=["监控分析"])

start_time = time.time()

def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if seconds > 0:
        parts.append(f"{seconds}秒")
    
    return " ".join(parts) if parts else "刚刚启动"

@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    tenant_result = await db.execute(select(func.count(TenantDB.tenant_id)))
    total_tenants = tenant_result.scalar() or 0
    
    active_tenant_result = await db.execute(
        select(func.count(TenantDB.tenant_id)).where(TenantDB.status == TenantStatus.ACTIVE.value)
    )
    active_tenants = active_tenant_result.scalar() or 0
    
    service_result = await db.execute(select(func.count(ServiceInstanceDB.instance_id)))
    total_services = service_result.scalar() or 0
    
    healthy_service_result = await db.execute(
        select(func.count(ServiceInstanceDB.instance_id)).where(
            ServiceInstanceDB.status.in_([ServiceStatus.HEALTHY.value, ServiceStatus.RUNNING.value])
        )
    )
    healthy_services = healthy_service_result.scalar() or 0
    
    return SystemMetrics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_services=total_services,
        healthy_services=healthy_services,
        evolution_progress=73.5,
        requests_per_second=124.5,
        uptime=get_uptime()
    )

@router.get("/metrics/services", response_model=dict)
async def get_service_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceInstanceDB))
    services = result.scalars().all()
    
    status_count = {}
    type_count = {}
    
    for svc in services:
        status = svc.status
        status_count[status] = status_count.get(status, 0) + 1
        
        service_type = svc.service_type
        type_count[service_type] = type_count.get(service_type, 0) + 1
    
    return {
        "total_services": len(services),
        "by_status": status_count,
        "by_type": type_count
    }

@router.get("/logs", response_model=List[LogEntry])
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LogEntryDB)
        .order_by(LogEntryDB.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        LogEntry(
            log_id=log.log_id,
            level=log.level,
            message=log.message,
            source=log.source,
            timestamp=log.timestamp
        )
        for log in logs
    ]
