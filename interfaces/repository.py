"""
仓储模式抽象接口定义

遵循仓储模式，为数据访问层提供清晰的契约。
所有实体仓储必须实现此接口，确保数据访问的一致性。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, TypeVar, Generic, Dict, Any
from uuid import UUID


T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """仓储模式抽象基类

    提供标准的CRUD操作接口，所有实体仓储必须实现。
    通过泛型支持不同类型的实体。

    Type Parameters:
        T: 实体类型

    Usage:
        class TenantRepository(Repository[Tenant]):
            def get_by_id(self, id: UUID) -> Optional[Tenant]:
                ...
    """

    @abstractmethod
    def get_by_id(self, id: UUID) -> Optional[T]:
        """根据ID获取实体

        Args:
            id: 实体唯一标识

        Returns:
            实体对象，不存在返回None
        """
        pass

    @abstractmethod
    def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """列取实体列表

        Args:
            limit: 返回数量限制（默认100，最大1000）
            offset: 偏移量（用于分页）

        Returns:
            实体列表
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """创建实体

        Args:
            entity: 实体对象

        Returns:
            创建后的实体（包含生成的ID）

        Raises:
            DuplicateError: 实体已存在
            ValidationError: 数据验证失败
        """
        pass

    @abstractmethod
    def update(self, id: UUID, entity: T) -> Optional[T]:
        """更新实体

        Args:
            id: 实体ID
            entity: 更新后的实体数据

        Returns:
            更新后的实体，不存在返回None
        """
        pass

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """删除实体

        Args:
            id: 实体ID

        Returns:
            删除是否成功
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """获取实体总数

        Returns:
            实体总数
        """
        pass


class TenantRepositoryInterface(Repository, ABC):
    """租户仓储接口

    扩展基础仓储，提供租户特定的数据访问方法。
    """

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Any]:
        """根据slug获取租户

        Args:
            slug: 租户slug

        Returns:
            租户对象，不存在返回None
        """
        pass

    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100, offset: int = 0) -> List[Any]:
        """根据状态获取租户列表

        Args:
            status: 租户状态
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            租户列表
        """
        pass

    @abstractmethod
    def update_status(self, tenant_id: UUID, status: str) -> bool:
        """更新租户状态

        Args:
            tenant_id: 租户ID
            status: 新状态

        Returns:
            更新是否成功
        """
        pass

    @abstractmethod
    def update_tier(self, tenant_id: UUID, tier: str) -> bool:
        """更新租户层级

        Args:
            tenant_id: 租户ID
            tier: 新层级

        Returns:
            更新是否成功
        """
        pass

    @abstractmethod
    def check_quota(self, tenant_id: UUID, resource_type: str, amount: int = 1) -> bool:
        """检查配额

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            amount: 请求数量

        Returns:
            是否有足够配额
        """
        pass

    @abstractmethod
    def record_usage(self, tenant_id: UUID, resource_type: str, amount: int = 1) -> bool:
        """记录使用量

        Args:
            tenant_id: 租户ID
            resource_type: 资源类型
            amount: 使用数量

        Returns:
            记录是否成功
        """
        pass


class ServiceRepositoryInterface(Repository, ABC):
    """服务仓储接口

    扩展基础仓储，提供服务实例特定的数据访问方法。
    """

    @abstractmethod
    def get_by_type(self, service_type: str, limit: int = 100) -> List[Any]:
        """根据类型获取服务实例

        Args:
            service_type: 服务类型
            limit: 返回数量限制

        Returns:
            服务实例列表
        """
        pass

    @abstractmethod
    def get_healthy_instances(self, service_type: str) -> List[Any]:
        """获取健康的服务实例

        Args:
            service_type: 服务类型

        Returns:
            健康实例列表
        """
        pass

    @abstractmethod
    def update_health(self, instance_id: str, health_score: float) -> bool:
        """更新健康评分

        Args:
            instance_id: 实例ID
            health_score: 健康评分（0-100）

        Returns:
            更新是否成功
        """
        pass

    @abstractmethod
    def update_status(self, instance_id: str, status: str) -> bool:
        """更新实例状态

        Args:
            instance_id: 实例ID
            status: 新状态

        Returns:
            更新是否成功
        """
        pass
