"""
第六层：数据访问层 - 任务仓储实现
任务数据访问的具体实现
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum
from data_access.repository_interfaces.i_task_repository import ITaskRepository


class TaskRepository(ITaskRepository):
    """任务仓储实现类 - 具体的任务数据访问实现"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_task(
        self,
        task_content: str,
        task_priority: int = 0,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TaskEntity:
        """创建新任务"""
        task = TaskEntity(
            task_identifier=str(uuid.uuid4()),
            task_content=task_content,
            task_priority=task_priority,
            task_status=TaskStatusEnum.PENDING,
            created_by=created_by,
            tags=",".join(tags) if tags else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.session.add(task)
        await self.session.flush()
        
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[TaskEntity]:
        """根据ID获取任务"""
        stmt = select(TaskEntity).where(TaskEntity.task_identifier == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_tasks(self, limit: int = 100, offset: int = 0) -> List[TaskEntity]:
        """获取所有任务"""
        stmt = select(TaskEntity).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_task(
        self,
        task_id: str,
        task_content: Optional[str] = None,
        task_priority: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """更新任务"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False
        
        if task_content is not None:
            task.task_content = task_content
        if task_priority is not None:
            task.task_priority = task_priority
        if tags is not None:
            task.tags = ",".join(tags)
        
        task.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        
        return True
    
    async def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatusEnum,
        task_result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False
        
        task.task_status = new_status
        task.updated_at = datetime.now(timezone.utc)
        
        if task_result is not None:
            task.task_result = task_result
        if error_message is not None:
            task.error_message = error_message
        
        if new_status == TaskStatusEnum.COMPLETED or new_status == TaskStatusEnum.FAILED:
            task.completed_at = datetime.now(timezone.utc)
        
        await self.session.flush()
        
        return True
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False
        
        await self.session.delete(task)
        await self.session.flush()
        
        return True
    
    async def count_tasks(self) -> int:
        """统计任务总数"""
        stmt = select(func.count()).select_from(TaskEntity)
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def count_tasks_by_status(self, status: TaskStatusEnum) -> int:
        """根据状态统计任务数"""
        stmt = select(func.count()).select_from(TaskEntity).where(
            TaskEntity.task_status == status
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
