"""
Agent Eternal Evolution System - 集成测试套件
测试多层架构间的交互和协作
"""
import pytest
from datetime import datetime

from application_services.task_application_service.task_application_service import TaskApplicationService
from domain_logic.task_domain_logic import TaskDomainLogic
from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum
from data_access.repository_interfaces.i_task_repository import ITaskRepository
from data_access.repository_implementations.task_repository import TaskRepository


class TestTaskApplicationServiceWithRepository:
    """测试任务应用服务与仓储集成"""
    
    @pytest.mark.asyncio
    async def test_create_task_via_application_service(self, async_session, sample_task_data):
        """测试通过应用服务创建任务"""
        service = TaskApplicationService(session=async_session)
        
        task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=sample_task_data["task_priority"],
            created_by=sample_task_data["created_by"],
            tags=sample_task_data["tags"]
        )
        
        assert task is not None
        assert task.task_content == sample_task_data["task_content"]
        assert task.task_priority == sample_task_data["task_priority"]
        assert task.created_by == sample_task_data["created_by"]
        assert task.task_status == TaskStatusEnum.PENDING
    
    @pytest.mark.asyncio
    async def test_create_task_with_validation(self, async_session):
        """测试应用服务验证任务"""
        service = TaskApplicationService(session=async_session)
        
        with pytest.raises(ValueError, match="无效的任务内容"):
            await service.create_task(task_content="")
        
        with pytest.raises(ValueError, match="无效的任务优先级"):
            await service.create_task(task_content="有效内容", task_priority=100)
    
    @pytest.mark.asyncio
    async def test_get_task_via_application_service(self, async_session, sample_task_data):
        """测试通过应用服务获取任务"""
        service = TaskApplicationService(session=async_session)
        
        created_task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=sample_task_data["task_priority"]
        )
        
        retrieved_task = await service.get_task(created_task.task_identifier)
        
        assert retrieved_task is not None
        assert retrieved_task.task_identifier == created_task.task_identifier
        assert retrieved_task.task_content == created_task.task_content
    
    @pytest.mark.asyncio
    async def test_list_tasks_via_application_service(self, async_session):
        """测试通过应用服务列出任务"""
        service = TaskApplicationService(session=async_session)
        
        await service.create_task("任务1", task_priority=5)
        await service.create_task("任务2", task_priority=3)
        await service.create_task("任务3", task_priority=7)
        
        tasks = await service.list_tasks(limit=10, offset=0)
        
        assert len(tasks) >= 3
    
    @pytest.mark.asyncio
    async def test_update_task_priority_via_application_service(self, async_session, sample_task_data):
        """测试通过应用服务更新任务优先级"""
        service = TaskApplicationService(session=async_session)
        
        task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=5
        )
        
        success = await service.update_task_priority(task.task_identifier, 8)
        
        assert success is True
        
        updated_task = await service.get_task(task.task_identifier)
        assert updated_task.task_priority == 8
    
    @pytest.mark.asyncio
    async def test_delete_task_via_application_service(self, async_session, sample_task_data):
        """测试通过应用服务删除任务"""
        service = TaskApplicationService(session=async_session)
        
        task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=5
        )
        
        success = await service.delete_task(task.task_identifier)
        
        assert success is True
        
        deleted_task = await service.get_task(task.task_identifier)
        assert deleted_task is None


class TestTaskApplicationServiceExecution:
    """测试任务应用服务执行逻辑"""
    
    @pytest.mark.asyncio
    async def test_execute_task_success_flow(self, async_session, sample_task_data):
        """测试任务执行成功流程"""
        service = TaskApplicationService(session=async_session)
        
        task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=5
        )
        
        result = await service.execute_task(task.task_identifier)
        
        assert result["success"] is True
        assert result["task_id"] == task.task_identifier
        assert result["status"] == "completed"
        
        executed_task = await service.get_task(task.task_identifier)
        assert executed_task.task_status == TaskStatusEnum.COMPLETED
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_task(self, async_session):
        """测试执行不存在的任务"""
        service = TaskApplicationService(session=async_session)
        
        with pytest.raises(ValueError, match="不存在"):
            await service.execute_task("nonexistent-id")
    
    @pytest.mark.asyncio
    async def test_execute_already_running_task(self, async_session, sample_task_data):
        """测试执行已经在运行的任务"""
        service = TaskApplicationService(session=async_session)
        
        task = await service.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=5
        )
        
        await service.execute_task(task.task_identifier)
        
        with pytest.raises(ValueError, match="不能从"):
            await service.execute_task(task.task_identifier)


