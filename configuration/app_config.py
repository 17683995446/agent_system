"""
配置管理 - 应用配置
统一管理所有配置项
"""
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """应用配置"""
    app_name: str = Field(default="Agent Eternal Evolution System")
    app_version: str = Field(default="2.8.0")
    version: str = Field(default="2.8.0")
    debug_mode: bool = Field(default=False)
    
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    database_url: str = Field(default="sqlite+aiosqlite:///./data/agent_system.db")
    
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")
    
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/agent_system.log")
    
    task_timeout_seconds: int = Field(default=3600)
    max_task_retries: int = Field(default=3)
    health_check_interval_seconds: int = Field(default=60)
    idle_evolution_interval_seconds: int = Field(default=300)
    
    @property
    def get_version(self) -> str:
        """获取版本号的兼容方法"""
        return self.app_version


@lru_cache()
def get_settings() -> AppConfig:
    """获取配置单例"""
    return AppConfig()
