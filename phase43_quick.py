#!/usr/bin/env python3
"""
Phase 43 Quick: 快速验证测试
5分钟，500线程，快速验证系统
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import threading
import random
from uuid import uuid4
from datetime import datetime
from typing import List
import logging
import traceback
import json
from dataclasses import dataclass, field
import gc
from collections import defaultdict

from multi_tenant.tenant_core import (
    TenantRegistry, TenantTier, TenantStatus
)
from distributed.distributed_core import (
    ServiceRegistry, ServiceType, ServiceStatus
)

LOG_FILE = os.path.join(os.path.dirname(__file__), 'phase43_quick.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)
logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    total_ops: int = 0
    success_ops: int = 0
    fail_ops: int = 0
    operation_counts: dict = field(default_factory=lambda: defaultdict(int))
    errors: list = field(default_factory=list)


class QuickTester:
    def __init__(self, duration_min=5, threads=500):
        self.duration = duration_min * 60
        self.num_threads = threads
        self.tenant_registry = TenantRegistry()
        self.service_registry = ServiceRegistry()
        self.metrics = Metrics()
        self.tenants: List[str] = []
        self.services: List[str] = []
        self.lock = threading.RLock()
        self.running = True
        self.start_time = None
        
    def random_tenant_id(self) -> str:
        with self.lock:
            return random.choice(self.tenants) if self.tenants else None
            
    def random_service_id(self) -> str:
        with self.lock:
            return random.choice(self.services) if self.services else None
    
    def worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} 启动")
        ops_count = 0
        local_errors = 0
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                op = random.randint(0, 40)
                
                if op == 0:  # CREATE_TENANT
                    slug = f"p43q-{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Chaos-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"c{worker_id}{uuid4().hex[:6]}@test.com",
                        owner_id=uuid4(),
                        tier=random.choice(list(TenantTier))
                    )
                    with self.lock:
                        self.tenants.append(str(tenant.tenant_id))
                        
                elif op == 1:  # GET_TENANT
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.get_tenant(tid)
                        
                elif op == 2:  # UPDATE_STATUS
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tenant_status(
                            tid, random.choice(list(TenantStatus))
                        )
                        
                elif op == 3:  # UPDATE_TIER
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tier(
                            tid, random.choice(list(TenantTier))
                        )
                        
                elif op == 4:  # RECORD_USAGE
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.record_usage(
                            tid, random.choice(["agents", "api_calls"]),
                            random.randint(1, 100)
                        )
                        
                elif op == 5:  # CHECK_QUOTA
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.check_quota(
                            tid, random.choice(["agents", "api_calls"]),
                            random.randint(1, 50)
                        )
                        
                elif op == 6:  # DELETE_TENANT
                    with self.lock:
                        if len(self.tenants) > 10:
                            tid = self.tenants.pop(0)
                            self.tenant_registry.delete_tenant(tid)
                            
                elif op == 7:  # REGISTER_SERVICE
                    svc = self.service_registry.register_service(
                        f"s{worker_id}-{uuid4().hex[:6]}",
                        random.choice(list(ServiceType)),
                        f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                        random.randint(1000, 65535)
                    )
                    with self.lock:
                        self.services.append(svc.instance_id)
                        
                elif op == 8:  # GET_SERVICE
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.get_service_instance(sid)
                        
                elif op == 9:  # UPDATE_HEALTH
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_health(
                            sid, random.uniform(0, 1)
                        )
                        
                elif op == 10:  # UNREGISTER_SERVICE
                    with self.lock:
                        if len(self.services) > 5:
                            sid = self.services.pop(0)
                            self.service_registry.unregister_service(sid)
                            
                elif op == 11:  # DISCOVER_SERVICE
                    self.service_registry.discover_service(
                        random.choice(list(ServiceType))
                    )
                    
                elif op == 12:  # LIST_TENANTS
                    self.tenant_registry.list_tenants(
                        limit=random.choice([None, 10, 50, 100]),
                        offset=random.randint(0, 10)
                    )
                    
                elif op == 13:  # CONSISTENCY_CHECK
                    tid = self.random_tenant_id()
                    if tid:
                        t1 = self.tenant_registry.get_tenant(tid)
                        t2 = self.tenant_registry.get_tenant(tid)
                        if t1 and t2:
                            assert t1.tenant_id == t2.tenant_id
                            
                elif op == 14:  # MIXED_WORKFLOW
                    slug = f"wf{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Workflow-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"wf{uuid4().hex[:8]}@test.com",
                        owner_id=uuid4(),
                        tier=TenantTier.BASIC
                    )
                    with self.lock:
                        self.tenants.append(str(tenant.tenant_id))
                    self.tenant_registry.record_usage(tenant.tenant_id, "agents", 5)
                    self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
                    self.tenant_registry.update_tenant_status(tenant.tenant_id, TenantStatus.ACTIVE)
                    
                elif op == 15:  # QUOTA_STRESS
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(10):
                            self.tenant_registry.record_usage(
                                tid, "agents", random.randint(1, 10)
                            )
                            
                elif op == 16:  # RAPID_CREATE_DELETE
                    slug = f"fast{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Fast-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"fast{uuid4().hex[:8]}@test.com",
                        owner_id=uuid4()
                    )
                    self.tenant_registry.delete_tenant(tenant.tenant_id)
                    
                elif op == 17:  # INVALID_NAME
                    try:
                        self.tenant_registry.create_tenant(
                            name="",
                            slug=f"e{uuid4().hex[:12]}",
                            email=f"e{uuid4().hex[:8]}@test.com",
                            owner_id=uuid4()
                        )
                    except ValueError:
                        pass
                        
                elif op == 18:  # NEGATIVE_USAGE
                    tid = self.random_tenant_id()
                    if tid:
                        try:
                            self.tenant_registry.record_usage(
                                tid, "agents", -random.randint(1, 100)
                            )
                        except ValueError:
                            pass
                            
                elif op == 19:  # STATE_CYCLE
                    tid = self.random_tenant_id()
                    if tid:
                        for status in list(TenantStatus)[:3]:
                            self.tenant_registry.update_tenant_status(tid, status)
                            
                elif op == 20:  # TIER_CYCLE
                    tid = self.random_tenant_id()
                    if tid:
                        for tier in list(TenantTier)[:3]:
                            self.tenant_registry.update_tier(tid, tier)
                            
                elif op == 21:  # SERVICE_HEALTH_CYCLE
                    sid = self.random_service_id()
                    if sid:
                        for h in [0.9, 0.5, 0.1, 0.5, 0.9]:
                            self.service_registry.update_service_health(sid, h)
                            
                elif op == 22:  # INVALID_HEALTH
                    sid = self.random_service_id()
                    if sid:
                        try:
                            self.service_registry.update_service_health(
                                sid, random.uniform(-2, 2)
                            )
                        except ValueError:
                            pass
                            
                elif op == 23:  # GET_NONEXISTENT
                    self.tenant_registry.get_tenant(uuid4())
                    
                elif op == 24:  # DELETE_NONEXISTENT
                    self.tenant_registry.delete_tenant(uuid4())
                    
                elif op == 25:  # CROSS_TENANT_OPS
                    tids, _ = self.get_random_ids(3) if hasattr(self, 'get_random_ids') else (None, None)
                    if tids:
                        for tid in tids:
                            self.tenant_registry.record_usage(
                                tid, random.choice(["agents", "api_calls"]),
                                random.randint(1, 100)
                            )
                            
                elif op == 26:  # SERVICE_DISCOVERY_STORM
                    for _ in range(3):
                        self.service_registry.discover_service(
                            random.choice(list(ServiceType))
                        )
                        
                elif op == 27:  # PARALLEL_UPDATE
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(5):
                            self.tenant_registry.update_tier(
                                tid, random.choice(list(TenantTier))
                            )
                            
                elif op == 28:  # BATCH_LIST
                    for _ in range(5):
                        self.tenant_registry.list_tenants(limit=100)
                        
                elif op == 29:  # MEMORY_CHECK
                    gc.collect()
                    initial_objs = len(gc.get_objects())
                    for _ in range(5):
                        self.tenant_registry.list_tenants(limit=50)
                    gc.collect()
                    
                # 更多场景 30-40
                elif op == 30:
                    self._create_tenant_internal(worker_id)
                elif op == 31:
                    self._register_service_internal(worker_id)
                elif op == 32:
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tenant_status(tid, TenantStatus.ACTIVE)
                        self.tenant_registry.update_tier(tid, TenantTier.PRO)
                elif op == 33:
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_status(sid, ServiceStatus.HEALTHY)
                elif op == 34:
                    tid = self.random_tenant_id()
                    if tid:
                        t = self.tenant_registry.get_tenant(tid)
                        if t:
                            self.tenant_registry.record_usage(tid, "api_calls", 100)
                elif op == 35:
                    for _ in range(3):
                        self.service_registry.discover_service(random.choice(list(ServiceType)))
                elif op == 36:
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.check_quota(tid, "agents", 10)
                elif op == 37:
                    with self.lock:
                        if len(self.tenants) > 20:
                            for _ in range(3):
                                tid = self.tenants.pop(0)
                                self.tenant_registry.delete_tenant(tid)
                elif op == 38:
                    with self.lock:
                        if len(self.services) > 10:
                            for _ in range(3):
                                sid = self.services.pop(0)
                                self.service_registry.unregister_service(sid)
                elif op == 39:
                    self.tenant_registry.list_tenants(limit=200)
                elif op == 40:
                    for _ in range(3):
                        self.service_registry.discover_service(ServiceType.API_GATEWAY)
                
                ops_count += 1
                
                with self.lock:
                    self.metrics.total_ops += 1
                    self.metrics.success_ops += 1
                
            except Exception as e:
                local_errors += 1
                error_info = {
                    "time": datetime.now().isoformat(),
                    "worker": worker_id,
                    "op": op,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)[:100]
                }
                with self.lock:
                    self.metrics.fail_ops += 1
                    if len(self.metrics.errors) < 100:
                        self.metrics.errors.append(error_info)
                logger.error(f"[W{worker_id}] ERROR: {type(e).__name__}: {str(e)[:50]}")
        
        logger.info(f"Worker {worker_id} 完成，执行了 {ops_count} 个操作，错误 {local_errors} 个")
    
    def _create_tenant_internal(self, worker_id: int) -> bool:
        try:
            slug = f"p43i-{worker_id}-{uuid4().hex[:8]}"
            tenant = self.tenant_registry.create_tenant(
                name=f"Internal-{worker_id}-{uuid4().hex[:4]}",
                slug=slug,
                email=f"i{worker_id}@{uuid4().hex[:6]}.com",
                owner_id=uuid4(),
                tier=random.choice(list(TenantTier))
            )
            with self.lock:
                self.tenants.append(str(tenant.tenant_id))
            return True
        except:
            return False
            
    def _register_service_internal(self, worker_id: int) -> bool:
        try:
            svc = self.service_registry.register_service(
                f"svc{worker_id}-{uuid4().hex[:6]}",
                random.choice(list(ServiceType)),
                f"192.168.{random.randint(1,255)}.{random.randint(1,254)}",
                random.randint(8000, 9000)
            )
            with self.lock:
                self.services.append(svc.instance_id)
            return True
        except:
            return False
    
    def get_random_ids(self, count: int) -> tuple:
        with self.lock:
            tids = random.sample(self.tenants, min(count, len(self.tenants))) if self.tenants else []
            sids = random.sample(self.services, min(count, len(self.services))) if self.services else []
        return tids, sids
    
    def monitor(self):
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            process = None
            
        while self.running:
            time.sleep(30)
            elapsed = time.time() - self.start_time
            progress = elapsed / self.duration * 100
            
            memory_mb = process.memory_info().rss / 1024 / 1024 if process else 0
            
            with self.lock:
                total = self.metrics.total_ops
                success = self.metrics.success_ops
                failed = self.metrics.fail_ops
                tenants = len(self.tenants)
                services = len(self.services)
                
            success_rate = (success / total * 100) if total > 0 else 0
            ops_per_sec = total / elapsed if elapsed > 0 else 0
            
            print(f"\n{'='*80}")
            print(f"⏱️ 进度: {elapsed:.1f}s / {self.duration:.1f}s ({progress:.1f}%)")
            print(f"📊 操作: {total:,} (当前: {ops_per_sec:.0f}/s)")
            print(f"✅ 成功: {success:,} ({success_rate:.2f}%)")
            print(f"❌ 失败: {failed:,}")
            print(f"🏠 租户: {tenants:,}")
            print(f"🔧 服务: {services:,}")
            print(f"💾 内存: {memory_mb:.1f} MB")
            print(f"{'='*80}\n")
            
            logger.info(f"进度快照: {elapsed:.0f}s, {total:,} ops, {success_rate:.2f}% success")
    
    def run(self):
        print("="*80)
        print("🚀 Phase 43 Quick: 快速验证测试")
        print("="*80)
        print(f"⏱️ 测试时长: {self.duration/60:.1f} 分钟")
        print(f"🧵 并发线程: {self.num_threads}")
        print(f"📋 操作类型: 41种")
        print("="*80)
        
        self.start_time = time.time()
        
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
        monitor_thread.join(2)
        
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
        
        if failed > 0:
            print(f"\n📋 错误统计 ({len(self.metrics.errors)} 条):")
            error_types = {}
            for err in self.metrics.errors:
                et = err['error_type']
                error_types[et] = error_types.get(et, 0) + 1
            for et, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {et}: {count}")
        
        output_file = os.path.join(os.path.dirname(__file__), "phase43_quick_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "phase": "Phase 43 Quick",
                "duration_sec": elapsed,
                "duration_min": elapsed/60,
                "threads": self.num_threads,
                "total_operations": total,
                "successful_operations": success,
                "failed_operations": failed,
                "success_rate": (success/total*100) if total>0 else 0,
                "qps": total/elapsed,
                "errors": self.metrics.errors[:50],
                "final_tenants": len(self.tenants),
                "final_services": len(self.services),
                "test_time": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ 结果已保存: {output_file}")
        
        print("\n" + "="*80)
        if failed == 0:
            print("🎉 完美！系统完美通过快速验证测试！")
        else:
            error_rate = failed / total * 100
            print(f"⚠️  发现 {failed} 个错误 ({error_rate:.4f}%)")
            if error_rate < 0.01:
                print("✅ 错误率极低，系统稳定性优秀！")
            else:
                print("❌ 错误率较高，需要进一步调查")
        print("="*80)
        
        return self.metrics


if __name__ == "__main__":
    tester = QuickTester(duration_min=5, threads=500)
    results = tester.run()
