"""
应用服务层 - 性能基准测试模块
提供系统性能测试和性能指标收集功能
"""
import time
import asyncio
import statistics
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from contextlib import asynccontextmanager


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    total_runs: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    ops_per_second: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_runs": self.total_runs,
            "total_time": round(self.total_time, 4),
            "avg_time": round(self.avg_time, 4),
            "min_time": round(self.min_time, 4),
            "max_time": round(self.max_time, 4),
            "std_dev": round(self.std_dev, 4),
            "ops_per_second": round(self.ops_per_second, 2),
            "timestamp": self.timestamp,
        }


class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self, warmup_runs: int = 3, min_runs: int = 10):
        self.warmup_runs = warmup_runs
        self.min_runs = min_runs
        self.results: List[BenchmarkResult] = []
    
    async def benchmark_async(
        self,
        name: str,
        func: Callable,
        *args,
        runs: Optional[int] = None,
        **kwargs
    ) -> BenchmarkResult:
        """基准测试异步函数"""
        runs = runs or self.min_runs
        
        for _ in range(self.warmup_runs):
            await func(*args, **kwargs)
        
        times: List[float] = []
        start_total = time.perf_counter()
        
        for _ in range(runs):
            start = time.perf_counter()
            await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = time.perf_counter() - start_total
        
        result = self._create_result(name, times, total_time, runs)
        self.results.append(result)
        return result
    
    def benchmark_sync(
        self,
        name: str,
        func: Callable,
        *args,
        runs: Optional[int] = None,
        **kwargs
    ) -> BenchmarkResult:
        """基准测试同步函数"""
        runs = runs or self.min_runs
        
        for _ in range(self.warmup_runs):
            func(*args, **kwargs)
        
        times: List[float] = []
        start_total = time.perf_counter()
        
        for _ in range(runs):
            start = time.perf_counter()
            func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = time.perf_counter() - start_total
        
        result = self._create_result(name, times, total_time, runs)
        self.results.append(result)
        return result
    
    def _create_result(
        self,
        name: str,
        times: List[float],
        total_time: float,
        runs: int
    ) -> BenchmarkResult:
        """创建结果对象"""
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_second = runs / total_time if total_time > 0 else 0.0
        
        return BenchmarkResult(
            name=name,
            total_runs=runs,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            ops_per_second=ops_per_second,
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        return {
            "total_benchmarks": len(self.results),
            "fastest": min(self.results, key=lambda x: x.avg_time).name,
            "slowest": max(self.results, key=lambda x: x.avg_time).name,
            "overall_ops_per_second": sum(r.ops_per_second for r in self.results),
            "results": [r.to_dict() for r in self.results],
        }


class MemoryProfiler:
    """内存性能分析器"""
    
    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []
    
    @asynccontextmanager
    async def profile_section(self, name: str):
        """分析代码段"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            end_memory = self._get_memory_usage()
            
            snapshot = {
                "name": name,
                "duration": elapsed,
                "memory_start": start_memory,
                "memory_end": end_memory,
                "memory_delta": end_memory - start_memory,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.snapshots.append(snapshot)
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def get_report(self) -> Dict[str, Any]:
        """获取分析报告"""
        if not self.snapshots:
            return {"error": "No profiling data available"}
        
        return {
            "total_sections": len(self.snapshots),
            "total_duration": sum(s["duration"] for s in self.snapshots),
            "max_memory_delta": max(s["memory_delta"] for s in self.snapshots),
            "snapshots": self.snapshots,
        }


class ConcurrentBenchmark:
    """并发性能基准测试"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
    
    async def benchmark_concurrent(
        self,
        name: str,
        func: Callable,
        concurrency: int,
        total_requests: int,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """并发基准测试"""
        semaphore = asyncio.Semaphore(concurrency)
        times: List[float] = []
        errors = 0
        
        async def bounded_task():
            nonlocal errors
            try:
                start = time.perf_counter()
                await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            except Exception:
                errors += 1
        
        start_total = time.perf_counter()
        
        tasks = [bounded_task() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_total
        
        result = {
            "name": name,
            "concurrency": concurrency,
            "total_requests": total_requests,
            "successful": len(times),
            "errors": errors,
            "total_time": round(total_time, 4),
            "avg_response_time": round(statistics.mean(times), 4) if times else 0,
            "min_response_time": round(min(times), 4) if times else 0,
            "max_response_time": round(max(times), 4) if times else 0,
            "requests_per_second": round(total_requests / total_time, 2) if total_time > 0 else 0,
        }
        
        self.results.append(result)
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self.results:
            return {"error": "No concurrent benchmark results"}
        
        return {
            "total_tests": len(self.results),
            "max_rps": max(r["requests_per_second"] for r in self.results),
            "avg_response_time": statistics.mean(r["avg_response_time"] for r in self.results),
            "results": self.results,
        }


benchmark_runner = PerformanceBenchmark()
concurrent_runner = ConcurrentBenchmark()
memory_profiler = MemoryProfiler()
