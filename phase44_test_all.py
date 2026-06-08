#!/usr/bin/env python3
"""
Phase 44: 标准化全流程测试
执行全面的测试，包括单元测试、集成测试、接口测试、业务场景测试等
"""

import sys
import os
import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_tenant.tenant_core import (
    TenantRegistry, TenantStatus, TenantTier,
    tenant_registry, TenantQuota, TenantSLA
)
from distributed.distributed_core import (
    ServiceRegistry, LoadBalancer, ServiceInstance,
    ServiceStatus, ServiceType
)

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0
}

def log_test(name: str, passed: bool, message: str = ""):
    """记录测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ [PASS] {name} {message}")
    else:
        test_results["failed"] += 1
        print(f"❌ [FAIL] {name} {message}")


def test_tenant_registry_basic():
    """测试租户注册表基本功能"""
    print("\n=== 1. 租户注册表基本功能测试 ===")
    
    test_registry = TenantRegistry()
    owner_id = uuid.uuid4()
    
    # 测试创建租户
    try:
        tenant = test_registry.create_tenant(
            name="测试公司",
            slug="test-company",
            email="test@example.com",
            owner_id=owner_id,
            tier=TenantTier.FREE
        )
        log_test("创建租户", True, f"租户ID: {tenant.tenant_id}")
    except Exception as e:
        log_test("创建租户", False, str(e))
        return
    
    # 测试获取租户
    tenant_by_id = test_registry.get_tenant(tenant.tenant_id)
    log_test("通过ID获取租户", tenant_by_id is not None and tenant_by_id.name == "测试公司")
    
    tenant_by_slug = test_registry.get_tenant_by_slug("test-company")
    log_test("通过Slug获取租户", tenant_by_slug is not None and tenant_by_slug.tenant_id == tenant.tenant_id)
    
    # 测试更新租户状态
    updated = test_registry.update_tenant_status(tenant.tenant_id, TenantStatus.SUSPENDED)
    log_test("更新租户状态", updated)
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("验证状态更新", tenant is not None and tenant.status == TenantStatus.SUSPENDED)
    
    # 测试更新租户层级
    updated = test_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
    log_test("更新租户层级", updated)
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("验证层级更新", tenant is not None and tenant.tier == TenantTier.PRO)
    
    # 测试删除租户
    deleted = test_registry.delete_tenant(tenant.tenant_id)
    log_test("删除租户", deleted)
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("验证租户已删除", tenant is None)


def test_tenant_quota_management():
    """测试租户配额管理"""
    print("\n=== 2. 租户配额管理测试 ===")
    
    test_registry = TenantRegistry()
    owner_id = uuid.uuid4()
    
    tenant = test_registry.create_tenant(
        name="配额测试公司",
        slug="quota-test",
        email="quota@example.com",
        owner_id=owner_id,
        tier=TenantTier.STARTER
    )
    log_test("创建STARTER层级租户", True)
    
    # 测试检查配额
    can_create = test_registry.check_quota(tenant.tenant_id, "agents", 1)
    log_test("检查agents配额（剩余）", can_create)
    
    # 测试记录使用量
    recorded = test_registry.record_usage(tenant.tenant_id, "agents", 1)
    log_test("记录使用量", recorded)
    
    # 验证配额
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("验证使用量已记录", tenant.usage.agents_created == 1)
    
    # 测试配额超限
    test_registry.record_usage(tenant.tenant_id, "agents", 1)
    can_create_more = test_registry.check_quota(tenant.tenant_id, "agents", 1)
    log_test("STARTER层级配额超限检查", not can_create_more)


def test_all_tenant_tiers():
    """测试所有租户层级"""
    print("\n=== 3. 所有租户层级测试 ===")
    
    test_registry = TenantRegistry()
    owner_id = uuid.uuid4()
    
    tiers = [
        TenantTier.STARTER,
        TenantTier.FREE,
        TenantTier.BASIC,
        TenantTier.PRO,
        TenantTier.ENTERPRISE,
        TenantTier.UNLIMITED,
        TenantTier.CUSTOM
    ]
    
    all_passed = True
    for tier in tiers:
        try:
            tenant = test_registry.create_tenant(
                name=f"测试{tier.value}",
                slug=f"test-{tier.value}",
                email=f"{tier.value}@example.com",
                owner_id=owner_id,
                tier=tier
            )
            print(f"  ✅ {tier.value} 层级创建成功，配额: {tenant.quota}")
        except Exception as e:
            print(f"  ❌ {tier.value} 层级创建失败: {e}")
            all_passed = False
    
    log_test("所有租户层级测试", all_passed)


def test_tenant_concurrent_access():
    """测试租户并发访问（竞态条件修复验证）"""
    print("\n=== 4. 租户并发访问测试 ===")
    
    test_registry = TenantRegistry()
    owner_id = uuid.uuid4()
    
    tenant = test_registry.create_tenant(
        name="并发测试公司",
        slug="concurrent-test",
        email="concurrent@example.com",
        owner_id=owner_id,
        tier=TenantTier.PRO
    )
    
    num_threads = 50
    operations_per_thread = 100
    results = []
    errors = []
    
    def worker(thread_id):
        try:
            for i in range(operations_per_thread):
                test_registry.record_usage(tenant.tenant_id, "api_calls", 1)
                test_registry.check_quota(tenant.tenant_id, "api_calls", 1)
            results.append(thread_id)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")
    
    threads = []
    start_time = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    end_time = time.time()
    
    log_test("并发测试无错误", len(errors) == 0, f"错误数: {len(errors)}")
    
    tenant = test_registry.get_tenant(tenant.tenant_id)
    expected_calls = num_threads * operations_per_thread
    log_test("并发使用量计数准确", tenant.usage.total_api_calls == expected_calls, 
             f"期望: {expected_calls}, 实际: {tenant.usage.total_api_calls}")
    
    print(f"  完成 {num_threads} 线程 * {operations_per_thread} 操作，耗时 {end_time - start_time:.2f}s")


def test_service_registry_basic():
    """测试服务注册表基本功能"""
    print("\n=== 5. 服务注册表基本功能测试 ===")
    
    service_registry = ServiceRegistry()
    
    # 测试注册服务
    instance = ServiceInstance(
        instance_id=str(uuid.uuid4()),
        service_name="test-service",
        service_type=ServiceType.API_GATEWAY,
        version="1.0.0",
        host="localhost",
        port=8000,
        status=ServiceStatus.HEALTHY
    )
    
    # 使用同步方法注册
    registered = service_registry.register_service(
        "test-service",
        ServiceType.API_GATEWAY,
        "localhost",
        8000
    )
    log_test("注册服务", True, f"实例ID: {registered.instance_id}")
    
    # 测试发现服务
    services = service_registry.discover_service(ServiceType.API_GATEWAY)
    log_test("发现服务", len(services) == 1)
    
    # 测试更新健康状态
    updated = service_registry.update_service_health(registered.instance_id, 0.3)
    log_test("更新健康状态到降级", updated)
    
    instance = service_registry.get_service_instance(registered.instance_id)
    log_test("验证状态为DEGRADED", instance.status == ServiceStatus.DEGRADED)
    
    # 测试更新健康状态到健康
    updated = service_registry.update_service_health(registered.instance_id, 0.8)
    log_test("更新健康状态到健康", updated)
    
    instance = service_registry.get_service_instance(registered.instance_id)
    log_test("验证状态为HEALTHY", instance.status == ServiceStatus.HEALTHY)
    
    # 测试注销服务
    unregistered = service_registry.unregister_service(registered.instance_id)
    log_test("注销服务", unregistered)
    
    services = service_registry.discover_service(ServiceType.API_GATEWAY)
    log_test("验证服务已注销", len(services) == 0)


def test_service_state_transitions():
    """测试服务状态转换（状态转换逻辑验证）"""
    print("\n=== 6. 服务状态转换测试 ===")
    
    service_registry = ServiceRegistry()
    
    instance = service_registry.register_service(
        "state-test-service",
        ServiceType.API_GATEWAY,
        "localhost",
        8000
    )
    
    # 测试从STARTING状态不应被健康检查改变
    service_registry.update_service_status(instance.instance_id, ServiceStatus.STARTING)
    service_registry.update_service_health(instance.instance_id, 0.3)
    instance = service_registry.get_service_instance(instance.instance_id)
    log_test("STARTING状态不受健康检查影响", instance.status == ServiceStatus.STARTING)
    
    # 测试从HEALTHY到DEGRADED
    service_registry.update_service_status(instance.instance_id, ServiceStatus.HEALTHY)
    service_registry.update_service_health(instance.instance_id, 0.3)
    instance = service_registry.get_service_instance(instance.instance_id)
    log_test("健康值低时变为DEGRADED", instance.status == ServiceStatus.DEGRADED)
    
    # 测试从DEGRADED到HEALTHY
    service_registry.update_service_health(instance.instance_id, 0.8)
    instance = service_registry.get_service_instance(instance.instance_id)
    log_test("健康值高时变为HEALTHY", instance.status == ServiceStatus.HEALTHY)


def test_load_balancer():
    """测试负载均衡器"""
    print("\n=== 7. 负载均衡器测试 ===")
    
    lb = LoadBalancer(strategy="round_robin")
    
    # 创建多个服务实例
    instances = []
    for i in range(3):
        instances.append(ServiceInstance(
            instance_id=str(uuid.uuid4()),
            service_name=f"lb-test-service",
            service_type=ServiceType.API_GATEWAY,
            version="1.0.0",
            host=f"host{i}",
            port=8000 + i,
            status=ServiceStatus.HEALTHY
        ))
    
    # 测试轮询
    selected_hosts = set()
    for i in range(6):
        selected = lb.select_instance(instances)
        selected_hosts.add(selected.host)
    
    log_test("轮询策略选择所有实例", len(selected_hosts) == 3)
    
    # 测试降级策略 - 所有实例都不健康
    for instance in instances:
        instance.status = ServiceStatus.ERROR
    
    selected = lb.select_instance(instances)
    log_test("降级到非健康实例", selected is not None)
    
    # 测试没有实例的情况
    selected = lb.select_instance([])
    log_test("没有实例时返回None", selected is None)


def test_load_balancer_degraded_fallback():
    """测试负载均衡器降级策略"""
    print("\n=== 8. 负载均衡器降级策略测试 ===")
    
    lb = LoadBalancer(strategy="round_robin")
    
    # 创建混合状态的实例
    instances = []
    
    # DEGRADED实例
    instances.append(ServiceInstance(
        instance_id=str(uuid.uuid4()),
        service_name="degraded-test",
        service_type=ServiceType.API_GATEWAY,
        version="1.0.0",
        host="degraded-host",
        port=8000,
        status=ServiceStatus.DEGRADED
    ))
    
    # ERROR实例
    instances.append(ServiceInstance(
        instance_id=str(uuid.uuid4()),
        service_name="degraded-test",
        service_type=ServiceType.API_GATEWAY,
        version="1.0.0",
        host="error-host",
        port=8001,
        status=ServiceStatus.ERROR
    ))
    
    selected = lb.select_instance(instances)
    log_test("降级到DEGRADED实例", selected is not None and selected.host == "degraded-host")


def test_business_scenario_complete():
    """测试完整的业务场景"""
    print("\n=== 9. 完整业务场景测试 ===")
    
    test_registry = TenantRegistry()
    service_registry = ServiceRegistry()
    lb = LoadBalancer()
    
    # 场景1: 新租户注册和服务创建
    owner_id = uuid.uuid4()
    tenant = test_registry.create_tenant(
        name="业务场景公司",
        slug="business-scenario",
        email="business@example.com",
        owner_id=owner_id,
        tier=TenantTier.BASIC
    )
    log_test("业务场景-创建租户", True)
    
    # 场景2: 为该租户创建多个服务实例
    for i in range(3):
        instance = service_registry.register_service(
            f"tenant-{tenant.tenant_id}-service",
            ServiceType.API_GATEWAY,
            "localhost",
            9000 + i
        )
    log_test("业务场景-创建服务实例", True)
    
    # 场景3: 发现并选择服务
    services = service_registry.discover_service(ServiceType.API_GATEWAY)
    selected = lb.select_instance(services)
    log_test("业务场景-选择服务", selected is not None)
    
    # 场景4: 记录服务使用量
    for i in range(10):
        test_registry.record_usage(tenant.tenant_id, "api_calls", 1)
        test_registry.record_usage(tenant.tenant_id, "ai_credits", 5)
    
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("业务场景-记录使用量", tenant.usage.total_api_calls == 10 and tenant.usage.ai_credits_used == 50)
    
    # 场景5: 检查配额
    can_proceed = test_registry.check_quota(tenant.tenant_id, "agents", 1)
    log_test("业务场景-检查配额", can_proceed)
    
    # 场景6: 升级租户
    test_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
    tenant = test_registry.get_tenant(tenant.tenant_id)
    log_test("业务场景-升级租户", tenant.tier == TenantTier.PRO)


def test_edge_cases():
    """测试边界情况"""
    print("\n=== 10. 边界情况测试 ===")
    
    test_registry = TenantRegistry()
    owner_id = uuid.uuid4()
    
    # 测试超长名称
    try:
        long_name = "x" * 300
        tenant = test_registry.create_tenant(
            name=long_name,
            slug="long-name-test",
            email="long@example.com",
            owner_id=owner_id
        )
        log_test("超长名称应该失败", False, "应该抛出异常但没有")
    except ValueError:
        log_test("超长名称正确抛出异常", True)
    
    # 测试无效邮箱
    try:
        tenant = test_registry.create_tenant(
            name="邮箱测试",
            slug="email-test",
            email="invalid-email",
            owner_id=owner_id
        )
        log_test("无效邮箱应该失败", False, "应该抛出异常但没有")
    except ValueError:
        log_test("无效邮箱正确抛出异常", True)
    
    # 测试重复slug
    tenant1 = test_registry.create_tenant(
        name="公司1",
        slug="duplicate-slug",
        email="company1@example.com",
        owner_id=owner_id
    )
    try:
        tenant2 = test_registry.create_tenant(
            name="公司2",
            slug="duplicate-slug",
            email="company2@example.com",
            owner_id=owner_id
        )
        log_test("重复slug应该失败", False, "应该抛出异常但没有")
    except ValueError:
        log_test("重复slug正确抛出异常", True)
    
    # 测试不存在的租户操作
    result = test_registry.update_tenant_status(uuid.uuid4(), TenantStatus.SUSPENDED)
    log_test("更新不存在的租户返回False", result is False)
    
    result = test_registry.delete_tenant(uuid.uuid4())
    log_test("删除不存在的租户返回False", result is False)
    
    result = test_registry.check_quota(uuid.uuid4(), "agents", 1)
    log_test("检查不存在租户的配额返回False", result is False)
    
    result = test_registry.record_usage(uuid.uuid4(), "agents", 1)
    log_test("记录不存在租户的使用量返回False", result is False)


def main():
    """主测试函数"""
    print("=" * 80)
    print("Phase 44: 标准化全流程测试")
    print("=" * 80)
    
    # 执行所有测试
    test_tenant_registry_basic()
    test_tenant_quota_management()
    test_all_tenant_tiers()
    test_tenant_concurrent_access()
    test_service_registry_basic()
    test_service_state_transitions()
    test_load_balancer()
    test_load_balancer_degraded_fallback()
    test_business_scenario_complete()
    test_edge_cases()
    
    # 打印测试结果汇总
    print("\n" + "=" * 80)
    print("测试结果汇总:")
    print(f"  总测试数: {test_results['total']}")
    print(f"  通过率: {test_results['passed']}/{test_results['total']} ({test_results['passed']/test_results['total']*100:.1f}%)")
    print(f"  失败数: {test_results['failed']}")
    print("=" * 80)
    
    if test_results['failed'] == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {test_results['failed']} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
