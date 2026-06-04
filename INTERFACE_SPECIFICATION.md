# 系统接口规范文档 v1.0

## 一、规范总览

### 1.1 设计原则
- **接口化**: 所有核心功能通过抽象接口定义
- **类型安全**: 100%类型注解覆盖
- **文档完备**: 每个接口都有清晰的文档字符串
- **单一职责**: 每个模块只负责一个明确的功能领域

### 1.2 模块架构

```
┌─────────────────────────────────────────────────────────┐
│                    API 接入层 (FastAPI)                  │
├─────────────────────────────────────────────────────────┤
│              应用服务层 (Application Service)             │
├─────────────────────────────────────────────────────────┤
│  租户服务    │  服务发现   │  安全认证   │  监控告警   │
│  TenantSvc   │  Discovery │  Security  │  Monitoring │
├─────────────────────────────────────────────────────────┤
│  缓存层 (Cache Layer)    │  消息队列 (可选)            │
├─────────────────────────────────────────────────────────┤
│  数据访问层 (Repository)  │  配置管理 (ConfigManager)   │
├─────────────────────────────────────────────────────────┤
│  数据库 (SQLite/PostgreSQL) │  Redis (可选)              │
└─────────────────────────────────────────────────────────┘
```

---

## 二、核心接口定义

### 2.1 缓存接口 (CacheBackend)

```python
from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict

class CacheBackend(ABC):
    """缓存后端抽象接口
    
    所有缓存实现必须遵循此接口，确保可替换性。
    
    Usage:
        cache = RedisCache()  # 或 MemoryCache()
        cache.set("key", {"data": "value"}, ttl=300)
        value = cache.get("key")
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在返回 None
            
        Raises:
            CacheException: 缓存服务异常时抛出
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值（必须可JSON序列化）
            ttl: 过期时间（秒），None表示永不过期
            
        Returns:
            设置是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            删除是否成功（键不存在也返回True）
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            键是否存在
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空所有缓存
        
        Returns:
            清空是否成功
            
        Warning:
            生产环境慎用！
        """
        pass
```

### 2.2 仓储接口 (Repository Pattern)

```python
from typing import Optional, List, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """仓储模式抽象基类
    
    提供标准的CRUD操作接口，所有实体仓储必须实现。
    
    Type Parameters:
        T: 实体类型
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
            limit: 返回数量限制（默认100）
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
```

### 2.3 安全认证接口 (Authentication)

```python
from typing import Optional, Dict, List
from datetime import datetime

class TokenManagerInterface(ABC):
    """Token管理接口
    
    提供JWT Token的生成、验证和撤销功能。
    """
    
    @abstractmethod
    def generate_access_token(
        self, 
        user_id: str, 
        tenant_id: str,
        permissions: List[str],
        expires_in: int = 1800
    ) -> str:
        """生成访问令牌
        
        Args:
            user_id: 用户唯一标识
            tenant_id: 租户ID
            permissions: 权限列表
            expires_in: 过期时间（秒，默认30分钟）
            
        Returns:
            JWT Token字符串
        """
        pass
    
    @abstractmethod
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证Token
        
        Args:
            token: JWT Token
            
        Returns:
            Token payload，无效返回None
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """撤销Token
        
        Args:
            token: 要撤销的Token
            
        Returns:
            撤销是否成功
        """
        pass

class PermissionCheckerInterface(ABC):
    """权限检查接口"""
    
    @abstractmethod
    def has_permission(
        self, 
        user_permissions: List[str], 
        required: str
    ) -> bool:
        """检查权限
        
        Args:
            user_permissions: 用户拥有的权限列表
            required: 需要的权限
            
        Returns:
            是否有权限
        """
        pass
    
    @abstractmethod
    def has_tenant_access(
        self,
        user_tenant_id: str,
        target_tenant_id: str,
        permissions: List[str]
    ) -> bool:
        """检查租户访问权限
        
        Args:
            user_tenant_id: 用户所属租户
            target_tenant_id: 目标租户
            permissions: 用户权限
            
        Returns:
            是否可以访问目标租户
        """
        pass
```

