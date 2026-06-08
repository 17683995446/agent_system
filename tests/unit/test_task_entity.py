"""
第五层：领域模型层 - 任务实体单元测试
测试任务实体核心功能
"""
import pytest
from datetime import datetime

from domain_model.entities.task_entity import TaskEntity
from domain_model.enums.enums import TaskStatusEnum


class TestTaskEntityCreation:
    """测试任务实体创建"""
    
    def test_task_entity_with_minimal_parameters(self):
        """测试使用最小参数创建任务实体"""
        task = TaskEntity(
            task_identifier="minimal-task",
            task_content="最小任务"
        )
        
        assert task.task_identifier == "minimal-task"
        assert task.task_content == "最小任务"
        assert task.task_status == TaskStatusEnum.PENDING
        assert task.task_priority == 0
        assert task.created_at is not None
    
    def test_task_entity_with_all_parameters(self):
        """测试使用所有参数创建任务实体"""
        now = datetime.utcnow()
        task = TaskEntity(
            task_identifier="full-task",
            task_content="完整任务内容",
            task_status=TaskStatusEnum.RUNNING,
            task_priority=8,
            task_result="执行结果",
            error_message=None,
            execution_duration_seconds=120,
            started_at=now,
            completed_at=None,
            created_at=now,
            updated_at=now,
            created_by="test_user",
            tags="tag1,tag2,tag3",
            metadata_json='{"key": "value"}'
        )
        
        assert task.task_identifier == "full-task"
        assert task.task_content == "完整任务内容"
        assert task.task_status == TaskStatusEnum.RUNNING
        assert task.task_priority == 8
        assert task.task_result == "执行结果"
        assert task.created_by == "test_user"
        assert task.tags == "tag1,tag2,tag3"
    
    def test_task_entity_default_values(self):
        """测试任务实体默认值"""
        task = TaskEntity(
            task_identifier="default-task",
            task_content="默认任务"
        )
        
        assert task.task_result is None
        assert task.error_message is None
        assert task.execution_duration_seconds is None
        assert task.started_at is None
        assert task.completed_at is None
        assert task.created_by is None
        assert task.tags is None


class TestTaskEntityToDict:
    """测试任务实体字典转换"""
    
    def test_to_dict_with_complete_task(self):
        """测试完整任务转换为字典"""
        now = datetime.utcnow()
        task = TaskEntity(
            task_identifier="dict-task",
            task_content="字典转换任务",
            task_status=TaskStatusEnum.COMPLETED,
            task_priority=7,
            task_result="成功结果",
            execution_duration_seconds=60,
            started_at=now,
            completed_at=now,
            created_at=now,
            updated_at=now,
            created_by="dict_user",
            tags="tag1,tag2"
        )
        
        result = task.to_dict()
        
        assert isinstance(result, dict)
        assert result["task_id"] == "dict-task"
        assert result["task_content"] == "字典转换任务"
        assert result["task_status"] == "completed"
        assert result["task_priority"] == 7
        assert result["task_result"] == "成功结果"
        assert result["created_by"] == "dict_user"
        assert result["tags"] == ["tag1", "tag2"]
        assert result["execution_duration_seconds"] == 60
    
    def test_to_dict_with_pending_task(self):
        """测试待处理任务转换为字典"""
        task = TaskEntity(
            task_identifier="pending-dict",
            task_content="待处理任务",
            task_status=TaskStatusEnum.PENDING,
            task_priority=5
        )
        
        result = task.to_dict()
        
        assert result["task_id"] == "pending-dict"
        assert result["task_status"] == "pending"
        assert result["task_result"] is None
        assert result["started_at"] is None
        assert result["completed_at"] is None
        assert result["tags"] == []
    
    def test_to_dict_with_failed_task(self):
        """测试失败任务转换为字典"""
        task = TaskEntity(
            task_identifier="failed-dict",
            task_content="失败任务",
            task_status=TaskStatusEnum.FAILED,
            error_message="测试错误信息"
        )
        
        result = task.to_dict()
        
        assert result["task_status"] == "failed"
        assert result["error_message"] == "测试错误信息"
        assert result["task_result"] is None


