"""
数据模型 - Agent智能体模型
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from infrastructure.database.async_database_config import Base


class AgentModel(Base):
    """
    Agent智能体数据模型
    存储Agent的基因组、适应度分数和进化状态
    """
    __tablename__ = "agents"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    status = Column(String(20), nullable=False, default="idle", index=True)
    state = Column(String(20), nullable=False, default="idle")
    
    genome_data = Column(JSON, nullable=False, default=dict)
    fitness_score = Column(Float, default=0.0, nullable=False, index=True)
    
    generation = Column(Integer, default=0, nullable=False)
    population_rank = Column(Integer, default=0, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_evolving = Column(Boolean, default=False, nullable=False)
    
    extra_metadata = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    last_evolution_at = Column(DateTime(timezone=True), nullable=True)
    
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("UserModel", back_populates="agents")
    
    __table_args__ = (
        Index('idx_agents_user_fitness', 'user_id', 'fitness_score'),
        Index('idx_agents_status_generation', 'status', 'generation'),
    )
    
    def __repr__(self):
        return f"<AgentModel(id={self.id}, name={self.name}, status={self.status}, fitness={self.fitness_score})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "state": self.state,
            "genome_data": self.genome_data,
            "fitness_score": self.fitness_score,
            "generation": self.generation,
            "population_rank": self.population_rank,
            "is_active": self.is_active,
            "is_evolving": self.is_evolving,
            "performance_metrics": self.performance_metrics,
            "evolution_history": self.evolution_history,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_evolution_at": self.last_evolution_at.isoformat() if self.last_evolution_at else None,
            "user_id": self.user_id
        }
    
    def to_summary_dict(self) -> dict:
        """转换为摘要字典"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "fitness_score": self.fitness_score,
            "generation": self.generation,
            "is_active": self.is_active,
            "is_evolving": self.is_evolving
        }
    
    def update_fitness(self, new_fitness: float):
        """更新适应度分数"""
        self.fitness_score = new_fitness
        self.last_evolution_at = datetime.now(timezone.utc)
        self.generation += 1
    
    def add_evolution_record(self, record: Dict[str, Any]):
        """添加进化记录"""
        if not self.evolution_history:
            self.evolution_history = []
        
        self.evolution_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **record
        })
        
        if len(self.evolution_history) > 100:
            self.evolution_history = self.evolution_history[-100:]
