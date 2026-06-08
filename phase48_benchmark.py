#!/usr/bin/env python3
"""
Phase 48: 缓存性能对比测试（修复版）
验证缓存层带来的性能提升
"""

import sys
import os
import time
import uuid
import threading
import statistics
import random
from typing import List, Dict

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase47_database import reset_db, SessionLocal
from phase47_repository import TenantRepository, TenantTierDB
from phase48_cache import CacheManager, MemoryCache

# ==================== 全局缓存实例 ====================

_cache_manager = None
_cache_lock = threading.Lock()

def get_global_cache() -> CacheManager:
    """获取全局缓存管理器（单例）"""
    global _cache_manager
    if _cache_manager is None:
        with _cache_lock:
            if _cache_manager is None:
                _cache_manager = CacheManager(backend=MemoryCache())
    return _cache_manager

# ==================== 测试配置 ====================

TEST_CONFIGS = {
    "small": {"tenants": 100, "operations": 1000},
    "medium": {"tenants": 500, "operations": 5000},
    "large": {"tenants": 1000, "operations": 10000}
}

# ==================== 无缓存性能测试 ====================

def benchmark_without_cache(num_tenants: int, num_operations: int) -> Dict:
    """无缓存性能测试"""
    print(f"\n{'='*80}")
    print(f"测试: 无缓存 - {num_tenants} 租户, {num_operations} 操作")
    print(f"{'='*80}")
    
    reset_db()
    
    # 创建初始数据
    print("创建租户数据...")
    tenant_ids = []
    db = SessionLocal()
    repo = TenantRepository(db)
    
    for i in range(num_tenants):
        tenant = repo.create(
            name=f"NoCache-Tenant-{i}",
            slug=f"nocache-{i}-{uuid.uuid4().hex[:6]}",
            email=f"nocache-{i}@test.com",
            owner_id=uuid.uuid4(),
            tier=random.choice(list(TenantTierDB))
        )
        tenant_ids.append(tenant.tenant_id)
    
    db.close()
    print(f"已创建 {len(tenant_ids)} 个租户")
    
    # 执行操作
    print("执行操作...")
    latencies = []
    errors = 0
    
    start_time = time.time()
    
    for i in range(num_operations):
        op_start = time.time()
        
        try:
            db = SessionLocal()
            repo = TenantRepository(db)
            
            op_type = random.choice(["get", "check_quota", "record_usage"])
            
            if op_type == "get":
                repo.get_by_id(random.choice(tenant_ids))
            elif op_type == "check_quota":
                repo.check_quota(random.choice(tenant_ids), "agents", 1)
            else:
                repo.record_usage(random.choice(tenant_ids), "api_calls", 1)
            
            db.close()
            
            latencies.append((time.time() - op_start) * 1000)
            
        except Exception as e:
            errors += 1
    
    total_time = time.time() - start_time
    qps = num_operations / total_time if total_time > 0 else 0
    
    return {
        "total_operations": num_operations,
        "successful_operations": num_operations - errors,
        "errors": errors,
        "total_time": total_time,
        "qps": qps,
        "latencies": latencies
    }

# ==================== 有缓存性能测试 ====================

def benchmark_with_cache(num_tenants: int, num_operations: int) -> Dict:
    """有缓存性能测试"""
    print(f"\n{'='*80}")
    print(f"测试: 有缓存 - {num_tenants} 租户, {num_operations} 操作")
    print(f"{'='*80}")
    
    reset_db()
    
    # 获取全局缓存
    cache = get_global_cache()
    cache.clear_stats()  # 清除统计
    
    # 创建初始数据
    print("创建租户数据...")
    tenant_ids = []
    db = SessionLocal()
    repo = TenantRepository(db)
    
    for i in range(num_tenants):
        tenant = repo.create(
            name=f"Cached-Tenant-{i}",
            slug=f"cached-{i}-{uuid.uuid4().hex[:6]}",
            email=f"cached-{i}@test.com",
            owner_id=uuid.uuid4(),
            tier=random.choice(list(TenantTierDB))
        )
        tenant_ids.append(tenant.tenant_id)
        
        # 立即缓存
        cache_key = f"tenant:{tenant.tenant_id}"
        cache_data = {
            "tenant_id": str(tenant.tenant_id),
            "name": tenant.name,
            "slug": tenant.slug
        }
        cache.set(cache_key, cache_data, ttl=300)
    
    db.close()
    print(f"已创建 {len(tenant_ids)} 个租户（已缓存）")
    
    # 预热缓存（确保缓存可用）
    print("预热缓存...")
    for tid in tenant_ids[:min(50, len(tenant_ids))]:
        cache_key = f"tenant:{tid}"
        cached_data = cache.get(cache_key)
        if cached_data is None:
            # 未命中则设置
            db = SessionLocal()
            repo = TenantRepository(db)
            tenant = repo.get_by_id(tid)
            if tenant:
                cache_data = {
                    "tenant_id": str(tenant.tenant_id),
                    "name": tenant.name
                }
                cache.set(cache_key, cache_data, ttl=300)
            db.close()
    
    # 执行操作
    print("执行操作...")
    latencies = []
    errors = 0
    cache_hits = 0
    cache_misses = 0
    
    start_time = time.time()
    
    for i in range(num_operations):
        op_start = time.time()
        
        try:
            op_type = random.choice(["get", "check_quota", "record_usage"])
            tenant_id = random.choice(tenant_ids)
            cache_key = f"tenant:{tenant_id}"
            
            if op_type == "get":
                # 尝试从缓存获取
                cached_data = cache.get(cache_key)
                if cached_data:
                    cache_hits += 1
                else:
                    cache_misses += 1
                    # 回源加载
                    db = SessionLocal()
                    repo = TenantRepository(db)
                    tenant = repo.get_by_id(tenant_id)
                    if tenant:
                        cache_data = {
                            "tenant_id": str(tenant.tenant_id),
                            "name": tenant.name
                        }
                        cache.set(cache_key, cache_data, ttl=300)
                    db.close()
                    
            elif op_type == "check_quota":
                db = SessionLocal()
                repo = TenantRepository(db)
                repo.check_quota(tenant_id, "agents", 1)
                db.close()
            else:
                db = SessionLocal()
                repo = TenantRepository(db)
                repo.record_usage(tenant_id, "api_calls", 1)
                db.close()
            
            latencies.append((time.time() - op_start) * 1000)
            
        except Exception as e:
            errors += 1
    
    total_time = time.time() - start_time
    qps = num_operations / total_time if total_time > 0 else 0
    
    # 获取缓存统计
    cache_stats = cache.get_stats()
    cache_stats["manual_hits"] = cache_hits
    cache_stats["manual_misses"] = cache_misses
    
    return {
        "total_operations": num_operations,
        "successful_operations": num_operations - errors,
        "errors": errors,
        "total_time": total_time,
        "qps": qps,
        "latencies": latencies,
        "cache_stats": cache_stats
    }