### 2.4 监控接口 (Monitoring)

```python
from enum import Enum
from typing import Dict, Any, Optional, Callable

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class MetricsCollectorInterface(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    def increment_counter(
        self, 
        name: str, 
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0
    ) -> None:
        """计数器递增
        
        Args:
            name: 指标名称
            labels: 标签字典
            value: 递增值（默认1.0）
        """
        pass
    
    @abstractmethod
    def set_gauge(
        self, 
        name: str, 
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """设置Gauge值
        
        Args:
            name: 指标名称
            value: 当前值
            labels: 标签字典
        """
        pass
    
    @abstractmethod
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """观察直方图值
        
        Args:
            name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        pass
    
    @abstractmethod
    def export_metrics(self) -> str:
        """导出Prometheus格式指标
        
        Returns:
            Prometheus文本格式
        """
        pass

class AlertManagerInterface(ABC):
    """告警管理器接口"""
    
    @abstractmethod
    def add_rule(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[float], bool],
        level: str,
        message: str
    ) -> None:
        """添加告警规则
        
        Args:
            name: 规则名称
            metric_name: 监控指标名
            condition: 触发条件函数
            level: 告警级别
            message: 告警消息
        """
        pass
    
    @abstractmethod
    def check_rules(self) -> List[Dict]:
        """检查所有告警规则
        
        Returns:
            触发的告警列表
        """
        pass
```

### 2.5 配置管理接口 (Configuration)

```python
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 20
    max_overflow: int = 10

class ConfigManagerInterface(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def get_config(self, env: Optional[Environment] = None) -> Dict[str, Any]:
        """获取配置
        
        Args:
            env: 环境类型，None表示当前环境
            
        Returns:
            配置字典
        """
        pass
    
    @abstractmethod
    def set_environment(self, env: Environment) -> None:
        """设置当前环境
        
        Args:
            env: 环境类型
        """
        pass
    
    @abstractmethod
    def is_production(self) -> bool:
        """是否生产环境
        
        Returns:
            是否是生产环境
        """
        pass
```

---

## 三、接口使用示例

### 3.1 缓存使用

```python
from phase48_cache import CacheManager, MemoryCache

# 创建缓存实例
cache = CacheManager(backend=MemoryCache())

# 设置缓存
cache.set("tenant:123", {"name": "Example Corp"}, ttl=300)

# 获取缓存（带自动加载）
def load_tenant():
    return {"name": "Example Corp", "tier": "enterprise"}

tenant = cache.get("tenant:123", loader=load_tenant, ttl=300)

# 删除缓存
cache.delete("tenant:123")
```

### 3.2 仓储使用

```python
from phase47_repository import TenantRepository
from phase47_database import SessionLocal

# 创建会话
db = SessionLocal()
repo = TenantRepository(db)

# 创建租户
tenant = repo.create(
    name="Example Corp",
    slug="example-corp",
    email="admin@example.com",
    owner_id=uuid.uuid4(),
    tier=TenantTierDB.PRO
)

# 查询租户
tenant = repo.get_by_id(tenant.tenant_id)

# 列取租户
tenants = repo.list(limit=10, offset=0)
```

### 3.3 安全认证使用

```python
from phase49_security import TokenManager, APIKeyManager

# Token管理
token_manager = TokenManager()
token = token_manager.generate_access_token(
    user_id="user123",
    tenant_id="tenant456",
    permissions=["tenant:read", "tenant:write"]
)

# 验证Token
payload = token_manager.verify_token(token)

# API Key管理
api_key_manager = APIKeyManager()
key_info = api_key_manager.generate_api_key(
    tenant_id="tenant789",
    name="Integration Key",
    permissions=["tenant:read"]
)

# 验证API Key
api_key_data = api_key_manager.verify_api_key(key_info["full_key"])
```

