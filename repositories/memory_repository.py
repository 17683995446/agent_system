"""
MemoryRepository - Memory Repository实现
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, delete, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.memory_model import MemoryModel
from repositories.base_repository import BaseRepository
from infrastructure.logging.logging_system import get_logger


class MemoryRepository(BaseRepository[MemoryModel]):
    """
    Memory Repository
    提供Memory相关的CRUD操作
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(MemoryModel, db_session)
        self.logger = get_logger("MemoryRepository")
    
    async def create(self, data: Dict[str, Any]) -> MemoryModel:
        """创建记忆"""
        try:
            memory = MemoryModel(**data)
            self.db.add(memory)
            await self.db.flush()
            await self.db.refresh(memory)
            
            self.logger.info(f"Memory created: {memory.id}")
            return memory
            
        except Exception as e:
            self.logger.error(f"Error creating memory: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[MemoryModel]:
        """通过ID获取记忆"""
        try:
            query = select(MemoryModel).where(MemoryModel.id == id)
            result = await self.db.execute(query)
            memory = result.scalar_one_or_none()
            
            if memory:
                memory.increment_access()
                await self.db.flush()
            
            return memory
            
        except Exception as e:
            self.logger.error(f"Error getting memory: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[MemoryModel]:
        """更新记忆"""
        try:
            data['updated_at'] = datetime.now(timezone.utc)
            query = update(MemoryModel).where(MemoryModel.id == id).values(**data)
            await self.db.execute(query)
            await self.db.flush()
            return await self.get_by_id(id)
            
        except Exception as e:
            self.logger.error(f"Error updating memory: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """删除记忆"""
        try:
            query = delete(MemoryModel).where(MemoryModel.id == id)
            result = await self.db.execute(query)
            await self.db.flush()
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting memory: {str(e)}")
            raise
    
    async def search(
        self,
        user_id: str,
        query_text: Optional[str] = None,
        memory_type: Optional[str] = None,
        min_importance: Optional[int] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MemoryModel]:
        """搜索记忆"""
        try:
            query = select(MemoryModel).where(
                and_(
                    MemoryModel.user_id == user_id,
                    MemoryModel.is_archived == False
                )
            )
            
            if query_text:
                query = query.where(
                    MemoryModel.content.ilike(f"%{query_text}%")
                )
            
            if memory_type:
                query = query.where(MemoryModel.memory_type == memory_type)
            
            if min_importance:
                query = query.where(MemoryModel.importance_score >= min_importance)
            
            query = query.order_by(
                MemoryModel.importance_score.desc(),
                MemoryModel.created_at.desc()
            ).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            self.logger.error(f"Error searching memories: {str(e)}")
            raise
    
    async def cleanup_expired(self, max_age_days: int = 30) -> int:
        """清理过期记忆"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            
            query = delete(MemoryModel).where(
                and_(
                    MemoryModel.created_at < cutoff_date,
                    MemoryModel.is_archived == True
                )
            )
            
            result = await self.db.execute(query)
            await self.db.flush()
            
            deleted_count = result.rowcount
            self.logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up memories: {str(e)}")
            raise
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计"""
        try:
            query = select(
                func.count(MemoryModel.id).label('total'),
                func.avg(MemoryModel.importance_score).label('avg_importance'),
                func.sum(MemoryModel.access_count).label('total_access')
            ).where(MemoryModel.user_id == user_id)
            
            result = await self.db.execute(query)
            stats = result.one()
            
            return {
                "total_memories": stats.total or 0,
                "avg_importance": float(stats.avg_importance or 0),
                "total_access": stats.total_access or 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            raise
