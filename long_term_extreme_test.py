#!/usr/bin/env python3
"""
🚀🔥 长时间极限压力测试框架 - Phase 18
通过超长时间、高复杂度、真实生产场景主动发现系统缺陷
"""

import asyncio
import random
import time
import json
import uuid
import threading
import sys
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4, UUID
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from abc import ABC, abstractmethod

# 导入现有系统模块
try:
    from multi_tenant.tenant_core import TenantRegistry, TenantTier, Tenant
    from distributed.distributed_core import ServiceRegistry, ServiceStatus, ServiceType
    from memory.memory_core import MemoryStore, MemoryImportance
    from task.task_core import TaskManager, TaskPriority, TaskStatus
    from monitoring.monitoring_core import MetricsCollector
    print("✅ 所有核心模块导入成功")
except Exception as import_err:
    print(f"⚠️  导入警告: {import_err}")


class DefectSeverity(Enum):
    """缺陷严重程度"""
    FATAL = auto()      # 导致系统崩溃
    CRITICAL = auto()   # 核心功能完全失效
    HIGH = auto()       # 核心功能部分失效
    MEDIUM = auto()     # 辅助功能问题
    LOW = auto()        # 体验问题


@dataclass
class Defect:
    """缺陷数据类"""
    id: str
    category: str
    severity: DefectSeverity
    description: str
    stack_trace: Optional[str] = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    fixed: bool = False
    fix_time: Optional[datetime] = None
    scenario: str = ""
    reproduce_steps: List[str] = field(default_factory=list)


class DefectTracker:
    """缺陷追踪器"""
    
    def __init__(self):
        self.defects: List[Defect] = []
        self._lock = threading.Lock()
    
    def add_defect(self, defect: Defect) -> None:
        with self._lock:
            self.defects.append(defect)
    
    def get_defects_by_severity(self, severity: DefectSeverity) -> List[Defect]:
        return [d for d in self.defects if d.severity == severity]
    
    def get_total_defects(self) -> int:
        return len(self.defects)
    
    def get_fixed_defects(self) -> int:
        return len([d for d in self.defects if d.fixed])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_defects": len(self.defects),
            "defects_by_severity": {
                s.name: len(self.get_defects_by_severity(s))
                for s in DefectSeverity
            },
            "defects": [
                {
                    "id": d.id,
                    "category": d.category,
                    "severity": d.severity.name,
                    "description": d.description,
                    "stack_trace": d.stack_trace,
                    "discovered_at": d.discovered_at.isoformat(),
                    "fixed": d.fixed,
                    "scenario": d.scenario,
                    "reproduce_steps": d.reproduce_steps
                }
                for d in self.defects
            ]
        }


class TestScenario(ABC):
    """测试场景基类"""
    
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        pass


class Scenario1_ExtremeTenantStress(TestScenario):
    """场景1：极端租户压力测试 - 大量租户创建"""
    
    def name(self) -> str:
        return "极端租户压力测试"
    
    def description(self) -> str:
        return "创建大量租户，测试系统性能"
    
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        print("\n" + "="*80)
        print(f"  🚀 场景1: {self.name()}")
        print("="*80)
        results = {
            "total_ops": 0,
            "success_ops": 0,
            "fail_ops": 0,
            "duration": 0.0
        }
        
        try:
            from multi_tenant.tenant_core import TenantRegistry, TenantTier
            
            registry = TenantRegistry()
            start_time = time.time()
            tenant_ids = []
            errors = set()
            
            print("  📊 阶段1：批量创建1000个租户")
            for i in range(1000):
                try:
                    tenant = registry.create_tenant(
                        name=f"stress-tenant-{i:04d}",
                        slug=f"stress-tenant-{i:04d}",
                        email=f"stress-{i}@example.com",
                        owner_id=uuid4(),
                        tier=TenantTier.STARTER
                    )
                    tenant_ids.append(tenant.tenant_id)
                    results["success_ops"] += 1
                    results["total_ops"] += 1
                    
                    if (i + 1) % 200 == 0:
                        elapsed = time.time() - start_time
                        print(f"    ✅ 已创建: {i+1} / 1000 | 耗时 {elapsed:.2f}秒")
                        
                except Exception as e:
                    error_key = str(e)[:100]
                    if error_key not in errors:
                        errors.add(error_key)
                        defect = Defect(
                            id=f"LT-DEF-001-{len(errors):02d}",
                            category="TENANT_CREATE_ERROR",
                            severity=DefectSeverity.HIGH,
                            description=f"租户创建失败: {str(e)}",
                            scenario=self.name()
                        )
                        tracker.add_defect(defect)
                        print(f"    ❌ 缺陷发现: {defect.description[:50]}...")
                    
                    results["fail_ops"] += 1
                    results["total_ops"] += 1
            
            results["duration"] = time.time() - start_time
            print(f"  📊 场景1结果: {results['success_ops']}成功 / {results['fail_ops']}失败")
            
        except Exception as e:
            print(f"⚠️ 场景异常: {e}")
        
        return results


