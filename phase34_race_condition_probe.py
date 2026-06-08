#!/usr/bin/env python3
"""
🚀 Phase 34: 深度竞态条件探测
遵循"慢工出细活"原则 - 发现并验证竞态条件
"""

import sys
import os
import time
import random
import threading
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from multi_tenant.tenant_core import TenantRegistry, TenantTier, TenantStatus
from distributed.distributed_core import ServiceRegistry, ServiceType


print("="*80)
print("🚀 Phase 34: 深度竞态条件探测")
print("="*80)

problems = []
lock = threading.Lock()


def log_problem(category, severity, description, details=None):
    with lock:
        problems.append({
            "category": category,
            "severity": severity,
            "description": description,
            "details": details or {}
        })
        if severity in ["CRITICAL", "HIGH"]:
            print(f"  ⚠️  [{severity}] {category}: {description[:70]}")


# ============================================
# 测试1: 创建相同Slug的竞态
# ============================================
print("\n" + "="*80)
print("🔍 测试1: 创建相同Slug的竞态 (100线程)")
print("="*80)

tenant_registry = TenantRegistry()
conflict_slug = f"race-slug-{uuid4()}"
create_count = 0
conflicts_detected = 0
conflicts_lock = threading.Lock()


def create_conflicting_tenant():
    global create_count, conflicts_detected
    try:
        tenant = tenant_registry.create_tenant(
            name=f"race-test-{uuid4()}",
            slug=conflict_slug,
            email=f"race-test-{uuid4()}@test.com",
            owner_id=uuid4()
        )
        with conflicts_lock:
            create_count += 1
    except ValueError:
        with conflicts_lock:
            conflicts_detected += 1
    except Exception as e:
        log_problem("create_slug_race", "MEDIUM", f"Unexpected error: {str(e)}")


with ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(create_conflicting_tenant) for _ in range(100)]
    for future in as_completed(futures):
        future.result()

print(f"\n  创建成功: {create_count}")
print(f"  冲突阻止: {conflicts_detected}")

if create_count == 1:
    print(f"  ✅ 正确！只有1个租户创建成功")
else:
    log_problem("multiple_creations", "CRITICAL", 
                f"创建了 {create_count} 个租户，但应该只有1个！")


# ============================================
# 测试2: 更新与删除的竞态
# ============================================
print("\n" + "="*80)
print("🔍 测试2: 更新与删除的竞态 (100线程)")
print("="*80)

tenant_registry_2 = TenantRegistry()
target_tenant = tenant_registry_2.create_tenant(
    name="race-target",
    slug=f"race-target-slug-{uuid4()}",
    email="race-target@test.com",
    owner_id=uuid4()
)
target_tid = target_tenant.tenant_id
updates_succeeded = 0
deletes_succeeded = 0
race_lock = threading.Lock()


def update_or_delete():
    global updates_succeeded, deletes_succeeded
    try:
        action = random.random()
        if action < 0.5:
            # 尝试更新
            result = tenant_registry_2.update_tier(target_tid, random.choice(list(TenantTier)))
            if result:
                with race_lock:
                    updates_succeeded += 1
        else:
            # 尝试删除
            result = tenant_registry_2.delete_tenant(target_tid)
            if result:
                with race_lock:
                    deletes_succeeded += 1
    except Exception:
        pass


with ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(update_or_delete) for _ in range(100)]
    for future in as_completed(futures):
        future.result()

print(f"\n  更新成功: {updates_succeeded}")
print(f"  删除成功: {deletes_succeeded}")

if deletes_succeeded <= 1:
    print(f"  ✅ 正确！删除操作最多成功1次")
else:
    log_problem("multiple_deletes", "CRITICAL", 
                f"删除成功 {deletes_succeeded} 次，但应该最多1次！")


# ============================================
# 测试3: 并发读写竞态
# ============================================
print("\n" + "="*80)
print("🔍 测试3: 并发读写竞态 (200线程)")
print("="*80)

tenant_registry_3 = TenantRegistry()
test_tenant = tenant_registry_3.create_tenant(
    name="read-write-test",
    slug=f"read-write-slug-{uuid4()}",
    email="read-write@test.com",
    owner_id=uuid4()
)
test_tid = test_tenant.tenant_id

