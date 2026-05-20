"""
第五层：领域模型层 - 知识实体
定义知识的核心领域模型
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from domain_model.entities.task_entity import Base

class KnowledgeEntity(Base):
    """知识实体类 - 表示系统中的知识对象"""
    
    __tablename__ = "knowledge_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_identifier = Column(String(36), unique=True, index=True, nullable=False)
    knowledge_title = Column(String(255), nullable=False)
    knowledge_content = Column(Text, nullable=False)
    knowledge_category = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)
    confidence_level = Column(Integer, default=100)
    is_verified = Column(Boolean, default=False)
    source_reference = Column(String(500), nullable=True)
    usage_count = Column(Integer, default=0)
    effectiveness_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

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
        
        return {
            "knowledge_id": self.knowledge_identifier,
            "knowledge_title": self.knowledge_title,
            "knowledge_content": self.knowledge_content,
            "knowledge_category": self.knowledge_category,
            "tags": self.tags.split(",") if self.tags else [],
            "confidence_level": self.confidence_level,
            "is_verified": self.is_verified,
            "source_reference": self.source_reference,
            "usage_count": self.usage_count,
            "effectiveness_score": self.effectiveness_score,
            "created_at": created_at_val,
            "updated_at": updated_at_val,
        }

    def verify(self) -> None:
        """验证知识"""
        self.is_verified = True
        self.updated_at = datetime.now(timezone.utc)

    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def update_confidence(self, level: int) -> None:
        """更新置信度"""
        self.confidence_level = max(0, min(level, 100))
        self.updated_at = datetime.now(timezone.utc)
