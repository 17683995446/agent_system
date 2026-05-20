"""
第四层：领域逻辑层 - 任务领域逻辑
定义任务的核心业务规则和逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum, PriorityLevelEnum


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """确保datetime对象是时区感知的"""
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TaskDomainLogic:
    """任务领域逻辑类 - 封装任务的核心业务规则"""

    @staticmethod
    def validate_task_content(content: str) -> bool:
        """验证任务内容"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 10000:
            return False
        return True

    @staticmethod
    def validate_task_priority(priority: int) -> bool:
        """验证任务优先级"""
        return -10 <= priority <= 10

    @staticmethod
    def calculate_task_score(task: TaskEntity) -> int:
        """计算任务评分（优先级 + 等待时间）"""
        priority_score = task.task_priority * 10
        return priority_score

    @staticmethod
    def can_transition_status(current_status: TaskStatusEnum, new_status: TaskStatusEnum) -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            TaskStatusEnum.PENDING: [TaskStatusEnum.RUNNING, TaskStatusEnum.CANCELLED],
            TaskStatusEnum.RUNNING: [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED],
            TaskStatusEnum.COMPLETED: [],
            TaskStatusEnum.FAILED: [TaskStatusEnum.PENDING],
            TaskStatusEnum.CANCELLED: [TaskStatusEnum.PENDING],
        }
        return new_status in valid_transitions.get(current_status, [])

    @staticmethod
    def should_auto_cancel(task: TaskEntity, max_wait_seconds: int = 3600) -> bool:
        """判断任务是否应该自动取消"""
        if task.task_status != TaskStatusEnum.PENDING:
            return False
        
        if not task.created_at:
            return False
        
        created_at = ensure_timezone_aware(task.created_at)
        wait_time = (datetime.now(timezone.utc) - created_at).total_seconds()
        return wait_time > max_wait_seconds

    @staticmethod
    def get_priority_level(priority: int) -> PriorityLevelEnum:
        """获取优先级级别"""
        if priority >= 10:
            return PriorityLevelEnum.CRITICAL
        elif priority >= 7:
            return PriorityLevelEnum.HIGH
        elif priority >= 5:
            return PriorityLevelEnum.NORMAL
        elif priority >= 3:
            return PriorityLevelEnum.LOW
        else:
            return PriorityLevelEnum.MINIMAL

    @staticmethod
    def is_high_priority_task(task: TaskEntity) -> bool:
        """判断是否为高优先级任务"""
        return task.task_priority >= PriorityLevelEnum.HIGH.value

    @staticmethod
    def should_execute_immediately(task: TaskEntity) -> bool:
        """判断是否应该立即执行"""
        return TaskDomainLogic.is_high_priority_task(task) and task.task_status == TaskStatusEnum.PENDING