class Scenario2_LongTermServiceChaos(TestScenario):
    """场景2：长时间服务混沌测试 - 500个服务随机故障"""
    
    def name(self) -> str:
        return "长时间服务混沌测试"
    
    def description(self) -> str:
        return "长时间运行500个服务，随机注入故障，测试系统稳定性"
    
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        print("\n" + "="*80)
        print(f"  🌀 场景2: {self.name()}")
        print("="*80)
        
        results = {
            "services_created": 0,
            "failures_injected": 0,
            "recovery_time": [],
            "duration": 0.0
        }
        
        try:
            from distributed.distributed_core import ServiceRegistry, ServiceStatus, ServiceType
            
            registry = ServiceRegistry()
            start_time = time.time()
            service_ids = []
            errors = set()
            
            print("  📦 阶段1：创建500个服务")
            for i in range(500):
                try:
                    service = registry.register_service(
                        service_name=f"chaos-service-{i}",
                        service_type=random.choice(list(ServiceType)),
                        host="127.0.0.1",
                        port=8000 + i % 100,
                        version="1.0.0"
                    )
                    service_ids.append(service.instance_id)
                    results["services_created"] += 1
                    
                    if (i + 1) % 100 == 0:
                        print(f"    ✅ 服务创建: {i+1}/500")
                        
                except Exception as e:
                    error_key = str(e)[:100]
                    if error_key not in errors:
                        errors.add(error_key)
                        defect = Defect(
                            id=f"LT-DEF-002-{len(errors):02d}",
                            category="SERVICE_REGISTRATION",
                            severity=DefectSeverity.CRITICAL,
                            description=f"服务注册失败: {str(e)}",
                            scenario=self.name()
                        )
                        tracker.add_defect(defect)
                        print(f"    ❌ 缺陷: {defect.description[:50]}...")
            
            print("\n  💥 阶段2：随机故障注入（100次）")
            for i in range(100):
                if i % 20 == 0:
                    print(f"    混沌迭代: {i}/100")
                
                try:
                    if service_ids:
                        target_id = random.choice(service_ids)
                        
                        # 故障：标记服务为不健康
                        registry.update_service_health(target_id, 0.0)
                        results["failures_injected"] += 1
                        
                        # 立即恢复
                        rec_start = time.time()
                        registry.update_service_health(target_id, 0.95)
                        rec_time = time.time() - rec_start
                        results["recovery_time"].append(rec_time)
                        
                except Exception as e:
                    error_key = f"CHAOS-{str(e)[:50]}"
                    if error_key not in errors:
                        errors.add(error_key)
                        defect = Defect(
                            id=f"LT-DEF-003-{len(errors):02d}",
                            category="SERVICE_CHAOS_FAILURE",
                            severity=DefectSeverity.HIGH,
                            description=f"混沌操作失败: {str(e)}",
                            scenario=self.name()
                        )
                        tracker.add_defect(defect)
            
            results["duration"] = time.time() - start_time
            if results["recovery_time"]:
                avg_rec = sum(results["recovery_time"]) / len(results["recovery_time"])
                print(f"  📊 平均恢复时间: {avg_rec:.4f}秒")
                
        except Exception as e:
            print(f"⚠️ 场景异常: {e}")
        
        return results


