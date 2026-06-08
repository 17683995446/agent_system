#!/usr/bin/env python3
"""
Phase 42: 极限复杂场景测试
10分钟，500线程，极端混乱场景
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import threading
import random
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any
import logging
import traceback
import json
from dataclasses import dataclass
import gc

from multi_tenant.tenant_core import (
    TenantRegistry, TenantTier, TenantStatus
)
from distributed.distributed_core import (
    ServiceRegistry, ServiceType, ServiceStatus
)

LOG_FILE = os.path.join(os.path.dirname(__file__), 'phase42_ultimate.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
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
    errors: List[Dict] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class UltimateTester:
    def __init__(self, duration_min=10, threads=500):
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
        
        while self.running and (time.time() - self.start_time) < self.duration:
            try:
                op = random.randint(0, 30)
                error_occurred = False
                
                # 基础租户操作
                if op == 0:  # 创建租户
                    slug = f"p42-{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Chaos-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"c{uuid4().hex[:8]}@test.com",
                        owner_id=uuid4(),
                        tier=random.choice(list(TenantTier))
                    )
                    with self.lock:
                        self.tenants.append(str(tenant.tenant_id))
                    logger.debug(f"[W{worker_id}] CREATE: {tenant.tenant_id}")
                    
                elif op == 1:  # 查询租户
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.get_tenant(tid)
                        logger.debug(f"[W{worker_id}] GET_TENANT")
                        
                elif op == 2:  # 更新状态
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tenant_status(
                            tid, random.choice(list(TenantStatus))
                        )
                        logger.debug(f"[W{worker_id}] UPDATE_STATUS")
                        
                elif op == 3:  # 更新tier
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.update_tier(
                            tid, random.choice(list(TenantTier))
                        )
                        logger.debug(f"[W{worker_id}] UPDATE_TIER")
                        
                elif op == 4:  # 记录使用
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.record_usage(
                            tid, random.choice(["agents", "api_calls", "ai_credits"]),
                            random.randint(1, 100)
                        )
                        logger.debug(f"[W{worker_id}] RECORD_USAGE")
                        
                elif op == 5:  # 配额检查
                    tid = self.random_tenant_id()
                    if tid:
                        self.tenant_registry.check_quota(
                            tid, random.choice(["agents", "api_calls"]),
                            random.randint(1, 50)
                        )
                        logger.debug(f"[W{worker_id}] CHECK_QUOTA")
                        
                elif op == 6:  # 删除租户
                    with self.lock:
                        if self.tenants:
                            tid = self.tenants.pop(0)
                            result = self.tenant_registry.delete_tenant(tid)
                            if result:
                                logger.debug(f"[W{worker_id}] DELETE_TENANT")
                                
                # 服务操作
                elif op == 7:  # 注册服务
                    svc = self.service_registry.register_service(
                        f"s{uuid4().hex[:8]}",
                        random.choice(list(ServiceType)),
                        f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                        random.randint(1000, 65535)
                    )
                    with self.lock:
                        self.services.append(svc.instance_id)
                    logger.debug(f"[W{worker_id}] REGISTER_SERVICE: {svc.instance_id}")
                    
                elif op == 8:  # 查询服务
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.get_service_instance(sid)
                        logger.debug(f"[W{worker_id}] GET_SERVICE")
                        
                elif op == 9:  # 更新健康
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_health(
                            sid, random.uniform(0, 1)
                        )
                        logger.debug(f"[W{worker_id}] UPDATE_HEALTH")
                        
                elif op == 10:  # 更新服务状态
                    sid = self.random_service_id()
                    if sid:
                        self.service_registry.update_service_status(
                            sid, random.choice(list(ServiceStatus))
                        )
                        logger.debug(f"[W{worker_id}] UPDATE_SERVICE_STATUS")
                        
                elif op == 11:  # 注销服务
                    with self.lock:
                        if self.services:
                            sid = self.services.pop(0)
                            self.service_registry.unregister_service(sid)
                            logger.debug(f"[W{worker_id}] UNREGISTER_SERVICE")
                            
                elif op == 12:  # 服务发现
                    self.service_registry.discover_service(
                        random.choice(list(ServiceType))
                    )
                    logger.debug(f"[W{worker_id}] DISCOVER_SERVICE")
                    
                # 异常操作
                elif op == 13:  # 空名称
                    try:
                        self.tenant_registry.create_tenant(
                            name="",
                            slug=f"e{uuid4().hex[:12]}",
                            email=f"e{uuid4().hex[:8]}@test.com",
                            owner_id=uuid4()
                        )
                    except ValueError:
                        logger.debug(f"[W{worker_id}] EMPTY_NAME_REJECTED")
                        
                elif op == 14:  # 超长名称
                    try:
                        self.tenant_registry.create_tenant(
                            name="X" * 1000,
                            slug=f"l{uuid4().hex[:12]}",
                            email=f"l{uuid4().hex[:8]}@test.com",
                            owner_id=uuid4()
                        )
                    except ValueError:
                        logger.debug(f"[W{worker_id}] LONG_NAME_REJECTED")
                        
                elif op == 15:  # 负数使用量
                    tid = self.random_tenant_id()
                    if tid:
                        try:
                            self.tenant_registry.record_usage(
                                tid, "agents", -random.randint(1, 1000)
                            )
                        except ValueError:
                            logger.debug(f"[W{worker_id}] NEGATIVE_USAGE_REJECTED")
                            
                elif op == 16:  # 无效健康值
                    sid = self.random_service_id()
                    if sid:
                        try:
                            self.service_registry.update_service_health(
                                sid, random.uniform(-2, 2)
                            )
                        except ValueError:
                            logger.debug(f"[W{worker_id}] INVALID_HEALTH_REJECTED")
                            
                elif op == 17:  # 查询不存在
                    self.tenant_registry.get_tenant(uuid4())
                    logger.debug(f"[W{worker_id}] GET_NONEXISTENT")
                    
                elif op == 18:  # 删除不存在
                    self.tenant_registry.delete_tenant(uuid4())
                    logger.debug(f"[W{worker_id}] DELETE_NONEXISTENT")
                    
                elif op == 19:  # 列表查询
                    self.tenant_registry.list_tenants(
                        limit=random.choice([None, 10, 50, 100]),
                        offset=random.randint(0, 10)
                    )
                    logger.debug(f"[W{worker_id}] LIST_TENANTS")
                    
                # 复杂操作
                elif op == 20:  # 混合操作
                    slug = f"m{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Mixed-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"m{uuid4().hex[:8]}@test.com",
                        owner_id=uuid4(),
                        tier=TenantTier.FREE
                    )
                    with self.lock:
                        self.tenants.append(str(tenant.tenant_id))
                    self.tenant_registry.record_usage(tenant.tenant_id, "agents", 5)
                    self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
                    self.tenant_registry.update_tenant_status(
                        tenant.tenant_id, TenantStatus.ACTIVE
                    )
                    logger.debug(f"[W{worker_id}] MIXED_OPS")
                    
                elif op == 21:  # 一致性验证
                    tid = self.random_tenant_id()
                    if tid:
                        t1 = self.tenant_registry.get_tenant(tid)
                        t2 = self.tenant_registry.get_tenant(tid)
                        if t1 and t2:
                            assert t1.tenant_id == t2.tenant_id
                        logger.debug(f"[W{worker_id}] CONSISTENCY_CHECK")
                        
                elif op == 22:  # 并发冲突
                    tid = self.random_tenant_id()
                    if tid:
                        for _ in range(3):
                            self.tenant_registry.update_tier(
                                tid, random.choice(list(TenantTier))
                            )
                        logger.debug(f"[W{worker_id}] CONCURRENT_UPDATE")
                        
                elif op == 23:  # 批量操作
                    for _ in range(5):
                        self.tenant_registry.list_tenants(limit=10)
                    logger.debug(f"[W{worker_id}] BATCH_OPS")
                    
                elif op == 24:  # 服务链路
                    svc_type = random.choice(list(ServiceType))
                    discovered = self.service_registry.discover_service(svc_type)
                    if discovered:
                        for svc in discovered[:3]:
                            self.service_registry.get_service_instance(svc.instance_id)
                    logger.debug(f"[W{worker_id}] SERVICE_CHAIN")
                    
                elif op == 25:  # 复杂工作流
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
                    self.tenant_registry.record_usage(tenant.tenant_id, "api_calls", 100)
                    self.tenant_registry.update_tier(tenant.tenant_id, TenantTier.PRO)
                    self.tenant_registry.update_tenant_status(
                        tenant.tenant_id, TenantStatus.ACTIVE
                    )
                    
                    svc = self.service_registry.register_service(
                        f"wf-svc-{uuid4().hex[:6]}",
                        ServiceType.API_GATEWAY,
                        "10.0.0.1",
                        8000
                    )
                    with self.lock:
                        self.services.append(svc.instance_id)
                    
                    self.service_registry.update_service_health(svc.instance_id, 0.95)
                    logger.debug(f"[W{worker_id}] COMPLEX_WORKFLOW")
                    
                # 极端场景
                elif op == 26:  # 快速创建删除
                    slug = f"fast{uuid4().hex[:12]}"
                    tenant = self.tenant_registry.create_tenant(
                        name=f"Fast-{uuid4().hex[:6]}",
                        slug=slug,
                        email=f"fast{uuid4().hex[:8]}@test.com",
                        owner_id=uuid4()
                    )
                    self.tenant_registry.delete_tenant(tenant.tenant_id)
                    logger.debug(f"[W{worker_id}] FAST_CREATE_DELETE")
                    
                elif op == 27:  # 极限配额
                    tid = self.random_tenant_id()
                    if tid:
                        for i in range(10):
                            self.tenant_registry.record_usage(tid, "agents", random.randint(1, 10))
                        self.tenant_registry.check_quota(tid, "agents", 1)
                    logger.debug(f"[W{worker_id}] QUOTA_STRESS")
                    
                elif op == 28:  # 服务健康震荡
                    sid = self.random_service_id()
                    if sid:
                        for h in [0.9, 0.1, 0.8, 0.2, 0.95]:
                            self.service_registry.update_service_health(sid, h)
                    logger.debug(f"[W{worker_id}] HEALTH_FLUCTUATION")
                    
                elif op == 29:  # 状态循环
                    tid = self.random_tenant_id()
                    if tid:
                        statuses = list(TenantStatus)
                        for status in statuses[:3]:
                            self.tenant_registry.update_tenant_status(tid, status)
                    logger.debug(f"[W{worker_id}] STATUS_CYCLE")
                    
                elif op == 30:  # 极端Tier切换
                    tid = self.random_tenant_id()
                    if tid:
                        tiers = list(TenantTier)
                        for tier in tiers[:5]:
                            self.tenant_registry.update_tier(tid, tier)
                    logger.debug(f"[W{worker_id}] TIER_SWITCH")
                
                ops_count += 1
                
                with self.lock:
                    self.metrics.total_ops += 1
                    if not error_occurred:
                        self.metrics.success_ops += 1
                
            except Exception as e:
                error_info = {
                    "time": datetime.now().isoformat(),
                    "worker": worker_id,
                    "op": op,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
                with self.lock:
                    self.metrics.fail_ops += 1
                    self.metrics.errors.append(error_info)
                logger.error(f"[W{worker_id}] ERROR: {error_info['error_type']}: {error_info['error_msg']}")
        
        logger.info(f"Worker {worker_id} 完成，执行了 {ops_count} 个操作")
    
    def monitor(self):
        import psutil
        process = psutil.Process()
        last_report = time.time()
        while self.running:
            time.sleep(10)
            elapsed = time.time() - self.start_time
            progress = elapsed / self.duration * 100
            
            memory_mb = process.memory_info().rss / 1024 / 1024
            
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
            print(f"{'='*80}")
            
            if elapsed - last_report >= 30 and failed > 0:
                print("\n📋 最近错误:")
                with self.lock:
                    recent = self.metrics.errors[-5:]
                for i, err in enumerate(recent, 1):
                    print(f"  {i}. [{err['worker']}] {err['error_type']}: {err['error_msg'][:80]}")
                last_report = elapsed
    
    def run(self):
        print("="*80)
        print("🚀 Phase 42: 极限复杂场景测试")
        print("="*80)
        print(f"⏱️ 测试时长: {self.duration/60:.1f} 分钟")
        print(f"🧵 并发线程: {self.num_threads}")
        print("="*80)
        
        self.start_time = time.time()
        
        monitor_thread = threading.Thread(target=self.monitor, daemon=True)
        monitor_thread.start()
        
        workers = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(i,), daemon=True)
            workers.append(t)
            t.start()
        
        print(f"\n✅ {self.num_threads} 个工作线程已启动\n")
        
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
        print(f"⏱️ 总耗时: {elapsed:.2f} 秒")
        print(f"📊 总操作: {total:,}")
        print(f"✅ 成功: {success:,} ({(success/total*100) if total>0 else 0:.2f}%)")
        print(f"❌ 失败: {failed:,}")
        print(f"📈 QPS: {total/elapsed:.0f}")
        print("="*80)
        
        output_file = os.path.join(os.path.dirname(__file__), "phase42_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "duration_sec": elapsed,
                "threads": self.num_threads,
                "total_operations": total,
                "successful_operations": success,
                "failed_operations": failed,
                "success_rate": (success/total*100) if total>0 else 0,
                "qps": total/elapsed,
                "errors": self.metrics.errors[-100:],
                "final_tenants": len(self.tenants),
                "final_services": len(self.services)
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ 结果已保存: {output_file}")
        return self.metrics


if __name__ == "__main__":
    tester = UltimateTester(duration_min=10, threads=500)
    results = tester.run()
    
    if len(results.errors) == 0:
        print("\n🎉 完美！系统完美通过极限复杂场景测试！")
    else:
        print(f"\n❌ 发现 {len(results.errors)} 个错误")
