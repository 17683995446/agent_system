#!/usr/bin/env python3
"""
🚀 Phase 19: 端到端集成测试与真实Bug修复
通过真实的API调用和集成测试发现系统运行时Bug
"""

import requests
import time
import json
import random
import threading
from datetime import datetime, UTC
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from uuid import uuid4
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from multi_tenant.tenant_core import TenantRegistry, TenantTier, TenantStatus
    from distributed.distributed_core import ServiceRegistry, ServiceType, ServiceStatus
    print("✅ 核心模块导入成功")
    CORE_MODULES_AVAILABLE = True
except Exception as e:
    print(f"⚠️ 核心模块导入失败: {e}")
    CORE_MODULES_AVAILABLE = False


class BugSeverity(Enum):
    """Bug严重程度"""
    FATAL = auto()
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()


@dataclass
class Bug:
    """Bug数据类"""
    id: str
    category: str
    severity: BugSeverity
    description: str
    stack_trace: Optional[str] = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    fixed: bool = False
    fix_time: Optional[datetime] = None
    test_scenario: str = ""
    reproduce_steps: List[str] = field(default_factory=list)


class BugTracker:
    """Bug追踪器"""
    
    def __init__(self):
        self.bugs: List[Bug] = []
        self._lock = threading.Lock()
    
    def add_bug(self, bug: Bug) -> None:
        with self._lock:
            self.bugs.append(bug)
    
    def get_bugs_by_severity(self, severity: BugSeverity) -> List[Bug]:
        return [b for b in self.bugs if b.severity == severity]
    
    def get_total_bugs(self) -> int:
        return len(self.bugs)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_bugs": len(self.bugs),
            "bugs_by_severity": {
                s.name: len(self.get_bugs_by_severity(s))
                for s in BugSeverity
            },
            "bugs": [
                {
                    "id": b.id,
                    "category": b.category,
                    "severity": b.severity.name,
                    "description": b.description,
                    "discovered_at": b.discovered_at.isoformat(),
                    "fixed": b.fixed,
                    "test_scenario": b.test_scenario
                }
                for b in self.bugs
            ]
        }