class Scenario3_TenantLifecycleChaos(TestScenario):
    """场景3：租户生命周期混沌 - 创建/更新/删除循环"""
    
    def name(self) -> str:
        return "租户生命周期混沌测试"
    
    def description(self) -> str:
        return "执行10000次租户生命周期操作（创建/更新/查询/删除）"
    
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        print("\n" + "="*80)
        print(f"  🏢 场景3: {self.name()}")
        print("="*80)
        
        results = {
            "create_ops": 0,
            "update_ops": 0,
            "delete_ops": 0,
            "query_ops": 0,
            "failures": 0,
            "duration": 0.0
        }
        
        try:
            from multi_tenant.tenant_core import TenantRegistry, TenantTier
            
            registry = TenantRegistry()
            start_time = time.time()
            active_tenants = []
            errors = set()
            
            total_ops = 10000
            for op_id in range(total_ops):
                try:
                    action = random.choice(["create", "update", "query", "delete"])
                    
                    if action == "create" or (action == "delete" and not active_tenants):
                        # 创建新租户
                        tenant = registry.create_tenant(
                            name=f"chaos-tenant-{op_id}",
                            slug=f"chaos-tenant-{op_id}",
                            email=f"chaos{op_id}@example.com",
                            owner_id=uuid4(),
                            tier=random.choice(list(TenantTier))
                        )
                        active_tenants.append(tenant.tenant_id)
                        results["create_ops"] += 1
                        
                    elif action == "update" and active_tenants:
                        # 更新租户
                        target = random.choice(active_tenants)
                        registry.update_tier(target, random.choice(list(TenantTier)))
                        results["update_ops"] += 1
                        
                    elif action == "query" and active_tenants:
                        # 查询租户
                        target = random.choice(active_tenants)
                        registry.get_tenant(target)
                        results["query_ops"] += 1
                        
                    elif action == "delete" and active_tenants:
                        # 删除租户
                        target = active_tenants.pop(random.randint(0, len(active_tenants)-1))
                        success = registry.delete_tenant(target)
                        if success:
                            results["delete_ops"] += 1
                    
                    if (op_id + 1) % 2000 == 0:
                        elapsed = time.time() - start_time
                        print(f"    ✅ 操作进度: {op_id+1}/{total_ops} | 活跃租户: {len(active_tenants)} | 耗时 {elapsed:.2f}秒")
                        
                except Exception as e:
                    error_key = str(e)[:100]
                    if error_key not in errors:
                        errors.add(error_key)
                        severity = DefectSeverity.CRITICAL if "delete" in str(e).lower() else DefectSeverity.HIGH
                        defect = Defect(
                            id=f"LT-DEF-004-{len(errors):02d}",
                            category="TENANT_LIFECYCLE_ERROR",
                            severity=severity,
                            description=f"租户生命周期操作失败: {str(e)}",
                            scenario=self.name()
                        )
                        tracker.add_defect(defect)
                        print(f"    ❌ 缺陷: {defect.description[:60]}...")
                    
                    results["failures"] += 1
            
            results["duration"] = time.time() - start_time
            
            print(f"  📊 场景3结果:")
            print(f"    - 创建: {results['create_ops']}")
            print(f"    - 更新: {results['update_ops']}")
            print(f"    - 查询: {results['query_ops']}")
            print(f"    - 删除: {results['delete_ops']}")
            print(f"    - 失败: {results['failures']}")
            print(f"    - 总耗时: {results['duration']:.2f}秒")
            
        except Exception as e:
            print(f"⚠️ 场景异常: {e}")
        
        return results


