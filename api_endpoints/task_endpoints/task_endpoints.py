"""
第二层：API端点层 - 任务端点
处理任务相关的HTTP请求
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum
from data_access.repository_interfaces.i_task_repository import ITaskRepository
from data_access.repository_implementations.task_repository import TaskRepository
from application_services.task_application_service.task_application_service import TaskApplicationService
from api_gateway.request_validator import CreateTaskRequest, UpdateTaskRequest
from infrastructure.database.database_connection_manager import DatabaseConnectionManager

router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])


async def get_db_session():
    """获取数据库会话"""
    db_manager = DatabaseConnectionManager()
    async with db_manager.get_session() as session:
        yield session


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    request: CreateTaskRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """创建新任务"""
    try:
        service = TaskApplicationService(session=session)
        task = await service.create_task(
            task_content=request.task_content,
            task_priority=request.task_priority,
            created_by=request.created_by,
            tags=request.tags
        )
        return task.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{task_id}")
async def get_task_endpoint(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """获取指定任务"""
    try:
        service = TaskApplicationService(session=session)
        task = await service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/")
async def list_tasks_endpoint(
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session)
):
    """列出所有任务"""
    try:
        service = TaskApplicationService(session=session)
        tasks = await service.list_tasks(limit=limit, offset=offset)
        return [task.to_dict() for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{task_id}")
async def update_task_endpoint(
    task_id: str,
    request: UpdateTaskRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """更新任务"""
    try:
        service = TaskApplicationService(session=session)
        success = await service.update_task_priority(task_id, request.task_priority)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return {"success": True, "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{task_id}")
async def delete_task_endpoint(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """删除任务"""
    try:
        service = TaskApplicationService(session=session)
        success = await service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
        return {"success": True, "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{task_id}/execute")
async def execute_task_endpoint(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """执行任务"""
    try:
        service = TaskApplicationService(session=session)
        result = await service.execute_task(task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/statistics/summary")
async def get_task_statistics_endpoint(
    session: AsyncSession = Depends(get_db_session)
):
    """获取任务统计信息"""
    try:
        service = TaskApplicationService(session=session)
        stats = await service.get_task_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
