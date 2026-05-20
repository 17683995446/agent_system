"""
第五层：领域模型层 - 策略实体
定义策略的核心领域模型
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from domain_model.entities.task_entity import Base

class StrategyEntity(Base):
    """策略实体类 - 表示系统中的策略对象"""
    
    __tablename__ = "strategies_table"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_identifier = Column(String(36), unique=True, index=True, nullable=False)
    strategy_name = Column(String(255), nullable=False)
    strategy_description = Column(Text, nullable=True)
    strategy_content = Column(Text, nullable=False)
    strategy_category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    effectiveness_score = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)
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
            "strategy_id": self.strategy_identifier,
            "strategy_name": self.strategy_name,
            "strategy_description": self.strategy_description,
            "strategy_content": self.strategy_content,
            "strategy_category": self.strategy_category,
            "is_active": self.is_active,
            "effectiveness_score": self.effectiveness_score,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": created_at_val,
            "updated_at": updated_at_val,
        }

    def activate(self) -> None:
        """激活策略"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """停用策略"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_effectiveness(self, score: int) -> None:
        """更新有效性分数"""
        self.effectiveness_score = max(0, min(score, 100))
        self.updated_at = datetime.now(timezone.utc)

    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1
        self.updated_at = datetime.now(timezone.utc)
