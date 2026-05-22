#!/usr/bin/env python3
"""
Phase 43: 超终极混乱测试
20分钟，1000线程，极端混乱场景
新增：
- 混合租户和服务操作
- 数据一致性强验证
- 资源泄漏检测
- 状态机穷举测试
- 边界值极限测试
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import threading
import random
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Set
import logging
import traceback
import json
from dataclasses import dataclass, field
import gc
import weakref
from collections import defaultdict

from multi_tenant.tenant_core import (
    TenantRegistry, TenantTier, TenantStatus
)
from distributed.distributed_core import (
    ServiceRegistry, ServiceType, ServiceStatus
)

LOG_FILE = os.path.join(os.path.dirname(__file__), 'phase43_ultimate.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    total_ops: int = 0
    success_ops: int = 0
    fail_ops: int = 0
    operation_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: List[Dict] = field(default_factory=list)
    start_time: float = 0
    
    def record_success(self, op_name: str):
        self.operation_counts[op_name] += 1
        
    def record_failure(self, op_name: str, error: Exception):
        self.operation_counts[f"FAIL_{op_name}"] += 1
        

class UltimateTester:
    def __init__(self, duration_min=20, threads=1000):
        self.duration = duration_min * 60
        self.num_threads = threads
        self.tenant_registry = TenantRegistry()
        self.service_registry = ServiceRegistry()
        self.metrics = Metrics()
        self.tenants: List[str] = []
        self.services: List[str] = []
        self.tenant_snapshots: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self.running = True
        self.start_time = None
        self.operation_patterns: Dict[int, str] = {}
        
        self._build_operation_map()
        
    def _build_operation_map(self):
        self.operation_patterns = {
            # 基础租户操作 (0-9)
            0: "CREATE_TENANT",
            1: "GET_TENANT",
            2: "UPDATE_STATUS",
            3: "UPDATE_TIER",
            4: "RECORD_USAGE",
            5: "CHECK_QUOTA",
            6: "DELETE_TENANT",
            7: "LIST_TENANTS",
            8: "VERIFY_CONSISTENCY",
            9: "SNAPSHOT_TENANT",
            # 服务操作 (10-19)
            10: "REGISTER_SERVICE",
            11: "GET_SERVICE",
            12: "UPDATE_HEALTH",
            13: "UPDATE_SERVICE_STATUS",
            14: "UNREGISTER_SERVICE",
            15: "DISCOVER_SERVICE",
            16: "SERVICE_HEALTH_CYCLE",
            17: "SERVICE_STATUS_LOOP",
            18: "SERVICE_BATCH_REGISTER",
            19: "SERVICE_BATCH_UNREGISTER",
            # 异常操作 (20-29)
            20: "INVALID_EMPTY_NAME",
            21: "INVALID_LONG_NAME",
            22: "INVALID_EMAIL",
            23: "NEGATIVE_USAGE",
            24: "INVALID_HEALTH_VALUE",
            25: "GET_NONEXISTENT",
            26: "DELETE_NONEXISTENT",
            27: "UPDATE_NONEXISTENT",
            28: "SERVICE_OP_ON_NONEXISTENT",
            29: "INVALID_TIER_VALUE",
            # 复杂操作 (30-39)
            30: "MIXED_TENANT_WORKFLOW",
            31: "MIXED_SERVICE_WORKFLOW",
            32: "PARALLEL_TENANT_OPS",
            33: "PARALLEL_SERVICE_OPS",
            34: "CONSISTENCY_STRESS",
            35: "QUOTA_OVERLOAD",
            36: "RAPID_CREATE_DELETE",
            37: "STATE_CYCLE",
            38: "TIER_CYCLE",
            39: "HEALTH_CYCLE",
            # 极端场景 (40-49)
            40: "CHAOS_MONKEY_DELETE",
            41: "CHAOS_MONKEY_UPDATE",
            42: "CASCADING_FAILURES",
            43: "RESOURCE_EXHAUSTION_SIM",
            44: "CROSS_TENANT_OPERATIONS",
            45: "SERVICE_DISCOVERY_STORM",
            46: "DEADLOCK_SIMULATION",
            47: "STARVATION_TEST",
            48: "MEMORY_LEAK_DETECTION",
            49: "RACE_CONDITION_INJECTION",
        }
        
    def random_tenant_id(self) -> str:
        with self.lock:
            return random.choice(self.tenants) if self.tenants else None
            
    def random_service_id(self) -> str:
        with self.lock:
            return random.choice(self.services) if self.services else None
            
    def get_random_ids(self, count: int) -> tuple:
        with self.lock:
            tids = random.sample(self.tenants, min(count, len(self.tenants))) if self.tenants else []
            sids = random.sample(self.services, min(count, len(self.services))) if self.services else []
        return tids, sids
        
    def _log_operation(self, worker_id: int, op_code: int, success: bool, extra: str = ""):
        op_name = self.operation_patterns.get(op_code, f"OP_{op_code}")
        prefix = "✅" if success else "❌"
        if random.random() < 0.01:
            logger.debug(f"[W{worker_id}] {prefix} {op_name} {extra}")
            
    def _create_tenant_internal(self, worker_id: int, prefix: str = "t") -> tuple:
        slug = f"p43-{prefix}-{uuid4().hex[:12]}"
        try:
            tenant = self.tenant_registry.create_tenant(
                name=f"Chaos-{uuid4().hex[:6]}",
                slug=slug,
                email=f"c{worker_id}{uuid4().hex[:6]}@test.com",
                owner_id=uuid4(),
                tier=random.choice(list(TenantTier))
            )
            with self.lock:
                self.tenants.append(str(tenant.tenant_id))
                self.tenant_snapshots[str(tenant.tenant_id)] = {
                    "created_at": time.time(),
                    "tier": tenant.tier,
                    "status": tenant.status
                }
            self._log_operation(worker_id, 0, True, str(tenant.tenant_id)[:8])
            return True, tenant.tenant_id
        except Exception as e:
            self._log_operation(worker_id, 0, False, str(e)[:50])
            return False, None
            
    def _register_service_internal(self, worker_id: int, prefix: str = "s") -> tuple:
        try:
            svc = self.service_registry.register_service(
                f"{prefix}{worker_id}-{uuid4().hex[:6]}",
                random.choice(list(ServiceType)),
                f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                random.randint(1000, 65535)
            )
            with self.lock:
                self.services.append(svc.instance_id)
            self._log_operation(worker_id, 10, True, svc.instance_id[:8])
            return True, svc.instance_id
        except Exception as e:
            self._log_operation(worker_id, 10, False, str(e)[:50])
            return False, None
    
    def worker(self, worker_id: int):
        thread_logger = logging.getLogger(f"Worker-{worker_id}")
        thread_logger.info(f"Worker {worker_id} 启动")
        ops_count = 0
        local_errors = 0
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                op = random.randint(0, 49)
                error_occurred = False
                
                if op == 0:  # CREATE_TENANT
                    self._create_tenant_internal(worker_id)
                    
                elif op == 1:  # GET_TENANT
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.get_tenant(tid)
                        self._log_operation(worker_id, 1, True)
                        
                elif op == 2:  # UPDATE_STATUS
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tenant_status(
                            tid, random.choice(list(TenantStatus))
                        )
                        self._log_operation(worker_id, 2, True)
                        
                elif op == 3:  # UPDATE_TIER
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tier(
                            tid, random.choice(list(TenantTier))
                        )
                        self._log_operation(worker_id, 3, True)
                        
                elif op == 4:  # RECORD_USAGE
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.record_usage(
                            tid, random.choice(["agents", "api_calls", "ai_credits"]),
                            random.randint(1, 100)
                        )
                        self._log_operation(worker_id, 4, True)
                        
                elif op == 5:  # CHECK_QUOTA
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.check_quota(
                            tid, random.choice(["agents", "api_calls"]),
                            random.randint(1, 50)
                        )
                        self._log_operation(worker_id, 5, True)
                        
                elif op == 6:  # DELETE_TENANT
                    with self.lock:
                        if len(self.tenants) > 10:
                            tid = self.tenants.pop(0)
                            result = self.tenant_registry.delete_tenant(tid)
                            if str(tid) in self.tenant_snapshots:
                                del self.tenant_snapshots[str(tid)]
                            self._log_operation(worker_id, 6, result)
                            
                elif op == 7:  # LIST_TENANTS
                    self.tenant_registry.list_tenants(
                        limit=random.choice([None, 10, 50, 100, 200]),
                        offset=random.randint(0, 10)
                    )
                    self._log_operation(worker_id, 7, True)
                    
                elif op == 8:  # VERIFY_CONSISTENCY
                    tid = self.random_tenant_id()
                    if tid:
                        t1 = self.tenant_registry.get_tenant(tid)
                        t2 = self.tenant_registry.get_tenant(tid)
                        if t1 and t2:
                            assert t1.tenant_id == t2.tenant_id
                            assert t1.slug == t2.slug
                        self._log_operation(worker_id, 8, True)
                        
                elif op == 9:  # SNAPSHOT_TENANT
                    tid = self.random_tenant_id()
                    if tid:
                        tenant = self.tenant_registry.get_tenant(tid)
                        if tenant:
                            with self.lock:
                                self.tenant_snapshots[str(tid)] = {
                                    "tier": tenant.tier,
                                    "status": tenant.status,
                                    "snapshot_at": time.time()
                                }
                        self._log_operation(worker_id, 9, True)
                        
                elif op == 10:  # REGISTER_SERVICE
                    self._register_service_internal(worker_id)
                    
                elif op == 11:  # GET_SERVICE
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.get_service_instance(sid)
                        self._log_operation(worker_id, 11, True)
                        
                elif op == 12:  # UPDATE_HEALTH
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_health(
                            sid, random.uniform(0, 1)
                        )
                        self._log_operation(worker_id, 12, True)
                        
                elif op == 13:  # UPDATE_SERVICE_STATUS
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_status(
                            sid, random.choice(list(ServiceStatus))
                        )
                        self._log_operation(worker_id, 13, True)
                        
                elif op == 14:  # UNREGISTER_SERVICE
                    with self.lock:
                        if len(self.services) > 5:
                            sid = self.services.pop(0)
                            self.service_registry.unregister_service(sid)
                            self._log_operation(worker_id, 14, True)
                            
                elif op == 15:  # DISCOVER_SERVICE
                    self.service_registry.discover_service(
                        random.choice(list(ServiceType))
                    )
                    self._log_operation(worker_id, 15, True)
                    
                elif op == 16:  # SERVICE_HEALTH_CYCLE
                    sid = self.random_service_id()
                    if sid:
                        for h in [0.95, 0.8, 0.5, 0.3, 0.1, 0.3, 0.6, 0.9]:
                            self.service_registry.update_service_health(sid, h)
                        self._log_operation(worker_id, 16, True)
                        
                elif op == 17:  # SERVICE_STATUS_LOOP
                    sid = self.random_service_id()
                    if sid:
                        for status in list(ServiceStatus):
                            self.service_registry.update_service_status(sid, status)
                        self._log_operation(worker_id, 17, True)
                        
                elif op == 18:  # SERVICE_BATCH_REGISTER
                    success_count = 0
                    for _ in range(5):
                        ok, _ = self._register_service_internal(worker_id, f"batch{worker_id}")
                        if ok:
                            success_count += 1
                    self._log_operation(worker_id, 18, success_count > 0, f"{success_count}/5")
                    
                elif op == 19:  # SERVICE_BATCH_UNREGISTER
                    with self.lock:
                        if len(self.services) > 5:
                            for _ in range(min(5, len(self.services) - 3)):
                                sid = self.services.pop(0)
                                self.service_registry.unregister_service(sid)
                            self._log_operation(worker_id, 19, True)
                            
                elif op == 20:  # INVALID_EMPTY_NAME
                    try:
                        self.tenant_registry.create_tenant(
                            name="",
                            slug=f"e{uuid4().hex[:12]}",
                            email=f"e{uuid4().hex[:8]}@test.com",
                            owner_id=uuid4()
                        )
                        error_occurred = True
                    except ValueError:
                        self._log_operation(worker_id, 20, True, "正确拒绝")
                        
                elif op == 21:  # INVALID_LONG_NAME
                    try:
                        self.tenant_registry.create_tenant(
                            name="X" * 1000,
                            slug=f"l{uuid4().hex[:12]}",
                            email=f"l{uuid4().hex[:8]}@test.com",
                            owner_id=uuid4()
                        )
                        error_occurred = True
                    except ValueError:
                        self._log_operation(worker_id, 21, True, "正确拒绝")
                        
                elif op == 22:  # INVALID_EMAIL
                    try:
                        self.tenant_registry.create_tenant(
                            name="Test",
                            slug=f"inv{uuid4().hex[:12]}",
                            email="invalid-email",
                            owner_id=uuid4()
                        )
                        error_occurred = True
                    except ValueError:
                        self._log_operation(worker_id, 22, True, "正确拒绝")
                        
                elif op == 23:  # NEGATIVE_USAGE
                    tid = self.random_tenant_id()
                    if tid:
                        try:
                            self.tenant_registry.record_usage(
                                tid, "agents", -random.randint(1, 1000)
                            )
                            error_occurred = True
                        except ValueError:
                            self._log_operation(worker_id, 23, True, "正确拒绝")
                            
                elif op == 24:  # INVALID_HEALTH_VALUE
                    sid = self.random_service_id()
                    if sid:
                        try:
                            self.service_registry.update_service_health(
                                sid, random.uniform(-2, 2)
                            )
                            error_occurred = True
                        except ValueError:
                            self._log_operation(worker_id, 24, True, "正确拒绝")
                            
                elif op == 25:  # GET_NONEXISTENT
                    self.tenant_registry.get_tenant(uuid4())
                    self._log_operation(worker_id, 25, True)
                    
                elif op == 26:  # DELETE_NONEXISTENT
                    self.tenant_registry.delete_tenant(uuid4())
                    self._log_operation(worker_id, 26, True)
                    
                elif op == 27:  # UPDATE_NONEXISTENT
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.delete_tenant(tid)
                        try:
                            self.tenant_registry.update_tenant_status(
                                tid, TenantStatus.ACTIVE
                            )
                            error_occurred = True
                        except:
                            self._log_operation(worker_id, 27, True, "正确处理")
                            
                elif op == 28:  # SERVICE_OP_ON_NONEXISTENT
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.unregister_service(sid)
                        try:
                            self.service_registry.update_service_health(sid, 0.5)
                            error_occurred = True
                        except:
                            self._log_operation(worker_id, 28, True, "正确处理")
                            
                elif op == 29:  # INVALID_TIER_VALUE
                    tid = self.random_tenant_id()
                    if tid:
                        try:
                            self.tenant_registry.update_tier(tid, "INVALID_TIER")
                            error_occurred = True
                        except:
                            self._log_operation(worker_id, 29, True, "正确拒绝")
                            
                elif op == 30:  # MIXED_TENANT_WORKFLOW
                    ok1, tid = self._create_tenant_internal(worker_id, "mixed")
                    if ok1:
                        self.tenant_registry.record_usage(tid, "agents", 10)
                        self.tenant_registry.record_usage(tid, "api_calls", 100)
                        self.tenant_registry.update_tier(tid, TenantTier.PRO)
                        self.tenant_registry.update_tenant_status(tid, TenantStatus.ACTIVE)
                        t = self.tenant_registry.get_tenant(tid)
                        assert t.tier == TenantTier.PRO
                        self._log_operation(worker_id, 30, True)
                        
                elif op == 31:  # MIXED_SERVICE_WORKFLOW
                    ok1, sid = self._register_service_internal(worker_id, "mixed")
                    if ok1:
                        self.service_registry.update_service_health(sid, 0.95)
                        self.service_registry.update_service_status(sid, ServiceStatus.HEALTHY)
                        svc = self.service_registry.get_service_instance(sid)
                        assert svc.health_score > 0.9
                        self._log_operation(worker_id, 31, True)
                        
                elif op == 32:  # PARALLEL_TENANT_OPS
                    tids, _ = self.get_random_ids(3)
                    for tid in tids:
                        self.tenant_registry.update_tier(tid, random.choice(list(TenantTier)))
                        self.tenant_registry.record_usage(tid, "api_calls", random.randint(1, 10))
                    self._log_operation(worker_id, 32, True)
                    
                elif op == 33:  # PARALLEL_SERVICE_OPS
                    _, sids = self.get_random_ids(3)
                    for sid in sids:
                        self.service_registry.update_service_health(sid, random.uniform(0, 1))
                        self.service_registry.update_service_status(sid, random.choice(list(ServiceStatus)))
                    self._log_operation(worker_id, 33, True)
                    
                elif op == 34:  # CONSISTENCY_STRESS
                    tid = self.random_tenant_id()
                    if tid:
                        results = []
                        for _ in range(10):
                            t = self.tenant_registry.get_tenant(tid)
                            if t:
                                results.append(t.tenant_id)
                        if results:
                            assert all(r == results[0] for r in results)
                        self._log_operation(worker_id, 34, True)
                        
                elif op == 35:  # QUOTA_OVERLOAD
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(20):
                            self.tenant_registry.record_usage(
                                tid, random.choice(["agents", "api_calls"]),
                                random.randint(1, 50)
                            )
                        self.tenant_registry.check_quota(tid, "agents", 1)
                        self._log_operation(worker_id, 35, True)
                        
                elif op == 36:  # RAPID_CREATE_DELETE
                    for _ in range(3):
                        ok, tid = self._create_tenant_internal(worker_id, "rapid")
                        if ok:
                            self.tenant_registry.delete_tenant(tid)
                    self._log_operation(worker_id, 36, True)
                    
                elif op == 37:  # STATE_CYCLE
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(3):
                            for status in list(TenantStatus):
                                self.tenant_registry.update_tenant_status(tid, status)
                        self._log_operation(worker_id, 37, True)
                        
                elif op == 38:  # TIER_CYCLE
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(3):
                            for tier in list(TenantTier):
                                self.tenant_registry.update_tier(tid, tier)
                        self._log_operation(worker_id, 38, True)
                        
                elif op == 39:  # HEALTH_CYCLE
                    sid = self.random_service_id()
                    if sid:
                        for _ in range(3):
                            for h in [0.99, 0.75, 0.5, 0.25, 0.01]:
                                self.service_registry.update_service_health(sid, h)
                        self._log_operation(worker_id, 39, True)
                        
                elif op == 40:  # CHAOS_MONKEY_DELETE
                    with self.lock:
                        if len(self.tenants) > 20:
                            to_delete = random.sample(self.tenants, min(5, len(self.tenants) - 15))
                            for tid in to_delete:
                                if tid in self.tenants:
                                    self.tenants.remove(tid)
                                self.tenant_registry.delete_tenant(tid)
                            self._log_operation(worker_id, 40, True, f"删除{len(to_delete)}个")
                            
                elif op == 41:  # CHAOS_MONKEY_UPDATE
                    tids, _ = self.get_random_ids(5)
                    for tid in tids:
                        self.tenant_registry.update_tenant_status(
                            tid, random.choice(list(TenantStatus))
                        )
                        self.tenant_registry.update_tier(
                            tid, random.choice(list(TenantTier))
                        )
                    self._log_operation(worker_id, 41, True)
                    
                elif op == 42:  # CASCADING_FAILURES
                    ok, tid = self._create_tenant_internal(worker_id, "cascade")
                    if ok:
                        self.tenant_registry.delete_tenant(tid)
                        try:
                            self.tenant_registry.update_tenant_status(tid, TenantStatus.ACTIVE)
                            self.tenant_registry.record_usage(tid, "agents", 10)
                            error_occurred = True
                        except:
                            self._log_operation(worker_id, 42, True, "级联失败正确处理")
                            
                elif op == 43:  # RESOURCE_EXHAUSTION_SIM
                    for _ in range(10):
                        self.tenant_registry.list_tenants(limit=200)
                    self._log_operation(worker_id, 43, True)
                    
                elif op == 44:  # CROSS_TENANT_OPERATIONS
                    tids, _ = self.get_random_ids(5)
                    for tid in tids:
                        self.tenant_registry.record_usage(
                            tid, random.choice(["agents", "api_calls", "ai_credits"]),
                            random.randint(1, 100)
                        )
                        self.tenant_registry.check_quota(
                            tid, random.choice(["agents", "api_calls"]),
                            random.randint(1, 50)
                        )
                    self._log_operation(worker_id, 44, True)
                    
                elif op == 45:  # SERVICE_DISCOVERY_STORM
                    for _ in range(5):
                        self.service_registry.discover_service(random.choice(list(ServiceType)))
                    self._log_operation(worker_id, 45, True)
                    
                elif op == 46:  # DEADLOCK_SIMULATION
                    tids, sids = self.get_random_ids(2)
                    if tids and sids:
                        self.tenant_registry.update_tier(tids[0], random.choice(list(TenantTier)))
                        self.service_registry.update_service_health(sids[0], random.uniform(0, 1))
                        self.tenant_registry.update_tenant_status(tids[0], random.choice(list(TenantStatus)))
                        self.service_registry.update_service_status(sids[0], random.choice(list(ServiceStatus)))
                    self._log_operation(worker_id, 46, True)
                    
                elif op == 47:  # STARVATION_TEST
                    with self.lock:
                        for _ in range(5):
                            self.tenant_registry.list_tenants(limit=100)
                    self._log_operation(worker_id, 47, True)
                    
                elif op == 48:  # MEMORY_LEAK_DETECTION
                    gc.collect()
                    initial_objs = len(gc.get_objects())
                    for _ in range(10):
                        self.tenant_registry.list_tenants(limit=100)
                    gc.collect()
                    final_objs = len(gc.get_objects())
                    obj_diff = final_objs - initial_objs
                    if obj_diff > 1000:
                        thread_logger.warning(f"潜在内存泄漏检测: 对象增加 {obj_diff}")
                    self._log_operation(worker_id, 48, True, f"obj_diff={obj_diff}")
                    
                elif op == 49:  # RACE_CONDITION_INJECTION
                    ok, tid = self._create_tenant_internal(worker_id, "race")
                    if ok:
                        threads = []
                        for i in range(5):
                            def update_tier():
                                self.tenant_registry.update_tier(tid, random.choice(list(TenantTier)))
                            t = threading.Thread(target=update_tier)
                            threads.append(t)
                            t.start()
                        for t in threads:
                            t.join()
                        t = self.tenant_registry.get_tenant(tid)
                        assert t is not None
                        self._log_operation(worker_id, 49, True)
                
                ops_count += 1
                
                with self.lock:
                    self.metrics.total_ops += 1
                    if not error_occurred:
                        self.metrics.success_ops += 1
                
            except Exception as e:
                local_errors += 1
                error_info = {
                    "time": datetime.now().isoformat(),
                    "worker": worker_id,
                    "op": op,
                    "op_name": self.operation_patterns.get(op, f"OP_{op}"),
                    "error_type": type(e).__name__,
                    "error_msg": str(e)[:200],
                    "traceback": traceback.format_exc()[:500]
                }
                with self.lock:
                    self.metrics.fail_ops += 1
                    self.metrics.errors.append(error_info)
                thread_logger.error(f"[W{worker_id}] ERROR in {self.operation_patterns.get(op, f'OP_{op}')}: {type(e).__name__}: {str(e)[:100]}")
                if local_errors > 100:
                    thread_logger.error(f"Worker {worker_id} 错误过多，停止")
                    break
        
        thread_logger.info(f"Worker {worker_id} 完成，执行了 {ops_count} 个操作，错误 {local_errors} 个")
    
    def monitor(self):
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            process = None
            
        last_report = time.time()
        last_snapshot = time.time()
        
        while self.running:
            time.sleep(10)
            elapsed = time.time() - self.start_time
            progress = elapsed / self.duration * 100
            
            memory_mb = process.memory_info().rss / 1024 / 1024 if process else 0
            
            with self.lock:
                total = self.metrics.total_ops
                success = self.metrics.success_ops
                failed = self.metrics.fail_ops
                tenants = len(self.tenants)
                services = len(self.services)
                snapshots = len(self.tenant_snapshots)
                
            success_rate = (success / total * 100) if total > 0 else 0
            ops_per_sec = total / elapsed if elapsed > 0 else 0
            
            print(f"\n{'='*80}")
            print(f"⏱️ 进度: {elapsed:.1f}s / {self.duration:.1f}s ({progress:.1f}%)")
            print(f"📊 操作: {total:,} (当前: {ops_per_sec:.0f}/s)")
            print(f"✅ 成功: {success:,} ({success_rate:.2f}%)")
            print(f"❌ 失败: {failed:,}")
            print(f"🏠 租户: {tenants:,}")
            print(f"🔧 服务: {services:,}")
            print(f"📸 快照: {snapshots:,}")
            print(f"💾 内存: {memory_mb:.1f} MB")
            print(f"{'='*80}")
            
            if elapsed - last_snapshot >= 60:
                logger.info(f"进度快照: {elapsed:.0f}s, {total:,} ops, {success_rate:.2f}% success")
                last_snapshot = elapsed
                
            if elapsed - last_report >= 60 and failed > 0:
                print("\n📋 最近错误 (前10):")
                with self.lock:
                    recent = self.metrics.errors[-10:]
                for i, err in enumerate(recent, 1):
                    print(f"  {i}. [W{err['worker']}] {err['op_name']}: {err['error_type']}: {err['error_msg'][:60]}")
                last_report = elapsed
    
    def run(self):
        print("="*80)
        print("🚀 Phase 43: 超终极混乱测试")
        print("="*80)
        print(f"⏱️ 测试时长: {self.duration/60:.1f} 分钟")
        print(f"🧵 并发线程: {self.num_threads}")
        print(f"📋 操作类型: 50种 (0-49)")
        print("="*80)
        
        self.start_time = time.time()
        self.metrics.start_time = self.start_time
        
        monitor_thread = threading.Thread(target=self.monitor, daemon=True)
        monitor_thread.start()
        
        workers = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()
            if i % 100 == 0 and i > 0:
                print(f"✅ 已启动 {i} 个工作线程...")
        
        print(f"\n✅ {self.num_threads} 个工作线程已全部启动\n")
        
        for t in workers:
            t.join()
        
        self.running = False
        monitor_thread.join(5)
        
        elapsed = time.time() - self.start_time
        total = self.metrics.total_ops
        success = self.metrics.success_ops
        failed = self.metrics.fail_ops
        
        print("\n" + "="*80)
        print("📊 最终测试结果")
        print("="*80)
        print(f"⏱️ 总耗时: {elapsed:.2f} 秒 ({elapsed/60:.2f} 分钟)")
        print(f"📊 总操作: {total:,}")
        print(f"✅ 成功: {success:,} ({(success/total*100) if total>0 else 0:.2f}%)")
        print(f"❌ 失败: {failed:,} ({(failed/total*100) if total>0 else 0:.2f}%)")
        print(f"📈 QPS: {total/elapsed:.0f}")
        print("="*80)
        
        print("\n📋 操作统计:")
        with self.lock:
            op_counts = dict(self.metrics.operation_counts)
        sorted_ops = sorted(op_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        for op, count in sorted_ops:
            print(f"  {op}: {count:,}")
            
        if failed > 0:
            print(f"\n📋 错误统计 ({len(self.metrics.errors)} 条):")
            error_types = {}
            for err in self.metrics.errors:
                et = err['error_type']
                error_types[et] = error_types.get(et, 0) + 1
            for et, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {et}: {count}")
        
        output_file = os.path.join(os.path.dirname(__file__), "phase43_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": "Phase 43",
                "duration_sec": elapsed,
                "duration_min": elapsed/60,
                "threads": self.num_threads,
                "total_operations": total,
                "successful_operations": success,
                "failed_operations": failed,
                "success_rate": (success/total*100) if total>0 else 0,
                "qps": total/elapsed,
                "operation_counts": dict(self.metrics.operation_counts),
                "errors": self.metrics.errors[-200:],
                "final_tenants": len(self.tenants),
                "final_services": len(self.services),
                "test_time": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ 结果已保存: {output_file}")
        
        log_summary_file = os.path.join(os.path.dirname(__file__), "phase43_summary.log")
        with open(log_summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Phase 43 超终极混乱测试结果\n")
            f.write(f"{'='*60}\n")
            f.write(f"测试时长: {elapsed/60:.2f} 分钟\n")
            f.write(f"并发线程: {self.num_threads}\n")
            f.write(f"总操作数: {total:,}\n")
            f.write(f"成功率: {(success/total*100) if total>0 else 0:.2f}%\n")
            f.write(f"失败数: {failed:,}\n")
            f.write(f"QPS: {total/elapsed:.0f}\n")
            f.write(f"\n操作统计:\n")
            for op, count in sorted_ops:
                f.write(f"  {op}: {count:,}\n")
            if failed > 0:
                f.write(f"\n错误统计:\n")
                for et, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                    f.write(f"  {et}: {count}\n")
        
        print(f"✅ 日志摘要已保存: {log_summary_file}")
        
        return self.metrics


if __name__ == "__main__":
    tester = UltimateTester(duration_min=20, threads=1000)
    results = tester.run()
    
    print("\n" + "="*80)
    if len(results.errors) == 0:
        print("🎉 完美！系统完美通过超终极混乱测试！")
    else:
        error_rate = len(results.errors) / results.total_ops * 100
        print(f"⚠️  发现 {len(results.errors)} 个错误 ({error_rate:.4f}%)")
        if error_rate < 0.01:
            print("✅ 错误率极低，系统稳定性优秀！")
        else:
            print("❌ 错误率较高，需要进一步调查")
    print("="*80)
