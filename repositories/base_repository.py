"""
基础Repository - 抽象基类和通用功能
Agent永续自进化系统 - 数据持久化层
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

from infrastructure.logging.logging_system import get_logger

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """
    基础Repository抽象类
    提供通用的CRUD操作
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        db_session: AsyncSession
    ):
        self.model = model
        self.db = db_session
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """创建记录"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """通过ID获取记录"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除记录"""
        pass
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        列出记录
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数限制
            filters: 过滤条件
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            记录列表
        """
        try:
            query = select(self.model)
            
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, (list, tuple)):
                            filter_conditions.append(getattr(self.model, key).in_(value))
                        else:
                            filter_conditions.append(getattr(self.model, key) == value)
                
                if filter_conditions:
                    query = query.where(and_(*filter_conditions))
            
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                if hasattr(self.model, 'created_at'):
                    query = query.order_by(self.model.created_at.desc())
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            self.logger.info(
                f"Listed {len(records)} records",
                model=self.model.__name__,
                skip=skip,
                limit=limit
            )
            
            return list(records)
            
        except Exception as e:
            self.logger.error(f"Error listing records: {str(e)}")
            raise
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        计数
        
        Args:
            filters: 过滤条件
            
        Returns:
            记录数量
        """
        try:
            query = select(func.count()).select_from(self.model)
            
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, (list, tuple)):
                            filter_conditions.append(getattr(self.model, key).in_(value))
                        else:
                            filter_conditions.append(getattr(self.model, key) == value)
                
                if filter_conditions:
                    query = query.where(and_(*filter_conditions))
            
            result = await self.db.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            self.logger.error(f"Error counting records: {str(e)}")
            raise
    
    async def exists(self, id: str) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            是否存在
        """
        try:
            query = select(func.count()).select_from(self.model).where(
                getattr(self.model, 'id') == id
            )
            
            result = await self.db.execute(query)
            count = result.scalar()
            
            return (count or 0) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking existence: {str(e)}")
            raise
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        批量创建
        
        Args:
            data_list: 数据列表
            
        Returns:
            创建的记录列表
        """
        try:
            records = []
            
            for data in data_list:
                record = self.model(**data)
                self.db.add(record)
                records.append(record)
            
            await self.db.flush()
            
            self.logger.info(
                f"Bulk created {len(records)} records",
                model=self.model.__name__
            )
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error bulk creating records: {str(e)}")
            raise
    
    async def bulk_delete(self, ids: List[str]) -> int:
        """
        批量删除
        
        Args:
            ids: ID列表
            
        Returns:
            删除的记录数量
        """
        try:
            query = delete(self.model).where(
                getattr(self.model, 'id').in_(ids)
            )
            
            result = await self.db.execute(query)
            
            self.logger.info(
                f"Bulk deleted {result.rowcount} records",
                model=self.model.__name__
            )
            
            return result.rowcount
            
        except Exception as e:
            self.logger.error(f"Error bulk deleting records: {str(e)}")
            raise
    
    async def find_one(
        self,
        filters: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        查找单条记录
        
        Args:
            filters: 过滤条件
            
        Returns:
            记录或None
        """
        try:
            query = select(self.model)
            
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
            
            query = query.limit(1)
            
            result = await self.db.execute(query)
            record = result.scalar_one_or_none()
            
            return record
            
        except Exception as e:
            self.logger.error(f"Error finding record: {str(e)}")
            raise
    
    async def find_many(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        查找多条记录
        
        Args:
            filters: 过滤条件
            skip: 跳过的记录数
            limit: 返回的记录数限制
            
        Returns:
            记录列表
        """
        try:
            query = select(self.model)
            
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
            
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            return list(records)
            
        except Exception as e:
            self.logger.error(f"Error finding records: {str(e)}")
            raise


class UserRepository(BaseRepository):
    """用户Repository"""
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """创建用户"""
        try:
            user = self.model(**data)
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            
            self.logger.info(f"User created: {user.id}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """通过ID获取用户"""
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Error getting user by id: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """更新用户"""
        try:
            data['updated_at'] = datetime.now(timezone.utc)
            
            query = update(self.model).where(self.model.id == id).values(**data)
            await self.db.execute(query)
            await self.db.flush()
            
            return await self.get_by_id(id)
            
        except Exception as e:
            self.logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """删除用户"""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.db.execute(query)
            await self.db.flush()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting user: {str(e)}")
            raise
