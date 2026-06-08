"""
第四层：领域逻辑层 - 任务领域逻辑单元测试
测试任务核心业务规则
"""
import pytest
from datetime import datetime, timedelta

from domain_logic.task_domain_logic import TaskDomainLogic
from domain_model.enums.enums import TaskStatusEnum, PriorityLevelEnum


class MockTaskEntity:
    """模拟任务实体类"""
    
    def __init__(
        self,
        task_identifier: str = "test-task-id",
        task_content: str = "测试任务内容",
        task_status: TaskStatusEnum = TaskStatusEnum.PENDING,
        task_priority: int = 5,
        created_at: datetime = None
    ):
        self.task_identifier = task_identifier
        self.task_content = task_content
        self.task_status = task_status
        self.task_priority = task_priority
        self.created_at = created_at or datetime.utcnow()


class TestTaskDomainLogicValidation:
    """测试任务领域逻辑 - 验证方法"""
    
    def test_validate_task_content_with_valid_content(self):
        """测试验证有效任务内容"""
        valid_contents = [
            "简单任务",
            "这是一个稍微复杂一点的任务描述",
            "A" * 1000,
            "任务包含特殊字符 !@#$%^&*()",
            "任务包含中文内容测试"
        ]
        
        for content in valid_contents:
            assert TaskDomainLogic.validate_task_content(content) is True
    
    def test_validate_task_content_with_empty_content(self):
        """测试验证空任务内容"""
        invalid_contents = [
            "",
            "   ",
            "\t",
            "\n",
            "  \t  \n  "
        ]
        
        for content in invalid_contents:
            assert TaskDomainLogic.validate_task_content(content) is False
    
    def test_validate_task_content_with_too_long_content(self):
        """测试验证超长任务内容"""
        too_long_content = "A" * 10001
        assert TaskDomainLogic.validate_task_content(too_long_content) is False
    
    def test_validate_task_content_with_none_content(self):
        """测试验证None任务内容"""
        assert TaskDomainLogic.validate_task_content(None) is False
    
    def test_validate_task_priority_with_valid_priority(self):
        """测试验证有效任务优先级"""
        valid_priorities = [-10, -5, 0, 3, 5, 7, 10]
        
        for priority in valid_priorities:
            assert TaskDomainLogic.validate_task_priority(priority) is True
    
    def test_validate_task_priority_with_invalid_priority(self):
        """测试验证无效任务优先级"""
        invalid_priorities = [-11, -100, 11, 100, -1000]
        
        for priority in invalid_priorities:
            assert TaskDomainLogic.validate_task_priority(priority) is False


