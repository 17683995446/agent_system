"""
集成测试

测试多个模块协同工作的场景。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4

from multi_tenant.tenant_core import TenantRegistry, TenantTier, TenantStatus
from phase48_cache import MemoryCache, CacheManager
from phase49_security import TokenManager, PermissionManager, RateLimiter
from phase47_database import init_db, SessionLocal
from phase47_repository import TenantRepository


def test_tenant_with_cache():
    """测试租户系统与缓存集成"""
    registry = TenantRegistry()
    cache = MemoryCache()

    # 创建租户
    tenant = registry.create_tenant(
        name="Test Company",
        slug="test-company",
        email="test@example.com",
        owner_id=uuid4(),
        tier=TenantTier.PRO
    )
    assert tenant is not None

    # 缓存租户信息
    cache.set(f"tenant:{tenant.tenant_id}", {
        "name": tenant.name,
        "slug": tenant.slug
    })

    # 从缓存读取
    cached = cache.get(f"tenant:{tenant.tenant_id}")
    assert cached["name"] == "Test Company"
    print("test_tenant_with_cache PASSED")


def test_tenant_quota_check():
    """测试租户配额检查"""
    registry = TenantRegistry()

    tenant = registry.create_tenant(
        name="Test Company",
        slug="test-quota",
        email="test@example.com",
        owner_id=uuid4(),
        tier=TenantTier.FREE
    )

    # FREE tier: max_agents=5
    # 初始应该允许
    assert registry.check_quota(tenant.tenant_id, "agents", 1) is True

    # 记录使用
    registry.record_usage(tenant.tenant_id, "agents", 5)

    # 超出配额
    assert registry.check_quota(tenant.tenant_id, "agents", 1) is False
    print("test_tenant_quota_check PASSED")


def test_auth_flow():
    """测试完整认证流程"""
    token_manager = TokenManager()
    permission_manager = PermissionManager()

    # 1. 生成Token
    token = token_manager.generate_access_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read", "tenant:write"]
    )
    assert token is not None

    # 2. 验证Token
    payload = token_manager.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"

    # 3. 检查权限
    user_permissions = payload.get("permissions", [])
    assert permission_manager.has_permission(user_permissions, "tenant:read") is True
    assert permission_manager.has_permission(user_permissions, "tenant:delete") is False

    # 4. 检查租户访问
    assert permission_manager.has_tenant_access(
        "tenant456", "tenant456", user_permissions
    ) is True

    print("test_auth_flow PASSED")


def test_rate_limit_with_auth():
    """测试速率限制与认证集成"""
    from phase49_security import SecurityConfig
    config = SecurityConfig(rate_limit_requests=2, rate_limit_window_seconds=60)
    limiter = RateLimiter(config)
    token_manager = TokenManager()

    # 生成Token
    token = token_manager.generate_access_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read"]
    )
    payload = token_manager.verify_token(token)
    user_id = payload["sub"]

    # 前2次请求允许
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is True

    # 第3次请求拒绝（速率限制）
    assert limiter.is_allowed(user_id) is False

    print("test_rate_limit_with_auth PASSED")


def test_database_repository():
    """测试数据库与仓储集成"""
    # 初始化内存数据库
    from phase47_database import Base, engine
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    repo = TenantRepository(db)

    # 创建租户（使用随机slug避免冲突）
    import random, string
    random_slug = "db-test-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    tenant = repo.create(
        name="DB Test",
        slug=random_slug,
        email="db@test.com",
        owner_id=uuid4()
    )
    assert tenant is not None
    assert tenant.name == "DB Test"

    # 查询
    found = repo.get_by_id(tenant.tenant_id)
    assert found is not None
    assert found.name == "DB Test"

    # 检查配额
    allowed = repo.check_quota(tenant.tenant_id, "agents", 1)
    assert allowed is True

    # 记录使用
    repo.record_usage(tenant.tenant_id, "api_calls", 10)

    db.close()
    print("test_database_repository PASSED")


def test_service_layer_with_container():
    """测试服务层与容器集成"""
    from container import create_default_container, reset_container

    reset_container()
    container = create_default_container()

    # 获取认证服务
    auth_service = container.resolve("auth_service")
    assert auth_service is not None

    # 生成Token
    tokens = auth_service.generate_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read"]
    )
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 验证Token
    payload = auth_service.authenticate_with_token(tokens["access_token"])
    assert payload["sub"] == "user123"

    # 检查权限
    assert auth_service.check_permission(["tenant:read"], "tenant:read") is True

    print("test_service_layer_with_container PASSED")


if __name__ == "__main__":
    print("=" * 80)
    print("集成测试")
    print("=" * 80)

    test_tenant_with_cache()
    test_tenant_quota_check()
    test_auth_flow()
    test_rate_limit_with_auth()
    test_database_repository()
    test_service_layer_with_container()

    print("\n" + "=" * 80)
    print("所有集成测试通过！")
    print("=" * 80)
