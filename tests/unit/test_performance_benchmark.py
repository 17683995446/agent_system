"""
测试 - 性能基准测试模块单元测试
"""
import pytest
import asyncio
from application_service.performance_benchmark_runner import (
    PerformanceBenchmark,
    ConcurrentBenchmark,
    BenchmarkResult,
)


class TestPerformanceBenchmark:
    """测试性能基准测试器"""
    
    def test_benchmark_sync_function(self):
        """测试同步函数基准测试"""
        benchmark = PerformanceBenchmark(min_runs=5)
        
        def sample_function():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        result = benchmark.benchmark_sync("sample_sync", sample_function, runs=10)
        
        assert isinstance(result, BenchmarkResult)
        assert result.name == "sample_sync"
        assert result.total_runs == 10
        assert result.total_time > 0
        assert result.avg_time > 0
        assert result.ops_per_second > 0
    
    @pytest.mark.asyncio
    async def test_benchmark_async_function(self):
        """测试异步函数基准测试"""
        benchmark = PerformanceBenchmark(min_runs=5)
        
        async def async_sample():
            await asyncio.sleep(0.001)
            return 42
        
        result = await benchmark.benchmark_async("sample_async", async_sample, runs=5)
        
        assert isinstance(result, BenchmarkResult)
        assert result.name == "sample_async"
        assert result.total_runs == 5
        assert result.total_time > 0
    
    def test_benchmark_with_warmup(self):
        """测试带预热的基准测试"""
        benchmark = PerformanceBenchmark(warmup_runs=2, min_runs=5)
        counter = {"value": 0}
        
        def increment():
            counter["value"] += 1
            return counter["value"]
        
        result = benchmark.benchmark_sync("warmup_test", increment, runs=5)
        
        assert result.total_runs == 5
        assert counter["value"] == 7
    
    def test_get_summary(self):
        """测试获取摘要"""
        benchmark = PerformanceBenchmark(min_runs=3)
        
        def func1():
            return sum(range(100))
        
        def func2():
            return [i * 2 for i in range(100)]
        
        benchmark.benchmark_sync("func1", func1, runs=5)
        benchmark.benchmark_sync("func2", func2, runs=5)
        
        summary = benchmark.get_summary()
        
        assert summary["total_benchmarks"] == 2
        assert "results" in summary
        assert len(summary["results"]) == 2


class TestConcurrentBenchmark:
    """测试并发基准测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmark(self):
        """测试并发基准测试"""
        runner = ConcurrentBenchmark()
        
        async def sample_task():
            await asyncio.sleep(0.01)
            return "completed"
        
        result = await runner.benchmark_concurrent(
            name="concurrent_test",
            func=sample_task,
            concurrency=5,
            total_requests=10
        )
        
        assert result["name"] == "concurrent_test"
        assert result["concurrency"] == 5
        assert result["total_requests"] == 10
        assert result["successful"] == 10
        assert result["errors"] == 0
        assert result["requests_per_second"] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmark_with_errors(self):
        """测试带错误的并发基准测试"""
        runner = ConcurrentBenchmark()
        call_count = {"count": 0}
        
        async def failing_task():
            call_count["count"] += 1
            if call_count["count"] <= 3:
                raise ValueError("Simulated error")
            return "success"
        
        result = await runner.benchmark_concurrent(
            name="error_test",
            func=failing_task,
            concurrency=2,
            total_requests=5
        )
        
        assert result["errors"] == 3
        assert result["successful"] == 2
    
    @pytest.mark.asyncio
    async def test_get_concurrent_summary(self):
        """测试获取并发摘要"""
        runner = ConcurrentBenchmark()
        
        async def sample():
            await asyncio.sleep(0.001)
        
        await runner.benchmark_concurrent("test1", sample, 5, 10)
        await runner.benchmark_concurrent("test2", sample, 10, 20)
        
        summary = runner.get_summary()
        
        assert summary["total_tests"] == 2
        assert "max_rps" in summary
        assert "results" in summary
