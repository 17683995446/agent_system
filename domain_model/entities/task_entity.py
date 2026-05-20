"""
第五层：领域模型层 - 任务实体
定义任务的核心领域模型
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

from domain_model.enums.enums import TaskStatusEnum

Base = declarative_base()


class TaskEntity(Base):
    """任务实体类 - 表示系统中的任务对象"""
    
    __tablename__ = "tasks_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_identifier = Column(String(36), unique=True, index=True, nullable=False)
    task_content = Column(Text, nullable=False)
    task_status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING, nullable=False)
    task_priority = Column(Integer, default=0, index=True)
    task_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_duration_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)
    
    def __init__(self, **kwargs):
        """自定义初始化方法以确保默认值生效"""
        if 'title' in kwargs:
            kwargs['task_content'] = kwargs.pop('title')
        if 'task_status' not in kwargs:
            kwargs['task_status'] = TaskStatusEnum.PENDING
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.now(timezone.utc)
        if 'task_priority' not in kwargs:
            kwargs['task_priority'] = 0
        super().__init__(**kwargs)
    
    @property
    def title(self) -> str:
        """获取任务标题（task_content的别名）"""
        return self.task_content
    
    @title.setter
    def title(self, value: str):
        """设置任务标题"""
        self.task_content = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        status_value = self.task_status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        elif status_value is None:
            status_value = 'pending'
        else:
            status_value = str(status_value)
        
        created_at = self.created_at
        if created_at and hasattr(created_at, 'isoformat'):
            created_at = created_at.isoformat()
        elif created_at is None:
            created_at = datetime.now(timezone.utc).isoformat()
        
        updated_at = self.updated_at
        if updated_at and hasattr(updated_at, 'isoformat'):
            updated_at = updated_at.isoformat()
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc).isoformat()
        
        started_at = None
        if self.started_at and hasattr(self.started_at, 'isoformat'):
            started_at = self.started_at.isoformat()
        
        completed_at = None
        if self.completed_at and hasattr(self.completed_at, 'isoformat'):
            completed_at = self.completed_at.isoformat()
        
        return {
            "task_id": self.task_identifier,
            "task_content": self.task_content,
            "task_status": status_value,
            "task_priority": self.task_priority,
            "task_result": self.task_result,
            "error_message": self.error_message,
            "execution_duration_seconds": self.execution_duration_seconds,
            "started_at": started_at,
            "completed_at": completed_at,
            "created_at": created_at,
            "updated_at": updated_at,
            "created_by": self.created_by,
            "tags": self.tags.split(",") if self.tags else [],
            "metadata": self.metadata_json,
        }
    
    def mark_as_running(self) -> None:
        """标记为运行中"""
        self.task_status = TaskStatusEnum.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_completed(self, result: str = None, duration: int = None) -> None:
        """标记为完成"""
        self.task_status = TaskStatusEnum.COMPLETED
        self.task_result = result
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        if duration:
            self.execution_duration_seconds = duration
    
    def mark_as_failed(self, error_message: str) -> None:
        """标记为失败"""
        self.task_status = TaskStatusEnum.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        status_value = self.task_status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        elif status_value is None:
            status_value = 'pending'
        else:
            status_value = str(status_value).lower()
        return f"<TaskEntity(task_id='{self.task_identifier}', status='{status_value}')>"
