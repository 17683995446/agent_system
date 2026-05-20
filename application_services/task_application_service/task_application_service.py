"""
第三层：应用服务层 - 任务应用服务
处理任务的业务流程和用例实现
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from domain_logic.task_domain_logic import TaskDomainLogic
from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum
from data_access.repository_interfaces.i_task_repository import ITaskRepository
from data_access.repository_implementations.task_repository import TaskRepository


class TaskApplicationService:
    """任务应用服务类 - 处理任务的业务流程"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository: ITaskRepository = TaskRepository(session)
        self.domain_logic = TaskDomainLogic()

    async def create_task(
        self,
        task_content: str,
        task_priority: int = 0,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TaskEntity:
        """创建任务 - 业务用例"""
        if not self.domain_logic.validate_task_content(task_content):
            raise ValueError("无效的任务内容")
        
        if not self.domain_logic.validate_task_priority(task_priority):
            raise ValueError("无效的任务优先级")
        
        task = await self.repository.create_task(
            task_content=task_content,
            task_priority=task_priority,
            created_by=created_by,
            tags=tags
        )
        
        await self.session.commit()
        return task

    async def get_task(self, task_id: str) -> Optional[TaskEntity]:
        """获取任务"""
        return await self.repository.get_task_by_id(task_id)

    async def list_tasks(self, limit: int = 100, offset: int = 0) -> List[TaskEntity]:
        """列出任务"""
        return await self.repository.get_all_tasks(limit=limit, offset=offset)

    async def update_task_priority(self, task_id: str, task_priority: int) -> bool:
        """更新任务优先级"""
        if not self.domain_logic.validate_task_priority(task_priority):
            raise ValueError("无效的任务优先级")
        
        success = await self.repository.update_task(task_id, task_priority=task_priority)
        if success:
            await self.session.commit()
        return success

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        success = await self.repository.delete_task(task_id)
        if success:
            await self.session.commit()
        return success

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行任务 - 业务用例"""
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        
        if not self.domain_logic.can_transition_status(task.task_status, TaskStatusEnum.RUNNING):
            raise ValueError(f"任务状态不能从 {task.task_status} 转换为 RUNNING")
        
        await self.repository.update_task_status(task_id, TaskStatusEnum.RUNNING)
        
        try:
            await self._perform_task_execution(task)
            await self.repository.update_task_status(
                task_id,
                TaskStatusEnum.COMPLETED,
                task_result="任务执行成功"
            )
            await self.session.commit()
            return {"success": True, "task_id": task_id, "status": "completed"}
        except Exception as e:
            await self.repository.update_task_status(
                task_id,
                TaskStatusEnum.FAILED,
                error_message=str(e)
            )
            await self.session.commit()
            return {"success": False, "task_id": task_id, "error": str(e)}

    async def _perform_task_execution(self, task: TaskEntity) -> None:
        """执行具体任务逻辑"""
        import asyncio
        await asyncio.sleep(1)

    async def get_pending_tasks_count(self) -> int:
        """获取待执行任务数量"""
        return await self.repository.count_tasks_by_status(TaskStatusEnum.PENDING)

    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total = await self.repository.count_tasks()
        pending = await self.repository.count_tasks_by_status(TaskStatusEnum.PENDING)
        running = await self.repository.count_tasks_by_status(TaskStatusEnum.RUNNING)
        completed = await self.repository.count_tasks_by_status(TaskStatusEnum.COMPLETED)
        failed = await self.repository.count_tasks_by_status(TaskStatusEnum.FAILED)
        
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
        }
