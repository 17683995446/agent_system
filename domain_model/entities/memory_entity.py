"""
第五层：领域模型层 - 记忆实体
定义记忆的核心领域模型
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Boolean

from domain_model.entities.task_entity import Base
from domain_model.enums.enums import MemoryTypeEnum

class MemoryEntity(Base):
    """记忆实体类 - 表示系统中的记忆对象"""
    
    __tablename__ = "memories_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_identifier = Column(String(36), unique=True, index=True, nullable=False)
    memory_content = Column(Text, nullable=False)
    memory_type = Column(SQLEnum(MemoryTypeEnum), default=MemoryTypeEnum.EXPERIENCE, nullable=False)
    importance_score = Column(Integer, default=0)
    is_hot_memory = Column(Boolean, default=False)
    related_task_id = Column(String(36), nullable=True)
    source_reference = Column(String(500), nullable=True)
    tags = Column(String(500), nullable=True)
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    accessed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        created_at_val = self.created_at
        if created_at_val and hasattr(created_at_val, 'isoformat'):
            created_at_val = created_at_val.isoformat()
        elif created_at_val is None:
            created_at_val = datetime.now(timezone.utc).isoformat()
        
        updated_at_val = self.updated_at
        if updated_at_val and hasattr(updated_at_val, 'isoformat'):
            updated_at_val = updated_at_val.isoformat()
        elif updated_at_val is None:
            updated_at_val = datetime.now(timezone.utc).isoformat()
        
        accessed_at_val = None
        if self.accessed_at and hasattr(self.accessed_at, 'isoformat'):
            accessed_at_val = self.accessed_at.isoformat()
        
        return {
            "memory_id": self.memory_identifier,
            "memory_content": self.memory_content,
            "memory_type": self.memory_type.value if hasattr(self.memory_type, "value") else str(self.memory_type),
            "importance_score": self.importance_score,
            "is_hot_memory": self.is_hot_memory,
            "related_task_id": self.related_task_id,
            "source_reference": self.source_reference,
            "tags": self.tags.split(",") if self.tags else [],
            "access_count": self.access_count,
            "created_at": created_at_val,
            "updated_at": updated_at_val,
            "accessed_at": accessed_at_val,
        }

    def mark_as_hot(self) -> None:
        """标记为热点记忆"""
        self.is_hot_memory = True
        self.importance_score = min(self.importance_score + 2, 10)
        self.updated_at = datetime.now(timezone.utc)

    def increment_access(self) -> None:
        """增加访问次数"""
        self.access_count += 1
        self.accessed_at = datetime.now(timezone.utc)

    def update_importance(self, score: int) -> None:
        """更新重要性分数"""
        self.importance_score = max(0, min(score, 10))
        self.updated_at = datetime.now(timezone.utc)
