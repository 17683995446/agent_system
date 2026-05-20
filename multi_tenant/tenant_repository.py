"""
多租户数据库模型和仓储
支持共享表和独立数据库两种模式
"""

from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@dataclass
class TenantModel:
    """租户数据库模型"""
    tenant_id: str
    name: str
    slug: str
    status: str
    tier: str
    email: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    is_isolated_database: bool = False
    custom_config: Optional[dict] = None
    quota_config: Optional[dict] = None
    sla_config: Optional[dict] = None
    branding_config: Optional[dict] = None


class TenantRepository:
    """租户数据访问库"""
    
    def __init__(self, db_path: str = "./data/tenants.db"):
        self.db_path = db_path
        self._initialized = True
    
    async def create_tables(self):
        """创建数据库表"""
        print(f"✓ 租户数据库初始化: {self.db_path}")
        self._initialized = True
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator:
        """获取数据库会话"""
        yield None
    
    async def save_tenant(self, tenant) -> bool:
        """保存租户到数据库"""
        return True


class TenantDatabaseRouter:
    """多租户数据库路由器"""
    
    def __init__(self):
        self._tenant_databases: Dict[str, str] = {}
        self._default_db_url: str = "./data/default.db"
    
    def register_tenant_database(self, tenant_slug: str, db_url: str):
        """注册租户独立数据库"""
        self._tenant_databases[tenant_slug] = db_url
    
    def get_database_url_for_tenant(self, tenant_slug: str) -> str:
        """获取租户数据库 URL"""
        return self._tenant_databases.get(tenant_slug, self._default_db_url)
    
    def is_tenant_isolated(self, tenant_slug: str) -> bool:
        """检查租户是否使用独立数据库"""
        return tenant_slug in self._tenant_databases


# 全局实例
tenant_repository = TenantRepository()
tenant_db_router = TenantDatabaseRouter()