### 3.4 监控使用

```python
from phase50_monitoring import get_metrics, get_alert_manager

# 获取指标收集器
metrics = get_metrics()

# 记录请求
metrics.increment_counter(
    "http_requests_total",
    {"method": "GET", "endpoint": "/api/tenant"}
)

# 记录延迟
metrics.observe_histogram(
    "http_request_duration_seconds",
    0.045
)

# 检查告警
alert_manager = get_alert_manager()
alerts = alert_manager.check_rules()
```

---

## 四、错误处理规范

### 4.1 异常层次

```python
class SystemException(Exception):
    """系统基础异常"""
    pass

class ValidationError(SystemException):
    """数据验证错误"""
    pass

class NotFoundError(SystemException):
    """资源不存在"""
    pass

class DuplicateError(SystemException):
    """资源重复"""
    pass

class PermissionDeniedError(SystemException):
    """权限不足"""
    pass

class CacheException(SystemException):
    """缓存异常"""
    pass
```

### 4.2 错误响应格式

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "field": "email",
            "reason": "Invalid email format"
        },
        "timestamp": "2024-01-01T00:00:00Z",
        "request_id": "req-123456"
    }
}
```

---

## 五、版本控制规范

### 5.1 接口版本策略

- **URL版本**: `/api/v1/tenant`
- **Header版本**: `Accept: application/vnd.api.v1+json`
- **向后兼容**: 小版本更新保持兼容
- **废弃通知**: 大版本变更提前3个月通知

### 5.2 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2024-05-24 | 初始版本，包含基础CRUD、认证、监控 |
| v1.1 | - | 计划：添加批量操作接口 |
| v2.0 | - | 计划：GraphQL支持 |

---

## 六、测试规范

### 6.1 接口测试要求

每个接口必须包含：
1. **单元测试**: 独立测试每个方法
2. **集成测试**: 测试模块间交互
3. **性能测试**: 基准性能指标
4. **混沌测试**: 异常场景验证

### 6.2 测试覆盖率目标

- 代码覆盖率: ≥ 80%
- 接口覆盖率: 100%
- 异常分支: 100%

---

## 七、文档规范

### 7.1 文档字符串格式

```python
def example_function(param1: str, param2: int) -> bool:
    """函数简短描述
    
    函数的详细说明，包括功能、使用场景、注意事项等。
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明
        
    Returns:
        返回值的说明
        
    Raises:
        ValidationError: 当参数无效时
        NotFoundError: 当资源不存在时
        
    Examples:
        >>> example_function("test", 123)
        True
    """
    pass
```

### 7.2 接口文档工具

- **OpenAPI/Swagger**: API接口文档
- **TypeDoc**: 类型文档
- **README**: 项目说明

---

## 八、安全规范

### 8.1 认证要求

| 接口类型 | 认证方式 | 权限要求 |
|---------|---------|---------|
| 公开接口 | 无需认证 | 无 |
| 租户接口 | JWT Token | tenant:read |
| 管理接口 | JWT Token | admin:all |
| 服务接口 | API Key | service:read |

### 8.2 数据保护

- 敏感字段加密存储
- 传输使用HTTPS
- 日志脱敏处理
- 定期密钥轮换

---

## 九、性能规范

### 9.1 响应时间标准

| 接口类型 | P50 | P95 | P99 |
|---------|-----|-----|-----|
| 简单查询 | < 10ms | < 50ms | < 100ms |
| 复杂查询 | < 50ms | < 200ms | < 500ms |
| 写入操作 | < 100ms | < 500ms | < 1000ms |

### 9.2 并发标准

- 单实例QPS: ≥ 1000
- 并发连接: ≥ 1000
- 缓存命中率: ≥ 80%

---

## 十、部署规范

### 10.1 环境配置

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
      - JWT_SECRET=${JWT_SECRET}
```

### 10.2 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

**文档版本**: v1.0  
**最后更新**: 2024-05-24  
**维护者**: Multi-Tenant System Team
