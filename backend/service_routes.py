"""
服务管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime, timezone

from backend.database import get_db, ServiceInstanceDB
from backend.schemas import ServiceInstance, ServiceInstanceCreate, ServiceStatus, ServiceType, MessageResponse

router = APIRouter(prefix="/api/services", tags=["服务管理"])

@router.get("", response_model=List[ServiceInstance])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceInstanceDB))
    services = result.scalars().all()
    
    return [
        ServiceInstance(
            instance_id=svc.instance_id,
            service_name=svc.service_name,
            service_type=ServiceType(svc.service_type),
            version=svc.version,
            host=svc.host,
            port=svc.port,
            status=ServiceStatus(svc.status),
            health_score=svc.health_score,
            load_factor=svc.load_factor,
            started_at=svc.started_at,
            last_heartbeat=svc.last_heartbeat
        )
        for svc in services
    ]

@router.post("/register", response_model=ServiceInstance, status_code=status.HTTP_201_CREATED)
async def register_service(service_in: ServiceInstanceCreate, db: AsyncSession = Depends(get_db)):
    instance_id = f"{service_in.service_name}-{uuid.uuid4().hex[:8]}"
    
    now = datetime.now(timezone.utc)
    service_db = ServiceInstanceDB(
        instance_id=instance_id,
        service_name=service_in.service_name,
        service_type=service_in.service_type.value,
        version=service_in.version,
        host=service_in.host,
        port=service_in.port,
        status=ServiceStatus.HEALTHY.value,
        health_score=1.0,
        load_factor=0.0,
        started_at=now,
        last_heartbeat=now
    )
    
    db.add(service_db)
    await db.commit()
    await db.refresh(service_db)
    
    return ServiceInstance(
        instance_id=service_db.instance_id,
        service_name=service_db.service_name,
        service_type=ServiceType(service_db.service_type),
        version=service_db.version,
        host=service_db.host,
        port=service_db.port,
        status=ServiceStatus(service_db.status),
        health_score=service_db.health_score,
        load_factor=service_db.load_factor,
        started_at=service_db.started_at,
        last_heartbeat=service_db.last_heartbeat
    )

@router.get("/{instance_id}", response_model=ServiceInstance)
async def get_service(instance_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceInstanceDB).where(ServiceInstanceDB.instance_id == instance_id))
    service_db = result.scalar_one_or_none()
    
    if not service_db:
        raise HTTPException(status_code=404, detail="服务实例不存在")
    
    return ServiceInstance(
        instance_id=service_db.instance_id,
        service_name=service_db.service_name,
        service_type=ServiceType(service_db.service_type),
        version=service_db.version,
        host=service_db.host,
        port=service_db.port,
        status=ServiceStatus(service_db.status),
        health_score=service_db.health_score,
        load_factor=service_db.load_factor,
        started_at=service_db.started_at,
        last_heartbeat=service_db.last_heartbeat
    )

@router.put("/{instance_id}/heartbeat", response_model=ServiceInstance)
async def update_heartbeat(instance_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceInstanceDB).where(ServiceInstanceDB.instance_id == instance_id))
    service_db = result.scalar_one_or_none()
    
    if not service_db:
        raise HTTPException(status_code=404, detail="服务实例不存在")
    
    service_db.last_heartbeat = datetime.now(timezone.utc)
    service_db.status = ServiceStatus.HEALTHY.value
    await db.commit()
    await db.refresh(service_db)
    
    return ServiceInstance(
        instance_id=service_db.instance_id,
        service_name=service_db.service_name,
        service_type=ServiceType(service_db.service_type),
        version=service_db.version,
        host=service_db.host,
        port=service_db.port,
        status=ServiceStatus(service_db.status),
        health_score=service_db.health_score,
        load_factor=service_db.load_factor,
        started_at=service_db.started_at,
        last_heartbeat=service_db.last_heartbeat
    )

@router.delete("/{instance_id}", response_model=MessageResponse)
async def unregister_service(instance_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceInstanceDB).where(ServiceInstanceDB.instance_id == instance_id))
    service_db = result.scalar_one_or_none()
    
    if not service_db:
        raise HTTPException(status_code=404, detail="服务实例不存在")
    
    await db.delete(service_db)
    await db.commit()
    
    return MessageResponse(message="服务已注销")