class TestTaskStatisticsAndReporting:
    """测试任务统计和报告功能"""
    
    @pytest.mark.asyncio
    async def test_get_pending_tasks_count(self, async_session):
        """测试获取待处理任务数量"""
        service = TaskApplicationService(session=async_session)
        
        initial_count = await service.get_pending_tasks_count()
        
        await service.create_task("新任务1", task_priority=5)
        await service.create_task("新任务2", task_priority=3)
        
        new_count = await service.get_pending_tasks_count()
        
        assert new_count == initial_count + 2
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, async_session):
        """测试获取任务统计信息"""
        service = TaskApplicationService(session=async_session)
        
        task1 = await service.create_task("任务1", task_priority=5)
        task2 = await service.create_task("任务2", task_priority=3)
        
        await service.execute_task(task1.task_identifier)
        
        stats = await service.get_task_statistics()
        
        assert "total" in stats
        assert "pending" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert stats["total"] >= 2
        assert stats["completed"] >= 1
        assert stats["pending"] >= 1


class TestDomainLogicWithEntities:
    """测试领域逻辑与实体集成"""
    
    def test_domain_logic_validates_entity(self):
        """测试领域逻辑验证实体"""
        task = TaskEntity(
            task_identifier="validation-test",
            task_content="有效任务内容",
            task_priority=5
        )
        
        assert TaskDomainLogic.validate_task_content(task.task_content) is True
        assert TaskDomainLogic.validate_task_priority(task.task_priority) is True
        assert TaskDomainLogic.is_high_priority_task(task) is False
    
    def test_domain_logic_with_entity_transitions(self):
        """测试实体状态转换的领域逻辑验证"""
        task = TaskEntity(
            task_identifier="transition-test",
            task_content="状态转换测试"
        )
        
        assert TaskDomainLogic.can_transition_status(
            task.task_status,
            TaskStatusEnum.RUNNING
        ) is True
        
        task.mark_as_running()
        
        assert TaskDomainLogic.can_transition_status(
            task.task_status,
            TaskStatusEnum.COMPLETED
        ) is True
        
        task.mark_as_completed()
        
        assert TaskDomainLogic.can_transition_status(
            task.task_status,
            TaskStatusEnum.PENDING
        ) is False
    
    def test_entity_status_transitions_match_domain_logic(self):
        """测试实体状态转换与领域逻辑一致"""
        task = TaskEntity(
            task_identifier="consistency-test",
            task_content="一致性测试"
        )
        
        if TaskDomainLogic.can_transition_status(task.task_status, TaskStatusEnum.RUNNING):
            task.mark_as_running()
            assert task.task_status == TaskStatusEnum.RUNNING
        
        if TaskDomainLogic.can_transition_status(task.task_status, TaskStatusEnum.COMPLETED):
            task.mark_as_completed(result="成功")
            assert task.task_status == TaskStatusEnum.COMPLETED


class TestRepositoryImplementation:
    """测试仓储实现"""
    
    @pytest.mark.asyncio
    async def test_repository_create_and_retrieve(self, async_session, sample_task_data):
        """测试仓储创建和检索"""
        repository = TaskRepository(async_session)
        
        task = await repository.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=sample_task_data["task_priority"],
            created_by=sample_task_data["created_by"]
        )
        
        await async_session.commit()
        
        retrieved = await repository.get_task_by_id(task.task_identifier)
        
        assert retrieved is not None
        assert retrieved.task_identifier == task.task_identifier
    
    @pytest.mark.asyncio
    async def test_repository_update_status(self, async_session, sample_task_data):
        """测试仓储更新状态"""
        repository = TaskRepository(async_session)
        
        task = await repository.create_task(
            task_content=sample_task_data["task_content"],
            task_priority=sample_task_data["task_priority"]
        )
        
        await async_session.commit()
        
        success = await repository.update_task_status(
            task.task_identifier,
            TaskStatusEnum.RUNNING
        )
        
        assert success is True
        
        updated = await repository.get_task_by_id(task.task_identifier)
        assert updated.task_status == TaskStatusEnum.RUNNING
    
    @pytest.mark.asyncio
    async def test_repository_count_operations(self, async_session, sample_task_data):
        """测试仓储计数操作"""
        repository = TaskRepository(async_session)
        
        await repository.create_task("计数任务1", task_priority=5)
        await repository.create_task("计数任务2", task_priority=3)
        
        await async_session.commit()
        
        total = await repository.count_tasks()
        pending = await repository.count_tasks_by_status(TaskStatusEnum.PENDING)
        
        assert total >= 2
        assert pending >= 2