class E2EIntegrationTest:
    """端到端集成测试"""
    
    def __init__(self):
        self.tracker = BugTracker()
        self.api_base_url = "http://localhost:8000"
        self.backend_available = False
        self.core_registry = None
        self.service_registry = None
    
    def check_backend_status(self) -> bool:
        """检查后端API是否可用"""
        try:
            response = requests.get(f"{self.api_base_url}/", timeout=2)
            if response.status_code == 200:
                self.backend_available = True
                print("✅ 后端API服务可用")
                return True
        except Exception as e:
            print(f"⚠️ 后端API不可用: {e}")
            print("  将使用核心模块直接测试")
        
        if CORE_MODULES_AVAILABLE:
            self.core_registry = TenantRegistry()
            self.service_registry = ServiceRegistry()
            print("✅ 使用核心模块直接测试")
            return True
        
        return False
    
    def test_scenario_1_core_module_tenant_operations(self):
        """场景1：核心模块租户操作测试"""
        print("\n" + "="*80)
        print("  🏢 场景1: 核心模块租户操作测试")
        print("="*80)
        
        if not self.core_registry:
            print("⚠️ 核心模块不可用，跳过此测试")
            return
        
        bugs = []
        
        # 测试1.1: 创建租户
        print("\n  📝 测试1.1: 批量创建租户 (100个)")
        errors = set()
        for i in range(100):
            try:
                tenant = self.core_registry.create_tenant(
                    name=f"test-tenant-{i:03d}",
                    slug=f"test-tenant-{i:03d}",
                    email=f"test{i}@example.com",
                    owner_id=str(uuid4()),
                    tier=TenantTier.STARTER
                )
                if (i + 1) % 25 == 0:
                    print(f"    ✅ 已创建: {i+1}/100")
            except Exception as e:
                error_key = str(e)[:80]
                if error_key not in errors:
                    errors.add(error_key)
                    bug = Bug(
                        id=f"E2E-BUG-001-{len(errors):02d}",
                        category="TENANT_CREATE",
                        severity=BugSeverity.HIGH,
                        description=f"租户创建失败: {str(e)}",
                        test_scenario="核心模块租户操作"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ Bug #{bug.id}: {bug.description[:60]}")
        
        # 测试1.2: 查询租户
        print("\n  🔍 测试1.2: 租户查询操作")
        all_tenants = self.core_registry.list_tenants()
        print(f"    当前租户总数: {len(all_tenants)}")
        
        if len(all_tenants) > 0:
            sample_tenant = all_tenants[0]
            try:
                found = self.core_registry.get_tenant(sample_tenant.tenant_id)
                print(f"    ✅ 查询成功: {found.name}")
            except Exception as e:
                bug = Bug(
                    id="E2E-BUG-002-01",
                    category="TENANT_QUERY",
                    severity=BugSeverity.CRITICAL,
                    description=f"租户查询失败: {str(e)}",
                    test_scenario="核心模块租户操作"
                )
                self.tracker.add_bug(bug)
                print(f"    ❌ Bug: {bug.description}")
        
        # 测试1.3: 更新租户层级
        print("\n  🔄 测试1.3: 更新租户层级")
        if len(all_tenants) > 0:
            target = all_tenants[0]
            try:
                success = self.core_registry.update_tier(target.tenant_id, TenantTier.PRO)
                if success:
                    print(f"    ✅ 层级更新成功")
                else:
                    bug = Bug(
                        id="E2E-BUG-003-01",
                        category="TENANT_UPDATE",
                        severity=BugSeverity.HIGH,
                        description="update_tier返回False",
                        test_scenario="核心模块租户操作"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ Bug: {bug.description}")
            except Exception as e:
                bug = Bug(
                    id="E2E-BUG-003-02",
                    category="TENANT_UPDATE",
                    severity=BugSeverity.CRITICAL,
                    description=f"更新租户失败: {str(e)}",
                    test_scenario="核心模块租户操作"
                )
                self.tracker.add_bug(bug)
                print(f"    ❌ Bug: {bug.description}")
        
        # 测试1.4: 删除租户
        print("\n  🗑️  测试1.4: 删除租户")
        if len(all_tenants) > 0:
            target = all_tenants[0]
            try:
                success = self.core_registry.delete_tenant(target.tenant_id)
                if success:
                    print(f"    ✅ 租户删除成功")
                else:
                    bug = Bug(
                        id="E2E-BUG-004-01",
                        category="TENANT_DELETE",
                        severity=BugSeverity.MEDIUM,
                        description="delete_tenant返回False",
                        test_scenario="核心模块租户操作"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ Bug: {bug.description}")
            except Exception as e:
                bug = Bug(
                    id="E2E-BUG-004-02",
                    category="TENANT_DELETE",
                    severity=BugSeverity.HIGH,
                    description=f"删除租户失败: {str(e)}",
                    test_scenario="核心模块租户操作"
                )
                self.tracker.add_bug(bug)
                print(f"    ❌ Bug: {bug.description}")
    
    def test_scenario_2_service_registry_operations(self):
        """场景2: 服务注册中心操作测试"""
        print("\n" + "="*80)
        print("  ⚡ 场景2: 服务注册中心操作测试")
        print("="*80)
        
        if not self.service_registry:
            print("⚠️ 服务注册中心不可用，跳过此测试")
            return
        
        # 测试2.1: 注册服务
        print("\n  📝 测试2.1: 批量注册服务 (50个)")
        errors = set()
        for i in range(50):
            try:
                service = self.service_registry.register_service(
                    service_name=f"test-service-{i:02d}",
                    service_type=random.choice(list(ServiceType)),
                    host="127.0.0.1",
                    port=8000 + i,
                    version="1.0.0"
                )
                if (i + 1) % 10 == 0:
                    print(f"    ✅ 已注册: {i+1}/50")
            except Exception as e:
                error_key = str(e)[:80]
                if error_key not in errors:
                    errors.add(error_key)
                    bug = Bug(
                        id=f"E2E-BUG-005-{len(errors):02d}",
                        category="SERVICE_REGISTER",
                        severity=BugSeverity.HIGH,
                        description=f"服务注册失败: {str(e)}",
                        test_scenario="服务注册中心操作"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ Bug #{bug.id}: {bug.description[:60]}")
        
        # 测试2.2: 更新服务健康状态
        print("\n  💚 测试2.2: 更新服务健康状态")
        all_services = []
        services_dict = self.service_registry._services
        for service_name, instances in services_dict.items():
            all_services.extend(instances)
        
        if len(all_services) > 0:
            sample_service = all_services[0]
            try:
                success = self.service_registry.update_service_health(
                    sample_service.instance_id, 
                    0.5
                )
                if success:
                    print(f"    ✅ 健康状态更新成功")
                else:
                    bug = Bug(
                        id="E2E-BUG-006-01",
                        category="SERVICE_HEALTH",
                        severity=BugSeverity.MEDIUM,
                        description="update_service_health返回False",
                        test_scenario="服务注册中心操作"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ Bug: {bug.description}")
            except Exception as e:
                bug = Bug(
                    id="E2E-BUG-006-02",
                    category="SERVICE_HEALTH",
                    severity=BugSeverity.CRITICAL,
                    description=f"更新服务健康状态失败: {str(e)}",
                    test_scenario="服务注册中心操作"
                )
                self.tracker.add_bug(bug)
                print(f"    ❌ Bug: {bug.description}")
    
    def test_scenario_3_concurrent_stress(self):
        """场景3: 并发压力测试"""
        print("\n" + "="*80)
        print("  🔥 场景3: 并发压力测试")
        print("="*80)
        
        if not self.core_registry:
            print("⚠️ 核心模块不可用，跳过此测试")
            return
        
        print("\n  ⚡ 启动100个并发线程")
        success_count = 0
        failure_count = 0
        lock = threading.Lock()
        
        def worker(worker_id: int):
            nonlocal success_count, failure_count
            local_success = 0
            local_fail = 0
            
            for _ in range(50):
                try:
                    # 随机操作
                    action = random.choice(["create", "query", "update"])
                    if action == "create":
                        self.core_registry.create_tenant(
                            name=f"concurrent-{worker_id}-{random.randint(1,10000)}",
                            slug=f"concurrent-{worker_id}-{random.randint(1,10000)}",
                            email=f"concurrent{worker_id}@{random.randint(1,10000)}.com",
                            owner_id=str(uuid4()),
                            tier=TenantTier.STARTER
                        )
                        local_success += 1
                    elif action == "query":
                        all_tenants = self.core_registry.list_tenants()
                        if len(all_tenants) > 0:
                            self.core_registry.get_tenant(all_tenants[0].tenant_id)
                            local_success += 1
                    elif action == "update":
                        all_tenants = self.core_registry.list_tenants()
                        if len(all_tenants) > 0:
                            self.core_registry.update_tier(
                                all_tenants[0].tenant_id,
                                random.choice(list(TenantTier))
                            )
                            local_success += 1
                except Exception:
                    local_fail += 1
            
            with lock:
                success_count += local_success
                failure_count += local_fail
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(worker, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()
        
        duration = time.time() - start_time
        
        print(f"\n  📊 并发测试结果:")
        print(f"    - 总操作: {success_count + failure_count}")
        print(f"    - 成功: {success_count}")
        print(f"    - 失败: {failure_count}")
        print(f"    - 耗时: {duration:.2f}秒")
        print(f"    - QPS: {(success_count + failure_count)/duration:.0f}")
        
        if failure_count > 100:
            bug = Bug(
                id="E2E-BUG-007-01",
                category="CONCURRENCY",
                severity=BugSeverity.CRITICAL,
                description=f"并发稳定性问题: {failure_count}次操作失败",
                test_scenario="并发压力测试"
            )
            self.tracker.add_bug(bug)
            print(f"\n  ⚠️ 检测到并发Bug: {bug.description}")
    
    def test_scenario_4_backend_api_endpoints(self):
        """场景4: 后端API端点测试"""
        print("\n" + "="*80)
        print("  🌐 场景4: 后端API端点测试")
        print("="*80)
        
        if not self.backend_available:
            print("⚠️ 后端API不可用，跳过此测试")
            return
        
        endpoints_to_test = [
            ("GET", "/", "健康检查"),
            ("GET", "/api/tenants", "获取租户列表"),
            ("POST", "/api/tenants", "创建租户"),
            ("GET", "/api/services", "获取服务列表"),
            ("POST", "/api/services/register", "注册服务"),
            ("GET", "/api/metrics/system", "获取系统指标"),
        ]
        
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)
                elif method == "POST":
                    if "tenants" in endpoint:
                        data = {
                            "name": "api-test-tenant",
                            "slug": f"api-test-{random.randint(1, 10000)}",
                            "email": f"apitest{random.randint(1, 10000)}@example.com",
                            "tier": "starter"
                        }
                        response = requests.post(
                            f"{self.api_base_url}{endpoint}", 
                            json=data, 
                            timeout=5
                        )
                    else:
                        data = {
                            "service_name": "api-test-service",
                            "service_type": "API_GATEWAY",
                            "version": "1.0.0",
                            "host": "127.0.0.1",
                            "port": random.randint(9000, 9999)
                        }
                        response = requests.post(
                            f"{self.api_base_url}{endpoint}",
                            json=data,
                            timeout=5
                        )
                
                if response.status_code < 400:
                    print(f"    ✅ {method} {endpoint} - {description}: {response.status_code}")
                else:
                    bug = Bug(
                        id=f"E2E-BUG-008-{len(self.tracker.bugs)+1:02d}",
                        category="API_ENDPOINT",
                        severity=BugSeverity.HIGH,
                        description=f"API端点错误: {method} {endpoint} 返回 {response.status_code}",
                        test_scenario="后端API端点测试"
                    )
                    self.tracker.add_bug(bug)
                    print(f"    ❌ {method} {endpoint}: {response.status_code}")
            except Exception as e:
                bug = Bug(
                    id=f"E2E-BUG-008-{len(self.tracker.bugs)+1:02d}",
                    category="API_ENDPOINT",
                    severity=BugSeverity.CRITICAL,
                    description=f"API端点异常: {method} {endpoint} - {str(e)}",
                    test_scenario="后端API端点测试"
                )
                self.tracker.add_bug(bug)
                print(f"    ❌ {method} {endpoint}: {str(e)[:50]}")
    
    def run_all_scenarios(self):
        """运行所有测试场景"""
        print("🚀 Phase 19: 端到端集成测试与Bug修复")
        print(f"⏰ 测试开始时间: {datetime.now(UTC).isoformat()}")
        
        # 步骤1: 检查后端状态
        self.check_backend_status()
        
        # 步骤2: 运行测试场景
        self.test_scenario_1_core_module_tenant_operations()
        self.test_scenario_2_service_registry_operations()
        self.test_scenario_3_concurrent_stress()
        self.test_scenario_4_backend_api_endpoints()
        
        # 步骤3: 生成总结报告
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*80)
        print("  📊 Phase 19 端到端集成测试 - 完整总结")
        print("="*80)
        
        total_bugs = self.tracker.get_total_bugs()
        bugs_by_severity = {
            s.name: len(self.tracker.get_bugs_by_severity(s))
            for s in BugSeverity
        }
        
        print(f"\n  Bug统计:")
        for severity, count in bugs_by_severity.items():
            icon = "💀" if severity == "FATAL" else "🔴" if severity == "CRITICAL" else "🟡" if severity == "HIGH" else "🟠" if severity == "MEDIUM" else "🟢"
            print(f"    {icon} {severity}: {count}")
        
        print(f"\n  总计Bug: {total_bugs}")
        
        if total_bugs > 0:
            print(f"\n  发现的Bug详情:")
            for bug in self.tracker.bugs:
                severity_icon = {
                    "FATAL": "💀",
                    "CRITICAL": "🔴",
                    "HIGH": "🟡",
                    "MEDIUM": "🟠",
                    "LOW": "🟢"
                }.get(bug.severity.name, "⚪")
                print(f"\n    {severity_icon} {bug.id}: {bug.description[:60]}...")
                print(f"       类别: {bug.category} | 场景: {bug.test_scenario}")
        else:
            print(f"\n  🎉 太棒了!没有发现任何Bug!")
        
        print("\n" + "="*80)
        
        # 保存结果
        report = {
            "test_time": datetime.now(UTC).isoformat(),
            "backend_available": self.backend_available,
            "bug_tracker": self.tracker.to_dict()
        }
        
        with open("phase19_e2e_test_results.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("  📄 结果已保存至: phase19_e2e_test_results.json")
        return total_bugs


from concurrent.futures import ThreadPoolExecutor, as_completed


def main():
    """主函数"""
    test = E2EIntegrationTest()
    test.run_all_scenarios()


if __name__ == "__main__":
    main()
