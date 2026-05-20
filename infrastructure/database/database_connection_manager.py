"""
第七层：基础设施层 - 数据库连接管理器
提供数据库连接的统一管理
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
import os

from .async_database_engine import AsyncDatabaseEngineFactory, get_database_url


class DatabaseConnectionManager:
    """数据库连接管理器类"""

    def __init__(self):
        self.engine = AsyncDatabaseEngineFactory.create_engine(
            database_url=get_database_url(),
            is_testing=True
        )
        self.session_maker = AsyncDatabaseEngineFactory.create_async_session_maker(self.engine)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.session_maker() as session:
            yield session

    async def initialize_database(self) -> None:
        """初始化数据库"""
        from domain_model.entities.task_entity import Base as TaskBase
        from domain_model.entities.memory_entity import Base as MemoryBase
        
        async with self.engine.begin() as conn:
            await conn.run_sync(TaskBase.metadata.create_all)
            await conn.run_sync(MemoryBase.metadata.create_all)

    async def shutdown(self) -> None:
        """关闭数据库连接"""
        await self.engine.dispose()

    @classmethod
    async def create_and_initialize(cls) -> "DatabaseConnectionManager":
        """创建并初始化连接管理器"""
        manager = cls()
        await manager.initialize_database()
        return manager