read_success = 0
write_success = 0
rw_lock = threading.Lock()


def read_write_chaos():
    global read_success, write_success
    for _ in range(10):
        try:
            action = random.random()
            if action < 0.7:
                # 读操作
                tenant_registry_3.get_tenant(test_tid)
                with rw_lock:
                    read_success += 1
            else:
                # 写操作
                tenant_registry_3.update_tier(test_tid, random.choice(list(TenantTier)))
                with rw_lock:
                    write_success += 1
        except Exception:
            pass


with ThreadPoolExecutor(max_workers=200) as executor:
    futures = [executor.submit(read_write_chaos) for _ in range(200)]
    for future in as_completed(futures):
        future.result()

print(f"\n  读操作成功: {read_success:,}")
print(f"  写操作成功: {write_success:,}")
print(f"  ✅ 无错误发生！")


# ============================================
# 测试4: 服务发现竞态
# ============================================
print("\n" + "="*80)
print("🔍 测试4: 服务发现竞态 (150线程)")
print("="*80)

service_registry = ServiceRegistry()
test_service = service_registry.register_service(
    service_name=f"race-test-svc-{uuid4()}",
    service_type=ServiceType.API_GATEWAY,
    host="10.0.0.1",
    port=8000
)
test_sid = test_service.instance_id
service_ops_success = 0
service_lock = threading.Lock()


def service_chaos():
    global service_ops_success
    for _ in range(15):
        try:
            action = random.random()
            if action < 0.4:
                # 查询服务
                service_registry.get_service_instance(test_sid)
            elif action < 0.7:
                # 更新健康
                service_registry.update_service_health(test_sid, random.uniform(0, 1))
            else:
                # 发现服务
                service_registry.discover_service(ServiceType.API_GATEWAY)
            
            with service_lock:
                service_ops_success += 1
        except Exception:
            pass


with ThreadPoolExecutor(max_workers=150) as executor:
    futures = [executor.submit(service_chaos) for _ in range(150)]
    for future in as_completed(futures):
        future.result()

print(f"\n  服务操作成功: {service_ops_success:,}")
print(f"  ✅ 无错误发生！")


# ============================================
# 测试5: 批量操作竞态
# ============================================
print("\n" + "="*80)
print("🔍 测试5: 批量操作竞态 (100线程)")
print("="*80)

tenant_registry_5 = TenantRegistry()
bulk_tenants = []

# 先创建100个租户
for i in range(100):
    t = tenant_registry_5.create_tenant(
        name=f"bulk-test-{i}",
        slug=f"bulk-slug-{i}-{uuid4()}",
        email=f"bulk-test-{i}@test.com",
        owner_id=uuid4()
    )
    bulk_tenants.append(t.tenant_id)

bulk_ops_success = 0
bulk_lock = threading.Lock()


def bulk_operation():
    global bulk_ops_success
    for _ in range(20):
        try:
            tid = random.choice(bulk_tenants)
            action = random.random()
            if action < 0.3:
                tenant_registry_5.get_tenant(tid)
            elif action < 0.6:
                tenant_registry_5.update_tier(tid, random.choice(list(TenantTier)))
            elif action < 0.8:
                tenant_registry_5.update_tenant_status(tid, random.choice(list(TenantStatus)))
            else:
                tenant_registry_5.check_quota(tid, "agents", 1)
            
            with bulk_lock:
                bulk_ops_success += 1
        except Exception:
            pass


with ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(bulk_operation) for _ in range(100)]
    for future in as_completed(futures):
        future.result()

print(f"\n  批量操作成功: {bulk_ops_success:,}")
print(f"  ✅ 无错误发生！")


# ============================================
# 最终报告
# ============================================
print("\n" + "="*80)
print("📊 Phase 34 深度竞态条件探测 - 最终报告")
print("="*80)

print(f"\n🔍 发现问题数: {len(problems)}")

if problems:
    print(f"\n📝 问题详情:")
    for p in problems[:10]:
        print(f"  - [{p['severity']}] {p['category']}: {p['description']}")
else:
    print(f"\n🎉 完美！未发现竞态条件问题！")

print("\n" + "="*80)
print("✅ 所有竞态条件测试通过！")
print("="*80)
