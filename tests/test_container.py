"""
依赖注入容器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from container import Container, create_default_container, get_container, reset_container


def test_container_basic():
    """测试容器基本功能"""
    container = Container()

    def factory(c):
        return {"type": "test"}

    container.register_factory("test", factory, singleton=True)
    val = container.resolve("test")
    assert val == {"type": "test"}
    print("test_container_basic PASSED")


def test_container_singleton():
    """测试单例模式"""
    container = Container()

    class Counter:
        def __init__(self):
            self.count = 0

    container.register_factory("counter", lambda c: Counter(), singleton=True)
    c1 = container.resolve("counter")
    c2 = container.resolve("counter")
    assert c1 is c2
    print("test_container_singleton PASSED")


def test_container_not_found():
    """测试未注册组件"""
    container = Container()
    try:
        container.resolve("nonexistent")
        assert False, "Should raise KeyError"
    except KeyError:
        pass
    print("test_container_not_found PASSED")


def test_default_container():
    """测试默认容器"""
    reset_container()
    container = create_default_container()
    assert container.has("cache_manager")
    assert container.has("token_manager")
    assert container.has("auth_service")
    assert container.has("tenant_service")
    print("test_default_container PASSED")


def test_service_resolution():
    """测试服务解析"""
    reset_container()
    container = create_default_container()

    cache = container.resolve("cache_manager")
    assert cache is not None

    auth = container.resolve("auth_service")
    assert auth is not None

    # 测试单例
    cache2 = container.resolve("cache_manager")
    assert cache is cache2
    print("test_service_resolution PASSED")


if __name__ == "__main__":
    print("=" * 80)
    print("容器单元测试")
    print("=" * 80)

    test_container_basic()
    test_container_singleton()
    test_container_not_found()
    test_default_container()
    test_service_resolution()

    print("\n" + "=" * 80)
    print("所有容器测试通过！")
    print("=" * 80)