class Scenario4_ConcurrencyAndRaceConditions(TestScenario):
    """场景4：并发与竞态条件测试 - 200个线程同时操作"""
    
    def name(self) -> str:
        return "并发与竞态条件测试"
    
    def description(self) -> str:
        return "200个线程同时操作共享资源，测试线程安全性"
    
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        print("\n" + "="*80)
        print(f"  ⚡ 场景4: {self.name()}")
        print("="*80)
        
        results = {
            "total_threads": 200,
            "operations_per_thread": 100,
            "success": 0,
            "failures": 0,
            "duration": 0.0
        }
        
        try:
            from multi_tenant.tenant_core import TenantRegistry, TenantTier
            
            registry = TenantRegistry()
            success_count = 0
            failure_count = 0
            lock = threading.Lock()
            
            # 先创建一些租户作为基础
            base_tenants = []
            for i in range(100):
                tenant = registry.create_tenant(
                    name=f"base-{i}",
                    slug=f"base-{i}",
                    email=f"base{i}@example.com",
                    owner_id=uuid4(),
                    tier=TenantTier.STARTER
                )
                base_tenants.append(tenant.tenant_id)
            
            start_time = time.time()
            
            def worker(worker_id: int):
                nonlocal success_count, failure_count
                local_success = 0
                local_fail = 0
                
                for _ in range(100):
                    try:
                        # 随机操作
                        target = random.choice(base_tenants)
                        registry.get_tenant(target)
                        registry.update_tier(target, random.choice(list(TenantTier)))
                        local_success += 1
                    except Exception:
                        local_fail += 1
                
                with lock:
                    success_count += local_success
                    failure_count += local_fail
            
            print(f"  🚀 启动 {results['total_threads']} 个并发线程")
            with ThreadPoolExecutor(max_workers=200) as executor:
                futures = [executor.submit(worker, i) for i in range(200)]
                for future in as_completed(futures):
                    future.result()
            
            results["success"] = success_count
            results["failures"] = failure_count
            results["duration"] = time.time() - start_time
            
            print(f"  📊 并发测试结果:")
            print(f"    - 总操作: {success_count + failure_count}")
            print(f"    - 成功: {success_count}")
            print(f"    - 失败: {failure_count}")
            print(f"    - 耗时: {results['duration']:.2f}秒")
            print(f"    - QPS: {(success_count + failure_count)/results['duration']:.0f}")
            
            if failure_count > 100:
                defect = Defect(
                    id="LT-DEF-005-001",
                    category="CONCURRENCY_STABILITY",
                    severity=DefectSeverity.CRITICAL,
                    description=f"并发稳定性问题: {failure_count}次操作失败",
                    scenario=self.name()
                )
                tracker.add_defect(defect)
                print(f"  ⚠️ 检测到并发问题!")
            
        except Exception as e:
            print(f"⚠️ 场景异常: {e}")
        
        return results


