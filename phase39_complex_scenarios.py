#!/usr/bin/env python3
"""
Phase 39: 复杂场景深度测试
专注于复杂业务逻辑、状态机、数据流、事务处理、异常恢复
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import threading
import random
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import logging
import traceback
import json
from enum import Enum
from collections import defaultdict
import asyncio

from multi_tenant.tenant_core import (
    TenantRegistry, TenantTier, TenantStatus, TenantQuota, TenantSLA, TenantUsage
)
from distributed.distributed_core import (
    ServiceRegistry, ServiceType, ServiceStatus, ServiceInstance
)

# ================= 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'phase39_complex.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ================= 复杂业务场景枚举
class ScenarioType(Enum):
    """复杂业务场景类型"""
    # 基础场景
    SIMPLE_CREATE = "simple_create"
    SIMPLE_UPDATE = "simple_update"
    SIMPLE_DELETE = "simple_delete"
    SIMPLE_QUERY = "simple_query"
    
    # 状态机场景
    STATUS_TRANSITION = "status_transition"
    TIER_UPGRADE_CASCADE = "tier_upgrade_cascade"
    TIER_DOWNGRADE_CASCADE = "tier_downgrade_cascade"
    
    # 事务场景
    ATOMIC_BATCH_CREATE = "atomic_batch_create"
    ATOMIC_BATCH_UPDATE = "atomic_batch_update"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    
    # 配额场景
    QUOTA_EXCEED_CHECK = "quota_exceed_check"
    QUOTA_CALCULATION = "quota_calculation"
    QUOTA_RESET = "quota_reset"
    
    # 服务发现场景
    SERVICE_DISCOVERY_ROUND_ROBIN = "service_discovery_round_robin"
    SERVICE_HEALTH_CASCADE = "service_health_cascade"
    SERVICE_FAILOVER = "service_failover"
    
    # 异常场景
    CONCURRENT_CONFLICT = "concurrent_conflict"
    NETWORK_PARTITION = "network_partition"
    CASCADE_FAILURE = "cascade_failure"
    PARTIAL_FAILURE = "partial_failure"
    
    # 数据一致性场景
    EVENTUAL_CONSISTENCY = "eventual_consistency"
    STRONG_CONSISTENCY = "strong_consistency"
    READ_YOUR_WRITES_CONSISTENCY = "read_your_writes_consistency"
    
    # 复杂组合场景
    COMPLEX_WORKFLOW = "complex_workflow"
    MICROSERVICE_CHAIN = "microservice_chain"
    DISTRIBUTED_TRANSACTION = "distributed_transaction"


# ================= 测试结果数据结构
@dataclass
class ScenarioResult:
    scenario: str
    success: bool
    duration_ms: float
    steps: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplexTestMetrics:
    total_scenarios: int = 0
    successful_scenarios: int = 0
    failed_scenarios: int = 0
    total_operations: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    scenario_results: List[ScenarioResult] = field(default_factory=list)


# ================= 复杂场景测试器
class ComplexScenarioTester:
    """复杂场景深度测试器"""
    
    def __init__(self):
        self.tenant_registry = TenantRegistry()
        self.service_registry = ServiceRegistry()
        self.metrics = ComplexTestMetrics()
        self.tenants: Dict[str, Dict] = {}
        self.services: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        self.operation_log: List[Dict] = []
        
    def log_operation(self, scenario: str, step: str, data: Any = None, 
                      success: bool = True, error: str = None):
        """记录操作日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "step": step,
            "data": data,
            "success": success,
            "error": error
        }
        with self.lock:
            self.operation_log.append(entry)
            if not success and error:
                if error not in self.metrics.errors_by_type:
                    self.metrics.errors_by_type[error] = 0
                self.metrics.errors_by_type[error] += 1
        logger.debug(f"[{scenario}] {step}: {data if success else error}")
    
    # ================= 复杂场景1: 状态机转换
    def scenario_status_transition(self) -> ScenarioResult:
        """测试租户状态机转换"""
        result = ScenarioResult(scenario="STATUS_TRANSITION", success=True, duration_ms=0)
        start = time.time()
        
        try:
            # 创建租户 -> ACTIVE
            tenant = self.tenant_registry.create_tenant(
                name=f"StatusTest-{uuid4().hex[:6]}",
                slug=f"status-{uuid4().hex[:10]}",
                email=f"status{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.BASIC
            )
            result.steps.append({"step": "CREATE", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "CREATE", tenant.status.value)
            
            assert tenant.status == TenantStatus.ACTIVE, "初始状态应为ACTIVE"
            
            # ACTIVE -> SUSPENDED
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.SUSPENDED)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "SUSPEND", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "SUSPEND", tenant.status.value)
            assert tenant.status == TenantStatus.SUSPENDED
            
            # SUSPENDED -> ACTIVE (恢复)
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.ACTIVE)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "REACTIVATE", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "REACTIVATE", tenant.status.value)
            assert tenant.status == TenantStatus.ACTIVE
            
            # ACTIVE -> INACTIVE
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.INACTIVE)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "DEACTIVATE", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "DEACTIVATE", tenant.status.value)
            assert tenant.status == TenantStatus.INACTIVE
            
            # INACTIVE -> ACTIVE
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.ACTIVE)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "REACTIVATE", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "REACTIVATE", tenant.status.value)
            assert tenant.status == TenantStatus.ACTIVE
            
            # ACTIVE -> TRIAL
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.TRIAL)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "TRIAL", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "TRIAL", tenant.status.value)
            assert tenant.status == TenantStatus.TRIAL
            
            # TRIAL -> ARCHIVED
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.ARCHIVED)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({"step": "ARCHIVE", "status": tenant.status.value})
            self.log_operation("STATUS_TRANSITION", "ARCHIVE", tenant.status.value)
            assert tenant.status == TenantStatus.ARCHIVED
            
            # 清理
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({
                "type": type(e).__name__,
                "message": str(e),
                "trace": traceback.format_exc()
            })
            self.log_operation("STATUS_TRANSITION", "ERROR", None, success=False, error=str(e))
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景2: Tier升级级联
    def scenario_tier_upgrade_cascade(self) -> ScenarioResult:
        """测试租户层级升级级联效应"""
        result = ScenarioResult(scenario="TIER_UPGRADE_CASCADE", success=True, duration_ms=0)
        start = time.time()
        
        try:
            # 创建基础租户
            tenant = self.tenant_registry.create_tenant(
                name=f"TierUpgrade-{uuid4().hex[:6]}",
                slug=f"tierup-{uuid4().hex[:10]}",
                email=f"tierup{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.FREE
            )
            initial_quota = tenant.quota
            result.steps.append({
                "step": "CREATE_FREE",
                "tier": "FREE",
                "max_agents": initial_quota.max_agents,
                "max_storage": initial_quota.max_storage_mb
            })
            
            # FREE -> BASIC
            self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.BASIC)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({
                "step": "UPGRADE_BASIC",
                "tier": "BASIC",
                "max_agents": tenant.quota.max_agents,
                "max_storage": tenant.quota.max_storage_mb
            })
            assert tenant.quota.max_agents > initial_quota.max_agents
            
            # BASIC -> PRO
            self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({
                "step": "UPGRADE_PRO",
                "tier": "PRO",
                "max_agents": tenant.quota.max_agents,
                "max_storage": tenant.quota.max_storage_mb
            })
            assert tenant.quota.max_agents > initial_quota.max_agents * 5
            
            # PRO -> ENTERPRISE
            self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.ENTERPRISE)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({
                "step": "UPGRADE_ENTERPRISE",
                "tier": "ENTERPRISE",
                "max_agents": tenant.quota.max_agents,
                "max_storage": tenant.quota.max_storage_mb
            })
            assert tenant.quota.max_agents > initial_quota.max_agents * 10
            
            # 清理
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({"type": type(e).__name__, "message": str(e)})
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景3: 配额计算
    def scenario_quota_calculation(self) -> ScenarioResult:
        """测试复杂配额计算"""
        result = ScenarioResult(scenario="QUOTA_CALCULATION", success=True, duration_ms=0)
        start = time.time()
        
        try:
            tenant = self.tenant_registry.create_tenant(
                name=f"QuotaTest-{uuid4().hex[:6]}",
                slug=f"quota-{uuid4().hex[:10]}",
                email=f"quota{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.PRO
            )
            
            # 记录多次使用量
            for i in range(10):
                self.tenant_registry.record_usage(tenant.tenant_id, "agents", random.randint(1, 5))
                self.tenant_registry.record_usage(tenant.tenant_id, "api_calls", random.randint(10, 100))
            
            # 检查配额
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            quota_ok = self.tenant_registry.check_quota(tenant.tenant_id, "agents", 1)
            
            result.steps.append({
                "step": "CHECK_QUOTA",
                "usage": tenant.usage.agents_created,
                "quota": tenant.quota.max_agents,
                "quota_ok": quota_ok
            })
            
            # 超过配额检查
            self.tenant_registry.record_usage(tenant.tenant_id, "agents", tenant.quota.max_agents)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            quota_exceeded = tenant.usage.agents_created > tenant.quota.max_agents
            
            result.steps.append({
                "step": "EXCEED_QUOTA",
                "usage": tenant.usage.agents_created,
                "quota": tenant.quota.max_agents,
                "exceeded": quota_exceeded
            })
            
            # 清理
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({"type": type(e).__name__, "message": str(e)})
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景4: 服务健康级联
    def scenario_service_health_cascade(self) -> ScenarioResult:
        """测试服务健康状态级联效应"""
        result = ScenarioResult(scenario="SERVICE_HEALTH_CASCADE", success=True, duration_ms=0)
        start = time.time()
        
        try:
            # 注册多个服务实例
            service_instances = []
            for i in range(5):
                svc = self.service_registry.register_service(
                    f"cascade-svc-{uuid4().hex[:6]}",
                    random.choice(list(ServiceType)),
                    f"10.0.{i}.{random.randint(1,254)}",
                    8000 + i
                )
                service_instances.append(svc)
                result.steps.append({
                    "step": f"REGISTER_{i}",
                    "instance_id": svc.instance_id,
                    "health": svc.health_score
                })
            
            # 逐步降低健康值
            for i, svc in enumerate(service_instances[:3]):
                self.service_registry.update_service_health(svc.instance_id, 0.8 - i * 0.2)
                updated = self.service_registry.get_service_instance(svc.instance_id)
                result.steps.append({
                    "step": f"DEGRADE_{i}",
                    "health": updated.health_score,
                    "status": updated.status.value
                })
            
            # 检查服务发现
            service_type = service_instances[0].service_type
            discovered = self.service_registry.discover_service(service_type)
            result.steps.append({
                "step": "DISCOVER",
                "count": len(discovered),
                "healthy": sum(1 for s in discovered if s.status == ServiceStatus.HEALTHY)
            })
            
            # 清理
            for svc in service_instances:
                self.service_registry.unregister_service(svc.instance_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({"type": type(e).__name__, "message": str(e)})
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景5: 并发冲突
    def scenario_concurrent_conflict(self) -> ScenarioResult:
        """测试并发冲突场景"""
        result = ScenarioResult(scenario="CONCURRENT_CONFLICT", success=True, duration_ms=0)
        start = time.time()
        
        conflicts_detected = 0
        successful_updates = 0
        
        def concurrent_update(thread_id: int):
            nonlocal conflicts_detected, successful_updates
            try:
                # 每个线程更新同一个租户的状态
                for _ in range(10):
                    status = random.choice(list(TenantStatus))
                    try:
                        self.tenant_registry.update_tenant_status(
                            result.metrics.get("tenant_id"), status
                        )
                        successful_updates += 1
                    except Exception as e:
                        conflicts_detected += 1
            except Exception:
                conflicts_detected += 1
        
        try:
            # 创建一个租户
            tenant = self.tenant_registry.create_tenant(
                name=f"ConcurrentTest-{uuid4().hex[:6]}",
                slug=f"concurrent-{uuid4().hex[:10]}",
                email=f"concurrent{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.BASIC
            )
            result.metrics["tenant_id"] = str(tenant.tenant_id)
            
            # 启动多个并发线程
            threads = []
            for i in range(20):
                t = threading.Thread(target=concurrent_update, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            result.steps.append({
                "step": "CONCURRENT_UPDATES",
                "threads": 20,
                "successful": successful_updates,
                "conflicts": conflicts_detected
            })
            
            # 验证最终状态一致
            final_tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            result.steps.append({
                "step": "FINAL_STATE",
                "status": final_tenant.status.value,
                "consistent": final_tenant is not None
            })
            
            # 清理
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({"type": type(e).__name__, "message": str(e)})
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景6: 复杂工作流
    def scenario_complex_workflow(self) -> ScenarioResult:
        """测试复杂的多步骤工作流"""
        result = ScenarioResult(scenario="COMPLEX_WORKFLOW", success=True, duration_ms=0)
        start = time.time()
        
        try:
            workflow_steps = []
            
            # Step 1: 创建租户
            tenant = self.tenant_registry.create_tenant(
                name=f"Workflow-{uuid4().hex[:6]}",
                slug=f"workflow-{uuid4().hex[:10]}",
                email=f"workflow{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.PRO
            )
            workflow_steps.append({"step": "1_CREATE_TENANT", "id": str(tenant.tenant_id)})
            
            # Step 2: 注册多个服务
            services = []
            for i in range(3):
                svc = self.service_registry.register_service(
                    f"workflow-svc-{i}-{uuid4().hex[:6]}",
                    random.choice(list(ServiceType)),
                    f"192.168.{i}.1",
                    9000 + i
                )
                services.append(svc)
            workflow_steps.append({"step": "2_REGISTER_SERVICES", "count": len(services)})
            
            # Step 3: 更新租户状态
            self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.ACTIVE)
            workflow_steps.append({"step": "3_UPDATE_STATUS"})
            
            # Step 4: 记录使用量
            for i in range(5):
                self.tenant_registry.record_usage(tenant.tenant_id, "api_calls", 100)
            workflow_steps.append({"step": "4_RECORD_USAGE"})
            
            # Step 5: 更新健康状态
            for svc in services:
                self.service_registry.update_service_health(svc.instance_id, 0.95)
            workflow_steps.append({"step": "5_UPDATE_HEALTH"})
            
            # Step 6: 升级tier
            self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.ENTERPRISE)
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            workflow_steps.append({"step": "6_UPGRADE_TIER", "new_tier": tenant.tier.value})
            
            # Step 7: 再次记录使用量
            self.tenant_registry.record_usage(tenant.tenant_id, "agents", 10)
            workflow_steps.append({"step": "7_RECORD_USAGE"})
            
            # Step 8: 验证最终状态
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            services_count = len(self.service_registry.discover_service(services[0].service_type))
            workflow_steps.append({
                "step": "8_VERIFY",
                "tenant_status": tenant.status.value,
                "tenant_tier": tenant.tier.value,
                "services_count": services_count
            })
            
            result.steps = workflow_steps
            
            # Step 9: 清理
            for svc in services:
                self.service_registry.unregister_service(svc.instance_id)
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            workflow_steps.append({"step": "9_CLEANUP"})
            
        except Exception as e:
            result.success = False
            result.errors.append({
                "type": type(e).__name__,
                "message": str(e),
                "steps_completed": len(result.steps)
            })
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景7: 微服务链路
    def scenario_microservice_chain(self) -> ScenarioResult:
        """测试微服务调用链路"""
        result = ScenarioResult(scenario="MICROSERVICE_CHAIN", success=True, duration_ms=0)
        start = time.time()
        
        try:
            chain = []
            
            # 创建API Gateway
            gateway = self.service_registry.register_service(
                "api-gateway",
                ServiceType.API_GATEWAY,
                "10.0.0.1",
                80
            )
            chain.append({"service": "api-gateway", "type": gateway.service_type.value})
            
            # 创建认证服务
            auth = self.service_registry.register_service(
                "auth-service",
                ServiceType.AUTH_SERVICE,
                "10.0.0.2",
                8080
            )
            chain.append({"service": "auth-service", "type": auth.service_type.value})
            
            # 创建Agent服务
            agent = self.service_registry.register_service(
                "agent-service",
                ServiceType.AGENT_SERVICE,
                "10.0.0.3",
                8081
            )
            chain.append({"service": "agent-service", "type": agent.service_type.value})
            
            # 创建记忆服务
            memory = self.service_registry.register_service(
                "memory-service",
                ServiceType.MEMORY_SERVICE,
                "10.0.0.4",
                8082
            )
            chain.append({"service": "memory-service", "type": memory.service_type.value})
            
            # 验证链路
            result.steps.append({"step": "REGISTER_CHAIN", "length": len(chain)})
            
            # 查询每个服务
            for svc_info in chain:
                svc = self.service_registry.get_service_instance(
                    [g for g in [gateway, auth, agent, memory] 
                     if g.service_name == svc_info["service"]][0].instance_id
                )
                assert svc is not None
                result.steps.append({"step": f"QUERY_{svc.service_name}"})
            
            # 模拟健康检查链路
            for svc in [gateway, auth, agent, memory]:
                self.service_registry.update_service_health(svc.instance_id, random.uniform(0.8, 1.0))
            
            # 服务发现
            all_services = self.service_registry.discover_service(ServiceType.API_GATEWAY)
            result.steps.append({"step": "DISCOVER", "count": len(all_services)})
            
            # 清理
            for svc in [gateway, auth, agent, memory]:
                self.service_registry.unregister_service(svc.instance_id)
            
        except Exception as e:
            result.success = False
            result.errors.append({"type": type(e).__name__, "message": str(e)})
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 复杂场景8: 分布式事务模拟
    def scenario_distributed_transaction(self) -> ScenarioResult:
        """测试分布式事务场景"""
        result = ScenarioResult(scenario="DISTRIBUTED_TRANSACTION", success=True, duration_ms=0)
        start = time.time()
        
        try:
            transaction_log = []
            
            # Phase 1: 预创建资源
            tenant = self.tenant_registry.create_tenant(
                name=f"DistTx-{uuid4().hex[:6]}",
                slug=f"disttx-{uuid4().hex[:10]}",
                email=f"disttx{uuid4().hex[:8]}@test.com",
                owner_id=uuid4(),
                tier=TenantTier.PRO
            )
            transaction_log.append({"phase": "1_PREPARE", "tenant_id": str(tenant.tenant_id)})
            
            # Phase 2: 注册关联服务
            services = []
            for i in range(3):
                svc = self.service_registry.register_service(
                    f"disttx-svc-{i}",
                    ServiceType.API_GATEWAY,
                    f"10.0.{i}.100",
                    8000 + i
                )
                services.append(svc)
            transaction_log.append({"phase": "2_REGISTER_SERVICES", "count": len(services)})
            
            # Phase 3: 验证所有资源
            tenant = self.tenant_registry.get_tenant(tenant.tenant_id)
            assert tenant is not None
            for svc in services:
                retrieved = self.service_registry.get_service_instance(svc.instance_id)
                assert retrieved is not None
            transaction_log.append({"phase": "3_VERIFY_RESOURCES"})
            
            # Phase 4: 记录使用量
            for _ in range(5):
                self.tenant_registry.record_usage(tenant.tenant_id, "api_calls", 100)
            transaction_log.append({"phase": "4_RECORD_USAGE"})
            
            # Phase 5: 更新所有服务健康
            for svc in services:
                self.service_registry.update_service_health(svc.instance_id, 0.95)
            transaction_log.append({"phase": "5_UPDATE_HEALTH"})
            
            # Phase 6: 提交事务（清理）
            for svc in services:
                self.service_registry.unregister_service(svc.instance_id)
            self.tenant_registry.delete_tenant(tenant.tenant_id)
            transaction_log.append({"phase": "6_COMMIT"})
            
            result.steps = transaction_log
            
        except Exception as e:
            result.success = False
            result.errors.append({
                "type": type(e).__name__,
                "message": str(e),
                "phase": transaction_log[-1]["phase"] if transaction_log else "UNKNOWN"
            })
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    # ================= 运行所有复杂场景
    def run_all_scenarios(self, iterations: int = 10) -> ComplexTestMetrics:
        """运行所有复杂场景测试"""
        print("="*80)
        print("🚀 Phase 39: 复杂场景深度测试")
        print("="*80)
        print(f"每个场景运行 {iterations} 次")
        print("="*80)
        
        scenarios = [
            self.scenario_status_transition,
            self.scenario_tier_upgrade_cascade,
            self.scenario_quota_calculation,
            self.scenario_service_health_cascade,
            self.scenario_concurrent_conflict,
            self.scenario_complex_workflow,
            self.scenario_microservice_chain,
            self.scenario_distributed_transaction,
        ]
        
        for iteration in range(iterations):
            print(f"\n{'='*80}")
            print(f"📊 迭代 {iteration + 1}/{iterations}")
            print(f"{'='*80}")
            
            for scenario_func in scenarios:
                scenario_name = scenario_func.__name__.replace("scenario_", "").replace("_", " ").upper()
                print(f"\n🔄 运行场景: {scenario_name}...")
                
                result = scenario_func()
                self.metrics.scenario_results.append(result)
                self.metrics.total_scenarios += 1
                
                if result.success:
                    self.metrics.successful_scenarios += 1
                    print(f"  ✅ 成功 (耗时: {result.duration_ms:.2f}ms)")
                    print(f"     步骤数: {len(result.steps)}")
                else:
                    self.metrics.failed_scenarios += 1
                    print(f"  ❌ 失败 (耗时: {result.duration_ms:.2f}ms)")
                    print(f"     错误: {result.errors}")
        
        return self.metrics
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("📊 Phase 39: 复杂场景测试结果摘要")
        print("="*80)
        print(f"总场景数: {self.metrics.total_scenarios}")
        print(f"成功: {self.metrics.successful_scenarios}")
        print(f"失败: {self.metrics.failed_scenarios}")
        
        success_rate = self.metrics.successful_scenarios / self.metrics.total_scenarios * 100
        print(f"成功率: {success_rate:.2f}%")
        
        if self.metrics.errors_by_type:
            print(f"\n错误类型统计:")
            for error_type, count in self.metrics.errors_by_type.items():
                print(f"  - {error_type}: {count}")
        
        print(f"\n总操作日志: {len(self.operation_log)}")
        
        print("\n" + "="*80)
        
        # 保存详细日志
        output_file = os.path.join(os.path.dirname(__file__), "phase39_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_scenarios": self.metrics.total_scenarios,
                "successful": self.metrics.successful_scenarios,
                "failed": self.metrics.failed_scenarios,
                "success_rate": success_rate,
                "errors_by_type": self.metrics.errors_by_type,
                "scenario_results": [
                    {
                        "scenario": r.scenario,
                        "success": r.success,
                        "duration_ms": r.duration_ms,
                        "steps_count": len(r.steps),
                        "errors": r.errors
                    }
                    for r in self.metrics.scenario_results
                ]
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 结果已保存: {output_file}")
        print("="*80)


def main():
    tester = ComplexScenarioTester()
    tester.run_all_scenarios(iterations=5)
    tester.print_summary()


if __name__ == "__main__":
    main()