# ==================== 对比分析 ====================

def compare_results(without_cache: Dict, with_cache: Dict):
    """对比分析结果"""
    print(f"\n{'='*80}")
    print("性能对比分析")
    print(f"{'='*80}")
    
    print(f"\n{'指标':<30} {'无缓存':<20} {'有缓存':<20} {'提升':<20}")
    print("-" * 90)
    
    # QPS
    qps_without = without_cache["qps"]
    qps_with = with_cache["qps"]
    qps_improvement = ((qps_with - qps_without) / qps_without * 100) if qps_without > 0 else 0
    
    print(f"{'QPS':<30} {qps_without:<20.2f} {qps_with:<20.2f} {qps_improvement:>+10.1f}%")
    
    # 平均延迟
    lat_without = statistics.mean(without_cache["latencies"])
    lat_with = statistics.mean(with_cache["latencies"])
    lat_improvement = ((lat_without - lat_with) / lat_without * 100) if lat_without > 0 else 0
    
    print(f"{'平均延迟 (ms)':<30} {lat_without:<20.2f} {lat_with:<20.2f} {lat_improvement:>+10.1f}%")
    
    # p95延迟
    p95_without = sorted(without_cache["latencies"])[int(len(without_cache["latencies"]) * 0.95)]
    p95_with = sorted(with_cache["latencies"])[int(len(with_cache["latencies"]) * 0.95)]
    p95_improvement = ((p95_without - p95_with) / p95_without * 100) if p95_without > 0 else 0
    
    print(f"{'P95延迟 (ms)':<30} {p95_without:<20.2f} {p95_with:<20.2f} {p95_improvement:>+10.1f}%")
    
    # 错误率
    err_without = without_cache["errors"] / without_cache["total_operations"] * 100
    err_with = with_cache["errors"] / with_cache["total_operations"] * 100
    
    print(f"{'错误率 (%)':<30} {err_without:<20.2f} {err_with:<20.2f}")
    
    # 缓存统计
    if "cache_stats" in with_cache:
        stats = with_cache["cache_stats"]
        print(f"\n缓存统计:")
        print(f"  GET 命中: {stats['hits']}")
        print(f"  GET 未命中: {stats['misses']}")
        print(f"  GET 命中率: {stats['hit_rate']:.2f}%")
        print(f"  手动命中: {stats.get('manual_hits', 0)}")
        print(f"  手动未命中: {stats.get('manual_misses', 0)}")
        
        # 计算综合命中率
        total_requests = stats['hits'] + stats['misses'] + stats.get('manual_hits', 0) + stats.get('manual_misses', 0)
        if total_requests > 0:
            overall_hit_rate = (stats['hits'] + stats.get('manual_hits', 0)) / total_requests * 100
            print(f"  综合命中率: {overall_hit_rate:.2f}%")
    
    # 总体评价
    print(f"\n{'='*80}")
    print("性能提升总结")
    print(f"{'='*80}")
    
    if qps_improvement > 0:
        print(f"✅ QPS 提升: {qps_improvement:.1f}%")
    if lat_improvement > 0:
        print(f"✅ 延迟降低: {lat_improvement:.1f}%")
    
    if qps_improvement >= 50:
        print("\n🏆 性能提升显著！缓存层工作正常。")
    elif qps_improvement >= 20:
        print("\n✅ 性能有明显提升。")
    elif qps_improvement > 0:
        print("\n⚠️ 性能有轻微提升，可以进一步优化。")
    else:
        print("\n⚠️ 性能未提升，可能因为：")
        print("   1. SQLite 本身性能很好，缓存开销抵消了收益")
        print("   2. 测试规模较小，缓存优势不明显")
        print("   3. 内存缓存的开销与数据库访问相近")

# ==================== 主函数 ====================

def main():
    print("=" * 80)
    print("Phase 48: 缓存性能对比测试")
    print("=" * 80)
    
    # 使用小规模测试（加快速度）
    config = TEST_CONFIGS["small"]
    num_tenants = config["tenants"]
    num_operations = config["operations"]
    
    print(f"\n测试规模: {num_tenants} 租户, {num_operations} 操作")
    
    # 无缓存测试
    without_cache = benchmark_without_cache(num_tenants, num_operations)
    
    # 有缓存测试
    with_cache = benchmark_with_cache(num_tenants, num_operations)
    
    # 对比分析
    compare_results(without_cache, with_cache)
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