class TestTaskDomainLogicStatusTransition:
    """测试任务领域逻辑 - 状态转换"""
    
    def test_can_transition_from_pending_to_running(self):
        """测试待处理状态可以转换为运行中"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.PENDING,
            TaskStatusEnum.RUNNING
        ) is True
    
    def test_can_transition_from_pending_to_cancelled(self):
        """测试待处理状态可以转换为已取消"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.PENDING,
            TaskStatusEnum.CANCELLED
        ) is True
    
    def test_cannot_transition_from_pending_to_completed(self):
        """测试待处理状态不能直接转换为已完成"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.PENDING,
            TaskStatusEnum.COMPLETED
        ) is False
    
    def test_can_transition_from_running_to_completed(self):
        """测试运行中状态可以转换为已完成"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.RUNNING,
            TaskStatusEnum.COMPLETED
        ) is True
    
    def test_can_transition_from_running_to_failed(self):
        """测试运行中状态可以转换为失败"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.RUNNING,
            TaskStatusEnum.FAILED
        ) is True
    
    def test_can_transition_from_running_to_cancelled(self):
        """测试运行中状态可以转换为已取消"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.RUNNING,
            TaskStatusEnum.CANCELLED
        ) is True
    
    def test_cannot_transition_from_completed_state(self):
        """测试已完成状态不能转换到任何状态"""
        all_statuses = [
            TaskStatusEnum.PENDING,
            TaskStatusEnum.RUNNING,
            TaskStatusEnum.COMPLETED,
            TaskStatusEnum.FAILED,
            TaskStatusEnum.CANCELLED
        ]
        
        for status in all_statuses:
            assert TaskDomainLogic.can_transition_status(
                TaskStatusEnum.COMPLETED,
                status
            ) is False
    
    def test_can_transition_from_failed_to_pending(self):
        """测试失败状态可以重新排队"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.FAILED,
            TaskStatusEnum.PENDING
        ) is True
    
    def test_can_transition_from_cancelled_to_pending(self):
        """测试取消状态可以重新排队"""
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.CANCELLED,
            TaskStatusEnum.PENDING
        ) is True


class TestTaskDomainLogicScoreCalculation:
    """测试任务领域逻辑 - 评分计算"""
    
    def test_calculate_task_score_with_positive_priority(self):
        """测试计算正优先级任务评分"""
        task = MockTaskEntity(task_priority=5)
        score = TaskDomainLogic.calculate_task_score(task)
        assert score == 50
    
    def test_calculate_task_score_with_negative_priority(self):
        """测试计算负优先级任务评分"""
        task = MockTaskEntity(task_priority=-3)
        score = TaskDomainLogic.calculate_task_score(task)
        assert score == -30
    
    def test_calculate_task_score_with_zero_priority(self):
        """测试计算零优先级任务评分"""
        task = MockTaskEntity(task_priority=0)
        score = TaskDomainLogic.calculate_task_score(task)
        assert score == 0
    
    def test_calculate_task_score_with_high_priority(self):
        """测试计算高优先级任务评分"""
        task = MockTaskEntity(task_priority=10)
        score = TaskDomainLogic.calculate_task_score(task)
        assert score == 100


class TestTaskDomainLogicAutoCancel:
    """测试任务领域逻辑 - 自动取消判断"""
    
    def test_should_auto_cancel_with_old_pending_task(self):
        """测试超时应取消待处理任务"""
        old_time = datetime.utcnow() - timedelta(hours=2)
        task = MockTaskEntity(
            task_status=TaskStatusEnum.PENDING,
            created_at=old_time
        )
        assert TaskDomainLogic.should_auto_cancel(task, max_wait_seconds=3600) is True
    
    def test_should_not_auto_cancel_with_recent_pending_task(self):
        """测试不应取消最近的待处理任务"""
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        task = MockTaskEntity(
            task_status=TaskStatusEnum.PENDING,
            created_at=recent_time
        )
        assert TaskDomainLogic.should_auto_cancel(task, max_wait_seconds=3600) is False
    
    def test_should_not_auto_cancel_with_running_task(self):
        """测试运行中任务不应自动取消"""
        old_time = datetime.utcnow() - timedelta(hours=2)
        task = MockTaskEntity(
            task_status=TaskStatusEnum.RUNNING,
            created_at=old_time
        )
        assert TaskDomainLogic.should_auto_cancel(task) is False
    
    def test_should_not_auto_cancel_with_completed_task(self):
        """测试已完成任务不应自动取消"""
        old_time = datetime.utcnow() - timedelta(hours=2)
        task = MockTaskEntity(
            task_status=TaskStatusEnum.COMPLETED,
            created_at=old_time
        )
        assert TaskDomainLogic.should_auto_cancel(task) is False
    
    def test_should_not_auto_cancel_with_no_created_at(self):
        """测试没有创建时间的任务不应自动取消"""
        task = MockTaskEntity(created_at=None)
        assert TaskDomainLogic.should_auto_cancel(task) is False


class TestTaskDomainLogicPriorityLevel:
    """测试任务领域逻辑 - 优先级级别"""
    
    def test_get_priority_level_critical(self):
        """测试获取临界优先级"""
        assert TaskDomainLogic.get_priority_level(10) == PriorityLevelEnum.CRITICAL
        assert TaskDomainLogic.get_priority_level(15) == PriorityLevelEnum.CRITICAL
    
    def test_get_priority_level_high(self):
        """测试获取高优先级"""
        assert TaskDomainLogic.get_priority_level(7) == PriorityLevelEnum.HIGH
        assert TaskDomainLogic.get_priority_level(9) == PriorityLevelEnum.HIGH
    
    def test_get_priority_level_normal(self):
        """测试获取普通优先级"""
        assert TaskDomainLogic.get_priority_level(5) == PriorityLevelEnum.NORMAL
        assert TaskDomainLogic.get_priority_level(6) == PriorityLevelEnum.NORMAL
    
    def test_get_priority_level_low(self):
        """测试获取低优先级"""
        assert TaskDomainLogic.get_priority_level(3) == PriorityLevelEnum.LOW
        assert TaskDomainLogic.get_priority_level(4) == PriorityLevelEnum.LOW
    
    def test_get_priority_level_minimal(self):
        """测试获取最低优先级"""
        assert TaskDomainLogic.get_priority_level(0) == PriorityLevelEnum.MINIMAL
        assert TaskDomainLogic.get_priority_level(2) == PriorityLevelEnum.MINIMAL
        assert TaskDomainLogic.get_priority_level(-5) == PriorityLevelEnum.MINIMAL


class TestTaskDomainLogicHighPriority:
    """测试任务领域逻辑 - 高优先级判断"""
    
    def test_is_high_priority_task_with_high_priority(self):
        """测试高优先级任务识别"""
        task = MockTaskEntity(task_priority=8)
        assert TaskDomainLogic.is_high_priority_task(task) is True
    
    def test_is_high_priority_task_with_critical_priority(self):
        """测试紧急优先级任务识别"""
        task = MockTaskEntity(task_priority=10)
        assert TaskDomainLogic.is_high_priority_task(task) is True
    
    def test_is_not_high_priority_task_with_normal_priority(self):
        """测试普通优先级任务不是高优先级"""
        task = MockTaskEntity(task_priority=5)
        assert TaskDomainLogic.is_high_priority_task(task) is False
    
    def test_is_not_high_priority_task_with_low_priority(self):
        """测试低优先级任务不是高优先级"""
        task = MockTaskEntity(task_priority=2)
        assert TaskDomainLogic.is_high_priority_task(task) is False


class TestTaskDomainLogicExecuteImmediately:
    """测试任务领域逻辑 - 立即执行判断"""
    
    def test_should_execute_immediately_with_high_priority_pending(self):
        """测试高优先级待处理任务应立即执行"""
        task = MockTaskEntity(
            task_priority=8,
            task_status=TaskStatusEnum.PENDING
        )
        assert TaskDomainLogic.should_execute_immediately(task) is True
    
    def test_should_not_execute_immediately_with_running_task(self):
        """测试运行中任务不应立即执行"""
        task = MockTaskEntity(
            task_priority=8,
            task_status=TaskStatusEnum.RUNNING
        )
        assert TaskDomainLogic.should_execute_immediately(task) is False
    
    def test_should_not_execute_immediately_with_low_priority_pending(self):
        """测试低优先级待处理任务不应立即执行"""
        task = MockTaskEntity(
            task_priority=3,
            task_status=TaskStatusEnum.PENDING
        )
        assert TaskDomainLogic.should_execute_immediately(task) is False


class TestTaskDomainLogicIntegration:
    """测试任务领域逻辑 - 集成场景"""
    
    def test_full_task_lifecycle_validation(self):
        """测试完整任务生命周期验证"""
        task = MockTaskEntity(
            task_identifier="lifecycle-test",
            task_content="完整生命周期测试任务",
            task_status=TaskStatusEnum.PENDING,
            task_priority=8
        )
        
        assert TaskDomainLogic.validate_task_content(task.task_content) is True
        assert TaskDomainLogic.validate_task_priority(task.task_priority) is True
        assert TaskDomainLogic.is_high_priority_task(task) is True
        assert TaskDomainLogic.should_execute_immediately(task) is True
        
        assert TaskDomainLogic.can_transition_status(
            task.task_status,
            TaskStatusEnum.RUNNING
        ) is True
        
        task.task_status = TaskStatusEnum.RUNNING
        assert TaskDomainLogic.can_transition_status(
            task.task_status,
            TaskStatusEnum.COMPLETED
        ) is True
    
    def test_task_retry_scenario(self):
        """测试任务重试场景"""
        failed_task = MockTaskEntity(
            task_status=TaskStatusEnum.FAILED,
            task_priority=5
        )
        
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.FAILED,
            TaskStatusEnum.PENDING
        ) is True
        
        assert TaskDomainLogic.should_execute_immediately(failed_task) is False
    
    def test_task_cancellation_and_resubmission(self):
        """测试任务取消和重新提交"""
        cancelled_task = MockTaskEntity(
            task_status=TaskStatusEnum.CANCELLED,
            task_priority=5
        )
        
        assert TaskDomainLogic.can_transition_status(
            TaskStatusEnum.CANCELLED,
            TaskStatusEnum.PENDING
        ) is True
        
        cancelled_task.task_status = TaskStatusEnum.PENDING
        assert TaskDomainLogic.should_execute_immediately(cancelled_task) is False
