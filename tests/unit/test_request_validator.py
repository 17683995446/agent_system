"""
第一层：API接入层 - 请求验证器单元测试
测试请求验证功能
"""
import pytest
from pydantic import ValidationError

from api_gateway.request_validator import (
    CreateTaskRequest,
    UpdateTaskRequest,
    ExecuteTaskRequest,
    RequestValidator
)


class TestCreateTaskRequest:
    """测试创建任务请求验证"""
    
    def test_valid_create_task_request(self):
        """测试有效创建任务请求"""
        request = CreateTaskRequest(
            task_content="测试任务内容",
            task_priority=5
        )
        
        assert request.task_content == "测试任务内容"
        assert request.task_priority == 5
    
    def test_create_task_request_with_all_fields(self):
        """测试带所有字段的创建任务请求"""
        request = CreateTaskRequest(
            task_content="完整任务",
            task_priority=8,
            created_by="test_user",
            tags=["tag1", "tag2"]
        )
        
        assert request.created_by == "test_user"
        assert request.tags == ["tag1", "tag2"]
    
    def test_create_task_request_empty_content(self):
        """测试空内容请求应失败"""
        with pytest.raises(ValidationError):
            CreateTaskRequest(task_content="")
    
    def test_create_task_request_none_content(self):
        """测试无内容请求应失败"""
        with pytest.raises(ValidationError):
            CreateTaskRequest(task_content=None)
    
    def test_create_task_request_invalid_priority(self):
        """测试无效优先级请求应失败"""
        with pytest.raises(ValidationError):
            CreateTaskRequest(task_content="内容", task_priority=100)


class TestUpdateTaskRequest:
    """测试更新任务请求验证"""
    
    def test_valid_update_task_request(self):
        """测试有效更新任务请求"""
        request = UpdateTaskRequest(
            task_id="test-id",
            task_priority=7
        )
        
        assert request.task_id == "test-id"
        assert request.task_priority == 7
    
    def test_update_task_request_empty_id(self):
        """测试空ID更新请求应失败"""
        with pytest.raises(ValidationError):
            UpdateTaskRequest(task_id="", task_priority=5)


class TestExecuteTaskRequest:
    """测试执行任务请求验证"""
    
    def test_valid_execute_task_request(self):
        """测试有效执行任务请求"""
        request = ExecuteTaskRequest(
            task_id="test-execute-id"
        )
        
        assert request.task_id == "test-execute-id"
    
    def test_execute_task_request_empty_id(self):
        """测试空ID执行请求应失败"""
        with pytest.raises(ValidationError):
            ExecuteTaskRequest(task_id="")


class TestRequestValidator:
    """测试请求验证器"""
    
    def test_validate_create_request_valid(self):
        """测试验证有效创建请求"""
        data = {
            "task_content": "验证测试",
            "task_priority": 5
        }
        
        validated = RequestValidator.validate_create_request(data)
        assert validated.task_content == "验证测试"
    
    def test_validate_create_request_missing_content(self):
        """测试验证缺失内容请求"""
        data = {"task_priority": 5}
        
        with pytest.raises(ValidationError):
            RequestValidator.validate_create_request(data)
    
    def test_validate_update_request_valid(self):
        """测试验证有效更新请求"""
        data = {
            "task_id": "update-test",
            "task_priority": 8
        }
        
        validated = RequestValidator.validate_update_request(data)
        assert validated.task_id == "update-test"
        assert validated.task_priority == 8
    
    def test_validate_execute_request_valid(self):
        """测试验证有效执行请求"""
        data = {"task_id": "execute-test"}
        
        validated = RequestValidator.validate_execute_request(data)
        assert validated.task_id == "execute-test"
