"""
第七层：基础设施层 - 异步数据库引擎模块
提供异步数据库引擎配置和工厂函数
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, StaticPool, NullPool
from typing import Optional
import os


class AsyncDatabaseEngineFactory:
    """异步数据库引擎工厂类"""
    
    @staticmethod
    def create_engine(
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        is_testing: bool = False
    ):
        """创建异步数据库引擎
        
        Args:
            database_url: 数据库连接URL
            echo: 是否打印SQL语句
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            pool_recycle: 连接回收时间（秒）
            pool_pre_ping: 连接前测试
            is_testing: 是否为测试模式
            
        Returns:
            异步数据库引擎实例
        """
        if is_testing:
            return create_async_engine(
                database_url,
                echo=echo,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
        
        return create_async_engine(
            database_url,
            echo=echo,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping
        )
    
    @staticmethod
    def create_async_session_maker(engine, expire_on_commit: bool = False):
        """创建异步会话制造器
        
        Args:
            engine: 异步数据库引擎
            expire_on_commit: 提交后是否使会话过期
            
        Returns:
            异步会话制造器
        """
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=expire_on_commit
        )


def get_database_url() -> str:
    """获取数据库连接URL"""
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agent_evolution.db")
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return database_url


async def get_async_session() -> AsyncSession:
    """获取异步会话的依赖注入函数"""
    # 避免循环导入，这个函数应该由应用层实现
    raise NotImplementedError("get_async_session should be implemented in application layer")


async def init_database():
    """初始化数据库"""
    from domain_model.entities.task_entity import Base as TaskBase
    from domain_model.entities.memory_entity import Base as MemoryBase
    from domain_model.entities.knowledge_entity import Base as KnowledgeBase
    from domain_model.entities.strategy_entity import Base as StrategyBase
    
    engine = AsyncDatabaseEngineFactory.create_engine(
        database_url=get_database_url(),
        is_testing=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(TaskBase.metadata.create_all)
        await conn.run_sync(MemoryBase.metadata.create_all)
        await conn.run_sync(KnowledgeBase.metadata.create_all)
        await conn.run_sync(StrategyBase.metadata.create_all)
    
    await engine.dispose()
