"""
租户应用服务

提供租户相关的业务逻辑，包括租户管理、配额管理、使用统计等。
服务层负责业务规则的实现，不直接操作数据库。
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from interfaces.repository import TenantRepositoryInterface
from interfaces.cache import CacheManagerInterface
from exceptions import (
    NotFoundError, DuplicateError, ValidationError,
    TenantError, QuotaExceededError
)

logger = logging.getLogger(__name__)


class TenantService:
    """租户应用服务

    提供租户管理的业务逻辑，包括：
    - 租户CRUD操作
    - 配额管理
    - 使用统计
    - 状态管理

    Attributes:
        tenant_repo: 租户仓储接口
        cache_manager: 缓存管理器接口
    """

    def __init__(
        self,
        tenant_repo: TenantRepositoryInterface,
        cache_manager: CacheManagerInterface
    ):
        self.tenant_repo = tenant_repo
        self.cache_manager = cache_manager
        logger.info("[TenantService] 初始化完成")

    def create_tenant(
        self,
        name: str,
        slug: str,
        email: str,
        owner_id: uuid.UUID,
        tier: str = "free",
        is_isolated: bool = False
    ) -> Dict[str, Any]:
        """创建租户

        Args:
            name: 租户名称
            slug: 租户slug（唯一标识）
            email: 联系邮箱
            owner_id: 所有者ID
            tier: 租户层级（默认free）
            is_isolated: 是否隔离

        Returns:
            创建的租户信息

        Raises:
            ValidationError: 输入数据无效
            DuplicateError: slug已存在
        """
        # 验证输入
        if not name or len(name) < 2:
            raise ValidationError("Tenant name must be at least 2 characters")
        if not slug or len(slug) < 2:
            raise ValidationError("Tenant slug must be at least 2 characters")
        if not email or "@" not in email:
            raise ValidationError("Invalid email format")

        # 检查slug是否已存在
        existing = self.tenant_repo.get_by_slug(slug)
        if existing:
            raise DuplicateError("Tenant", slug)

        # 创建租户
        tenant = self.tenant_repo.create({
            "name": name,
            "slug": slug,
            "email": email,
            "owner_id": owner_id,
            "tier": tier,
            "is_isolated": is_isolated
        })

        # 失效缓存
        self.cache_manager.invalidate_tenant(str(tenant.tenant_id))

        logger.info(f"[TenantService] 创建租户成功: {tenant.tenant_id}")
        return self._to_dict(tenant)

    def get_tenant(self, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """获取租户信息

        Args:
            tenant_id: 租户ID

        Returns:
            租户信息

        Raises:
            NotFoundError: 租户不存在
        """
        # 尝试从缓存获取
        cache_key = f"tenant:{tenant_id}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached

        # 从数据库获取
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        # 存入缓存
        tenant_dict = self._to_dict(tenant)
        self.cache_manager.set(cache_key, tenant_dict, ttl=300)

        return tenant_dict

    def get_tenant_by_slug(self, slug: str) -> Dict[str, Any]:
        """根据slug获取租户

        Args:
            slug: 租户slug

        Returns:
            租户信息

        Raises:
            NotFoundError: 租户不存在
        """
        tenant = self.tenant_repo.get_by_slug(slug)
        if not tenant:
            raise NotFoundError("Tenant", slug)

        return self._to_dict(tenant)

    def list_tenants(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列取租户列表

        Args:
            status: 过滤状态
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            租户列表
        """
        if status:
            tenants = self.tenant_repo.get_by_status(status, limit, offset)
        else:
            tenants = self.tenant_repo.list(limit, offset)

        return [self._to_dict(t) for t in tenants]

    def update_tenant_status(
        self,
        tenant_id: uuid.UUID,
        status: str
    ) -> Dict[str, Any]:
        """更新租户状态

        Args:
            tenant_id: 租户ID
            status: 新状态

        Returns:
            更新后的租户信息

        Raises:
            NotFoundError: 租户不存在
            ValidationError: 状态无效
        """
        valid_statuses = ["active", "inactive", "suspended", "pending"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {valid_statuses}"
            )

        success = self.tenant_repo.update_status(tenant_id, status)
        if not success:
            raise NotFoundError("Tenant", str(tenant_id))

        # 失效缓存
        self.cache_manager.invalidate_tenant(str(tenant_id))

        # 返回更新后的租户
        return self.get_tenant(tenant_id)

    def update_tenant_tier(
        self,
        tenant_id: uuid.UUID,
        tier: str
    ) -> Dict[str, Any]:
        """更新租户层级

        Args:
            tenant_id: 租户ID
            tier: 新层级

        Returns:
            更新后的租户信息

        Raises:
            NotFoundError: 租户不存在
            ValidationError: 层级无效
        """
        valid_tiers = ["free", "starter", "basic", "pro", "enterprise", "unlimited", "custom"]
        if tier not in valid_tiers:
            raise ValidationError(
                f"Invalid tier. Must be one of: {valid_tiers}"
            )

        success = self.tenant_repo.update_tier(tenant_id, tier)
        if not success:
            raise NotFoundError("Tenant", str(tenant_id))

        # 失效缓存
        self.cache_manager.invalidate_tenant(str(tenant_id))

        return self.get_tenant(tenant_id)

    def check_quota(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """检查配额

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            amount: 请求数量

        Returns:
            是否有足够配额

        Raises:
            NotFoundError: 租户不存在
        """
        # 验证租户存在
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        return self.tenant_repo.check_quota(tenant_id, resource_type, amount)

    def record_usage(
        self,
        tenant_id: uuid.UUID,
        resource_type: str,
        amount: int = 1
    ) -> Dict[str, Any]:
        """记录使用量

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            amount: 使用数量

        Returns:
            使用统计信息

        Raises:
            NotFoundError: 租户不存在
            QuotaExceededError: 配额已超限
        """
        # 检查配额
        if not self.check_quota(tenant_id, resource_type, amount):
            raise QuotaExceededError(
                resource_type=resource_type,
                current=None,
                limit=None
            )

        # 记录使用
        success = self.tenant_repo.record_usage(tenant_id, resource_type, amount)
        if not success:
            raise TenantError(
                message="Failed to record usage",
                tenant_id=str(tenant_id),
                operation="record_usage"
            )

        # 失效使用量缓存
        self.cache_manager.delete(f"usage:{tenant_id}")

        return {
            "tenant_id": str(tenant_id),
            "resource_type": resource_type,
            "amount": amount,
            "recorded_at": datetime.now().isoformat()
        }

    def delete_tenant(self, tenant_id: uuid.UUID) -> bool:
        """删除租户

        Args:
            tenant_id: 租户ID

        Returns:
            删除是否成功

        Raises:
            NotFoundError: 租户不存在
        """
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant", str(tenant_id))

        # 删除租户
        success = self.tenant_repo.delete(tenant_id)
        if success:
            # 失效缓存
            self.cache_manager.invalidate_tenant(str(tenant_id))
            logger.info(f"[TenantService] 删除租户: {tenant_id}")

        return success

    def _to_dict(self, tenant) -> Dict[str, Any]:
        """将租户对象转换为字典

        Args:
            tenant: 租户对象

        Returns:
            租户字典
        """
        return {
            "tenant_id": str(tenant.tenant_id) if hasattr(tenant, 'tenant_id') else str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "email": tenant.email,
            "status": tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
            "tier": tenant.tier.value if hasattr(tenant.tier, 'value') else tenant.tier,
            "created_at": tenant.created_at.isoformat() if hasattr(tenant, 'created_at') else None,
        }
