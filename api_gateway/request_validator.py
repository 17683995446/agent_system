"""
请求验证器
验证API请求的参数和数据格式
"""
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ValidationError, Field
from fastapi import HTTPException


class CreateTaskRequest(BaseModel):
    """创建任务请求模型"""
    task_content: str = Field(..., min_length=1, max_length=10000)
    task_priority: int = Field(default=0, ge=-10, le=10)
    created_by: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateTaskRequest(BaseModel):
    """更新任务请求模型"""
    task_id: str = Field(..., min_length=1)
    task_priority: Optional[int] = Field(default=None, ge=-10, le=10)


class ExecuteTaskRequest(BaseModel):
    """执行任务请求模型"""
    task_id: str = Field(..., min_length=1)


class RequestValidator:
    """请求验证器"""
    
    @staticmethod
    def validate_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """通用请求验证 - 验证基本请求格式"""
        if not isinstance(request_data, dict):
            raise HTTPException(status_code=400, detail="请求数据必须是字典格式")
        
        method = request_data.get("method", "GET")
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        if method not in valid_methods:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的HTTP方法: {method}，支持的方法: {', '.join(valid_methods)}"
            )
        
        path = request_data.get("path", "")
        if not path:
            raise HTTPException(status_code=400, detail="请求路径不能为空")
        
        headers = request_data.get("headers", {})
        if not isinstance(headers, dict):
            raise HTTPException(status_code=400, detail="请求头必须是字典格式")
        
        return {
            "method": method.upper(),
            "path": path.strip(),
            "headers": headers,
            "valid": True
        }
    
    @staticmethod
    def validate_create_request(data: Dict[str, Any]) -> 'CreateTaskRequest':
        """验证创建请求"""
        return CreateTaskRequest(**data)
    
    @staticmethod
    def validate_update_request(data: Dict[str, Any]) -> 'UpdateTaskRequest':
        """验证更新请求"""
        return UpdateTaskRequest(**data)
    
    @staticmethod
    def validate_execute_request(data: Dict[str, Any]) -> 'ExecuteTaskRequest':
        """验证执行请求"""
        return ExecuteTaskRequest(**data)
    
    @staticmethod
    def validate_create_task_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证创建任务请求"""
        if not data.get("task_content"):
            raise HTTPException(status_code=400, detail="任务内容不能为空")
        
        task_content = data["task_content"]
        if len(task_content) < 1 or len(task_content) > 10000:
            raise HTTPException(
                status_code=400,
                detail="任务内容长度必须在1-10000字符之间"
            )
        
        priority = data.get("task_priority", 0)
        if not isinstance(priority, int) or priority < -10 or priority > 10:
            raise HTTPException(
                status_code=400,
                detail="任务优先级必须在-10到10之间"
            )
        
        return {
            "task_content": task_content.strip(),
            "task_priority": priority,
        }
    
    @staticmethod
    def validate_task_id(task_id: str) -> str:
        """验证任务ID格式"""
        if not task_id or len(task_id) == 0:
            raise HTTPException(status_code=400, detail="任务ID不能为空")
        
        if len(task_id) > 100:
            raise HTTPException(status_code=400, detail="任务ID长度不能超过100")
        
        return task_id.strip()
    
    @staticmethod
    def validate_pagination_params(page: int, page_size: int) -> Dict[str, int]:
        """验证分页参数"""
        if page < 1:
            raise HTTPException(status_code=400, detail="页码必须大于0")
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="每页数量必须在1-100之间")
        
        return {"page": page, "page_size": page_size}
    
    @staticmethod
    def validate_priority(priority: int) -> int:
        """验证优先级参数"""
        if not isinstance(priority, int) or priority < -10 or priority > 10:
            raise HTTPException(
                status_code=400,
                detail="优先级必须在-10到10之间"
            )
        return priority
    
    @staticmethod
    def validate_memory_type(memory_type: str) -> str:
        """验证记忆类型"""
        valid_types = ["experience", "reflection", "knowledge", "strategy", "hot_memory"]
        if memory_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"记忆类型必须是以下之一: {', '.join(valid_types)}"
            )
        return memory_type
    
    @staticmethod
    def validate_task_status(status: str) -> str:
        """验证任务状态"""
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态必须是以下之一: {', '.join(valid_statuses)}"
            )
        return status
    
    @staticmethod
    def validate_string_field(
        field_name: str,
        value: str,
        min_length: int = 1,
        max_length: int = 1000
    ) -> str:
        """验证字符串字段"""
        if not value or len(value.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name}不能为空"
            )
        
        if len(value) < min_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name}长度不能少于{min_length}个字符"
            )
        
        if len(value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name}长度不能超过{max_length}个字符"
            )
        
        return value.strip()
    
    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """验证必需字段"""
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必需字段: {', '.join(missing_fields)}"
            )
        
        return data
