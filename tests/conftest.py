"""
Agent 永续自进化运行系统 - 测试配置文件
提供测试所需的fixtures和配置
"""
import pytest
import asyncio
from typing import Generator

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    SQLALCHEMY_AVAILABLE = True
    
    from domain_model.entities.task_entity import Base as TaskBase
except ImportError:
    SQLALCHEMY_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if SQLALCHEMY_AVAILABLE:
    @pytest.fixture(scope="function")
    async def async_engine():
        """创建异步数据库引擎fixture"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(TaskBase.metadata.create_all)
        
        yield engine
        
        await engine.dispose()
    
    
    @pytest.fixture(scope="function")
    async def async_session(async_engine) -> Generator[AsyncSession, None, None]:
        """创建异步数据库会话fixture"""
        async_session_maker = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            yield session
            await session.rollback()


@pytest.fixture
def sample_task_data() -> dict:
    """提供示例任务数据"""
    return {
        "task_content": "测试任务内容",
        "task_priority": 5,
        "created_by": "test_user",
        "tags": ["test", "unit"]
    }


@pytest.fixture
def sample_memory_data() -> dict:
    """提供示例记忆数据"""
    return {
        "memory_content": "测试记忆内容",
        "memory_type": "experience",
        "importance_score": 8,
        "created_by": "test_user"
    }


@pytest.fixture
def sample_knowledge_data() -> dict:
    """提供示例知识数据"""
    return {
        "knowledge_content": "测试知识内容",
        "knowledge_domain": "programming",
        "confidence_level": 9,
        "source_reference": "test_source"
    }


@pytest.fixture
def sample_strategy_data() -> dict:
    """提供示例策略数据"""
    return {
        "strategy_name": "测试策略",
        "strategy_description": "测试策略描述",
        "applicable_scenarios": ["test_scenario"],
        "effectiveness_score": 7
    }
