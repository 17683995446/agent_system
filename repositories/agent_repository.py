"""
AgentRepository - Agent Repository实现
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_model import AgentModel
from repositories.base_repository import BaseRepository
from infrastructure.logging.logging_system import get_logger


class AgentRepository(BaseRepository[AgentModel]):
    """
    Agent Repository
    提供Agent相关的CRUD操作
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(AgentModel, db_session)
        self.logger = get_logger("AgentRepository")
    
    async def create(self, data: Dict[str, Any]) -> AgentModel:
        """创建Agent"""
        try:
            agent = AgentModel(**data)
            self.db.add(agent)
            await self.db.flush()
            await self.db.refresh(agent)
            
            self.logger.info(f"Agent created: {agent.id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Error creating agent: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[AgentModel]:
        """通过ID获取Agent"""
        try:
            query = select(AgentModel).where(AgentModel.id == id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Error getting agent: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[AgentModel]:
        """更新Agent"""
        try:
            data['updated_at'] = datetime.now(timezone.utc)
            query = update(AgentModel).where(AgentModel.id == id).values(**data)
            await self.db.execute(query)
            await self.db.flush()
            return await self.get_by_id(id)
            
        except Exception as e:
            self.logger.error(f"Error updating agent: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """删除Agent"""
        try:
            query = delete(AgentModel).where(AgentModel.id == id)
            result = await self.db.execute(query)
            await self.db.flush()
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting agent: {str(e)}")
            raise
    
    async def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[AgentModel]:
        """列出用户的Agent"""
        try:
            query = select(AgentModel).where(AgentModel.user_id == user_id)
            
            if status:
                query = query.where(AgentModel.status == status)
            
            query = query.order_by(AgentModel.fitness_score.desc()).offset(skip).limit(limit)
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error(f"Error listing agents: {str(e)}")
            raise
    
    async def get_population_stats(self) -> Dict[str, Any]:
        """获取种群统计"""
        try:
            query = select(
                func.count(AgentModel.id).label('total'),
                func.avg(AgentModel.fitness_score).label('avg_fitness'),
                func.max(AgentModel.fitness_score).label('max_fitness'),
                func.min(AgentModel.fitness_score).label('min_fitness')
            )
            result = await self.db.execute(query)
            stats = result.one()
            
            return {
                "total_agents": stats.total or 0,
                "avg_fitness": float(stats.avg_fitness or 0),
                "max_fitness": float(stats.max_fitness or 0),
                "min_fitness": float(stats.min_fitness or 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            raise
    
    async def get_best_agent(self, user_id: str) -> Optional[AgentModel]:
        """获取最佳Agent"""
        try:
            query = select(AgentModel).where(
                AgentModel.user_id == user_id
            ).order_by(AgentModel.fitness_score.desc()).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Error getting best agent: {str(e)}")
            raise
