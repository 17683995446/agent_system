"""
数据库配置 - PostgreSQL异步引擎
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from infrastructure.logging.logging_system import get_logger


Base = declarative_base()


class DatabaseConfig:
    """数据库配置"""
    
    def __init__(
        self,
        database_url: str = "postgresql+asyncpg://agent_user:agent_pass@localhost/agent_db",
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True
    ):
        self.logger = get_logger("DatabaseConfig")
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        
        self._engine = None
        self._session_factory = None
        
    def create_engine(self):
        """创建数据库引擎"""
        self.logger.info(f"Creating database engine: {self.database_url}")
        
        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self.logger.info("Database engine created successfully")
        return self._engine
    
    def get_engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self.create_engine()
        return self._engine
    
    def get_session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            self.create_engine()
        return self._session_factory
    
    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if self._session_factory is None:
            self.create_engine()
        return self._session_factory()
    
    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self.logger.info("Database engine closed")
    
    async def create_tables(self):
        """创建所有表"""
        if self._engine is None:
            self.create_engine()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self.logger.info("All tables created successfully")
    
    async def drop_tables(self):
        """删除所有表"""
        if self._engine is None:
            self.create_engine()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        self.logger.warning("All tables dropped")


_db_config: Optional[DatabaseConfig] = None


def get_db_config() -> DatabaseConfig:
    """获取数据库配置单例"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


async def get_db_session() -> AsyncSession:
    """获取数据库会话的依赖注入"""
    config = get_db_config()
    async with config.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