class TestTaskEntityStatusTransition:
    """测试任务实体状态转换"""
    
    def test_mark_as_running(self):
        """测试标记为运行中"""
        task = TaskEntity(
            task_identifier="running-mark",
            task_content="运行标记任务"
        )
        
        task.mark_as_running()
        
        assert task.task_status == TaskStatusEnum.RUNNING
        assert task.started_at is not None
        assert task.updated_at is not None
    
    def test_mark_as_completed_with_result(self):
        """测试标记为完成（带结果）"""
        task = TaskEntity(
            task_identifier="completed-mark",
            task_content="完成标记任务"
        )
        
        task.mark_as_running()
        task.mark_as_completed(result="执行成功", duration=100)
        
        assert task.task_status == TaskStatusEnum.COMPLETED
        assert task.task_result == "执行成功"
        assert task.execution_duration_seconds == 100
        assert task.completed_at is not None
    
    def test_mark_as_completed_without_duration(self):
        """测试标记为完成（不带时长）"""
        task = TaskEntity(
            task_identifier="completed-no-duration",
            task_content="完成无时长任务"
        )
        
        task.mark_as_completed(result="快速完成")
        
        assert task.task_status == TaskStatusEnum.COMPLETED
        assert task.task_result == "快速完成"
        assert task.execution_duration_seconds is None
    
    def test_mark_as_failed(self):
        """测试标记为失败"""
        task = TaskEntity(
            task_identifier="failed-mark",
            task_content="失败标记任务"
        )
        
        task.mark_as_failed(error_message="执行失败原因")
        
        assert task.task_status == TaskStatusEnum.FAILED
        assert task.error_message == "执行失败原因"
        assert task.completed_at is not None


class TestTaskEntityRepr:
    """测试任务实体字符串表示"""
    
    def test_repr_format(self):
        """测试__repr__格式"""
        task = TaskEntity(
            task_identifier="repr-test",
            task_content="表示测试",
            task_status=TaskStatusEnum.PENDING
        )
        
        repr_str = repr(task)
        
        assert "repr-test" in repr_str
        assert "pending" in repr_str
        assert "TaskEntity" in repr_str
    
    def test_repr_with_running_status(self):
        """测试运行状态的__repr__"""
        task = TaskEntity(
            task_identifier="running-repr",
            task_content="运行表示",
            task_status=TaskStatusEnum.RUNNING
        )
        
        repr_str = repr(task)
        
        assert "running-repr" in repr_str
        assert "running" in repr_str


class TestTaskEntityLifecycle:
    """测试任务实体生命周期"""
    
    def test_full_successful_lifecycle(self):
        """测试完整成功生命周期"""
        task = TaskEntity(
            task_identifier="lifecycle-success",
            task_content="完整生命周期成功",
            task_priority=8
        )
        
        assert task.task_status == TaskStatusEnum.PENDING
        
        task.mark_as_running()
        assert task.task_status == TaskStatusEnum.RUNNING
        assert task.started_at is not None
        
        task.mark_as_completed(result="完美执行", duration=50)
        assert task.task_status == TaskStatusEnum.COMPLETED
        assert task.task_result == "完美执行"
        assert task.completed_at is not None
        
        result = task.to_dict()
        assert result["task_status"] == "completed"
        assert result["execution_duration_seconds"] == 50
    
    def test_full_failed_lifecycle(self):
        """测试完整失败生命周期"""
        task = TaskEntity(
            task_identifier="lifecycle-failed",
            task_content="完整生命周期失败"
        )
        
        task.mark_as_running()
        assert task.task_status == TaskStatusEnum.RUNNING
        
        task.mark_as_failed(error_message="网络连接超时")
        assert task.task_status == TaskStatusEnum.FAILED
        assert task.error_message == "网络连接超时"
        assert task.completed_at is not None
        
        result = task.to_dict()
        assert result["task_status"] == "failed"
        assert result["error_message"] == "网络连接超时"
