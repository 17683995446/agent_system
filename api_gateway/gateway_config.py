"""
API网关配置
管理API网关的所有配置项
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GatewayConfig(BaseModel):
    """API网关配置类"""
    
    host: str = Field(default="0.0.0.0", description="监听主机地址")
    port: int = Field(default=8000, description="监听端口")
    debug_mode: bool = Field(default=False, description="调试模式")
    
    cors_allowed_origins: List[str] = Field(
        default=["*"],
        description="允许的CORS源"
    )
    cors_allowed_methods: List[str] = Field(
        default=["*"],
        description="允许的HTTP方法"
    )
    cors_allowed_headers: List[str] = Field(
        default=["*"],
        description="允许的HTTP头"
    )
    
    rate_limit_per_minute: int = Field(
        default=100,
        description="每分钟请求限制"
    )
    request_timeout_seconds: int = Field(
        default=30,
        description="请求超时时间（秒）"
    )
    
    enable_request_validation: bool = Field(
        default=True,
        description="是否启用请求验证"
    )
    enable_response_compression: bool = Field(
        default=True,
        description="是否启用响应压缩"
    )
    
    openapi_url: str = Field(
        default="/openapi.json",
        description="OpenAPI文档路径"
    )
    docs_url: str = Field(
        default="/docs",
        description="API文档路径"
    )
    redoc_url: str = Field(
        default="/redoc",
        description="ReDoc文档路径"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug_mode": False,
                "cors_allowed_origins": ["*"],
                "rate_limit_per_minute": 100,
                "request_timeout_seconds": 30,
            }
        }
