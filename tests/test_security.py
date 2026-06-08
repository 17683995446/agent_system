"""
安全模块单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase49_security import (
    TokenManager, APIKeyManager, PermissionManager, RateLimiter,
    SecurityConfig
)


def test_token_generate_and_verify():
    """测试Token生成和验证"""
    manager = TokenManager()
    token = manager.generate_access_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read", "tenant:write"]
    )
    assert token is not None
    assert len(token) > 0

    payload = manager.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["tenant_id"] == "tenant456"
    print("test_token_generate_and_verify PASSED")


def test_token_revoke():
    """测试Token撤销"""
    manager = TokenManager()
    token = manager.generate_access_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read"]
    )

    # 撤销前可以验证
    assert manager.verify_token(token) is not None

    # 撤销
    assert manager.revoke_token(token) is True

    # 撤销后无法验证
    assert manager.verify_token(token) is None
    print("test_token_revoke PASSED")


def test_api_key_generate_and_verify():
    """测试API Key生成和验证"""
    manager = APIKeyManager()
    key_info = manager.generate_api_key(
        tenant_id="tenant789",
        name="Test Key",
        permissions=["tenant:read"]
    )
    assert key_info is not None
    assert "key_id" in key_info
    assert "full_key" in key_info

    # 验证
    verified = manager.verify_api_key(key_info["full_key"])
    assert verified is not None
    assert verified["tenant_id"] == "tenant789"
    print("test_api_key_generate_and_verify PASSED")


def test_api_key_revoke():
    """测试API Key撤销"""
    manager = APIKeyManager()
    key_info = manager.generate_api_key(
        tenant_id="tenant789",
        name="Test Key"
    )

    # 撤销
    assert manager.revoke_api_key(key_info["key_id"]) is True

    # 撤销后无法验证
    assert manager.verify_api_key(key_info["full_key"]) is None
    print("test_api_key_revoke PASSED")


def test_permission_check():
    """测试权限检查"""
    manager = PermissionManager()

    # 有权限
    assert manager.has_permission(["tenant:read", "tenant:write"], "tenant:read") is True

    # 无权限
    assert manager.has_permission(["tenant:read"], "tenant:write") is False

    # 管理员权限
    assert manager.has_permission(["admin:all"], "tenant:delete") is True
    print("test_permission_check PASSED")


def test_tenant_access():
    """测试租户访问控制"""
    manager = PermissionManager()

    # 同一租户
    assert manager.has_tenant_access("t1", "t1", ["tenant:read"]) is True

    # 不同租户（无管理员权限）
    assert manager.has_tenant_access("t1", "t2", ["tenant:read"]) is False

    # 不同租户（有管理员权限）
    assert manager.has_tenant_access("t1", "t2", ["admin:all"]) is True
    print("test_tenant_access PASSED")


def test_rate_limiter():
    """测试速率限制"""
    config = SecurityConfig(rate_limit_requests=3, rate_limit_window_seconds=60)
    limiter = RateLimiter(config)

    # 前3次允许
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True
    assert limiter.is_allowed("user1") is True

    # 第4次拒绝
    assert limiter.is_allowed("user1") is False

    # 不同用户不受影响
    assert limiter.is_allowed("user2") is True

    # 重置
    limiter.reset("user1")
    assert limiter.is_allowed("user1") is True
    print("test_rate_limiter PASSED")


if __name__ == "__main__":
    print("=" * 80)
    print("安全模块单元测试")
    print("=" * 80)

    test_token_generate_and_verify()
    test_token_revoke()
    test_api_key_generate_and_verify()
    test_api_key_revoke()
    test_permission_check()
    test_tenant_access()
    test_rate_limiter()

    print("\n" + "=" * 80)
    print("所有安全模块测试通过！")
    print("=" * 80)
