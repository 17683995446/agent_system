"""
第六层：数据访问层 - 任务仓储接口
定义任务数据访问的标准方法
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum


class ITaskRepository(ABC):
    """任务仓储接口 - 定义任务数据访问的标准方法"""
    
    @abstractmethod
    async def create_task(
        self,
        task_content: str,
        task_priority: int = 0,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> TaskEntity:
        """创建任务"""
        pass
    
    @abstractmethod
    async def get_task_by_id(self, task_id: str) -> Optional[TaskEntity]:
        """根据ID获取任务"""
        pass
    
    @abstractmethod
    async def get_all_tasks(self, limit: int = 100, offset: int = 0) -> List[TaskEntity]:
        """获取所有任务"""
        pass
    
    @abstractmethod
    async def update_task(
        self,
        task_id: str,
        task_content: Optional[str] = None,
        task_priority: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """更新任务"""
        pass
    
    @abstractmethod
    async def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatusEnum,
        task_result: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        pass
    
    @abstractmethod
    async def count_tasks(self) -> int:
        """统计任务总数"""
        pass
    
    @abstractmethod
    async def count_tasks_by_status(self, status: TaskStatusEnum) -> int:
        """根据状态统计任务数"""
        pass