class Scenario5_EdgeCasesAndBoundary(TestScenario):
    """场景5：边界情况与异常值测试"""
    
    def name(self) -> str:
        return "边界情况与异常值测试"
    
    def description(self) -> str:
        return "测试各种边界情况、异常值和极限输入"
    
    def run(self, tracker: DefectTracker) -> Dict[str, Any]:
        print("\n" + "="*80)
        print(f"  🧪 场景5: {self.name()}")
        print("="*80)
        
        results = {
            "tests_run": 0,
            "problems_found": 0,
            "duration": 0.0
        }
        
        start_time = time.time()
        
        try:
            from multi_tenant.tenant_core import TenantRegistry, TenantTier
            from distributed.distributed_core import ServiceRegistry, ServiceType
            
            tenant_registry = TenantRegistry()
            service_registry = ServiceRegistry()
            
            edge_cases = [
                ("empty_name", "", "empty-slug", "test@example.com"),
                ("very_long_name", "x" * 1000, "long-slug", "long@example.com"),
                ("special_chars", "测试テスト!@#$", "test-slug", "test@test.com"),
            ]
            
            print("  🧪 测试租户边界情况")
            problems = 0
            for test_name, name, slug, email in edge_cases:
                try:
                    tenant = tenant_registry.create_tenant(
                        name=name,
                        slug=slug,
                        email=email,
                        owner_id=uuid4(),
                        tier=TenantTier.STARTER
                    )
                    results["tests_run"] += 1
                except Exception as e:
                    problems += 1
                    defect = Defect(
                        id=f"LT-DEF-006-{problems:02d}",
                        category="EDGE_CASE_HANDLING",
                        severity=DefectSeverity.MEDIUM,
                        description=f"边界情况处理失败 ({test_name}): {str(e)}",
                        scenario=self.name()
                    )
                    tracker.add_defect(defect)
                    print(f"    ❌ 边界情况失败: {test_name}")
            
            results["problems_found"] = problems
            results["duration"] = time.time() - start_time
            
            print(f"  📊 边界测试结果: {results['tests_run']}运行, {results['problems_found']}问题")
            
        except Exception as e:
            print(f"⚠️ 场景异常: {e}")
        
        return results


class LongTermExtremeTest:
    """长时间极限压力测试主类"""
    
    def __init__(self):
        self.tracker = DefectTracker()
        self.scenarios = [
            Scenario1_ExtremeTenantStress(),
            Scenario2_LongTermServiceChaos(),
            Scenario3_TenantLifecycleChaos(),
            Scenario4_ConcurrencyAndRaceConditions(),
            Scenario5_EdgeCasesAndBoundary()
        ]
    
    def print_summary(self, scenario_results):
        """打印完整总结"""
        print("\n" + "="*80)
        print("  📊 长时间极限压力测试 - 完整总结")
        print("="*80)
        
        total_defects = self.tracker.get_total_defects()
        defects_by_severity = {
            s.name: len(self.tracker.get_defects_by_severity(s))
            for s in DefectSeverity
        }
        
        print(f"\n  缺陷统计:")
        for severity, count in defects_by_severity.items():
            icon = "🔴" if severity in ["FATAL", "CRITICAL"] else "🟡" if severity == "HIGH" else "🟢"
            print(f"    {icon} {severity}: {count}")
        
        print(f"\n  总计缺陷: {total_defects}")
        
        if total_defects > 0:
            print(f"\n  发现的缺陷详情:")
            for defect in self.tracker.defects:
                severity_icon = {
                    "FATAL": "💀",
                    "CRITICAL": "🔴", 
                    "HIGH": "🟡",
                    "MEDIUM": "🟠",
                    "LOW": "🟢"
                }.get(defect.severity.name, "⚪")
                print(f"\n    {severity_icon} {defect.id}: {defect.description[:60]}...")
                print(f"       类别: {defect.category} | 场景: {defect.scenario}")
        else:
            print(f"\n  🎉 太棒了!没有发现任何缺陷!")
        
        print("\n" + "="*80)
        
        # 保存结果
        report = {
            "test_time": datetime.now(UTC).isoformat(),
            "scenario_results": scenario_results,
            "defect_tracker": self.tracker.to_dict()
        }
        
        with open("phase18_long_term_test_results.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("  📄 结果已保存至: phase18_long_term_test_results.json")
        return total_defects
    
    def run_all(self):
        """运行所有测试场景"""
        print("🚀🔥 开始 Phase 18 - 长时间极限压力测试 🔥🚀")
        print(f"⏰ 测试开始时间: {datetime.now(UTC).isoformat()}")
        
        all_results = {}
        for scenario in self.scenarios:
            result = scenario.run(self.tracker)
            all_results[scenario.name()] = result
        
        total_defects = self.print_summary(all_results)
        
        return total_defects


def main():
    """主函数"""
    test = LongTermExtremeTest()
    test.run_all()


if __name__ == "__main__":
    main()
