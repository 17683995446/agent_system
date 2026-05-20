"""
数据模型 - Memory记忆模型
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Index, Float
from sqlalchemy.orm import relationship

from infrastructure.database.async_database_config import Base


class MemoryModel(Base):
    """
    Memory记忆数据模型
    存储Agent的经验、知识和记忆
    """
    __tablename__ = "memories"

    id = Column(String(100), primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    memory_type = Column(String(30), nullable=False, default="experience", index=True)
    importance_score = Column(Integer, nullable=False, default=5)
    
    tags = Column(JSON, default=list, nullable=False)
    extra_metadata = Column(JSON, default=dict, nullable=False)
    
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    embedding_vector = Column(JSON, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("UserModel", back_populates="memories")
    
    agent_id = Column(String(100), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    agent = relationship("AgentModel", back_populates="memories")
    
    __table_args__ = (
        Index('idx_memories_user_importance', 'user_id', 'importance_score'),
        Index('idx_memories_user_type', 'user_id', 'memory_type'),
        Index('idx_memories_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<MemoryModel(id={self.id}, type={self.memory_type}, importance={self.importance_score})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance_score": self.importance_score,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_pinned": self.is_pinned,
            "is_archived": self.is_archived,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "user_id": self.user_id,
            "agent_id": self.agent_id
        }
    
    def to_search_result(self) -> dict:
        """转换为搜索结果"""
        return {
            "id": self.id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "memory_type": self.memory_type,
            "importance_score": self.importance_score,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "similarity": self.semantic_similarity
        }
    
    def increment_access(self):
        """增加访问计数"""
        self.access_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
