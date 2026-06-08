"""
集成测试 - 基础设施模块
测试日志、缓存、监控等基础设施的集成
"""
import pytest
import time
from unittest.mock import MagicMock, patch

from infrastructure.logging.logging_system import get_logger, StructuredLogger
from infrastructure.cache.cache_manager import CacheManager, default_cache
from infrastructure.monitoring.monitoring_system import MonitoringSystem, monitoring_system


class TestInfrastructureIntegration:
    """测试基础设施集成"""
    
    def test_logging_and_cache_integration(self):
        """测试日志和缓存集成"""
        logger = get_logger("test_integration")
        
        cache = CacheManager(maxsize=100)
        cache.set("test_key", "test_value")
        
        logger.info("缓存操作完成", key="test_key", value="test_value")
        
        assert cache.get("test_key") == "test_value"
    
    def test_monitoring_and_logging_integration(self):
        """测试监控和日志集成"""
        logger = get_logger("monitor_test")
        
        start_time = time.time()
        
        monitoring_system.record_task("started")
        
        elapsed = time.time() - start_time
        
        logger.info("任务监控记录完成", elapsed=elapsed)
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_full_infrastructure_stack(self):
        """测试完整基础设施栈"""
        logger = get_logger("full_stack")
        
        cache = CacheManager(cache_type="ttl", maxsize=100, ttl=60)
        cache.set("integrated_data", {"status": "active", "timestamp": time.time()})
        
        monitoring_system.record_request("/integration/test", "GET", 200)
        
        health_data = await monitoring_system.run_health_checks()
        
        cached_data = cache.get("integrated_data")
        assert cached_data is not None
        assert health_data["status"] in ["healthy", "degraded"]
        
        logger.info("完整基础设施栈测试完成")


class TestCacheWithMonitoring:
    """测试带监控的缓存"""
    
    def test_cache_hits_metrics(self):
        """测试缓存命中统计"""
        cache = CacheManager(maxsize=100)
        
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}")
        
        for i in range(5):
            cache.get(f"key_{i}")
        
        for i in range(10, 20):
            cache.get(f"key_{i}")
        
        stats = cache.get_stats()
        monitoring_system.set_custom_metric("cache_hit_rate", stats["hit_rate"])
        
        assert stats["hits"] == 5
        assert stats["misses"] == 10


class TestSystemWithAllInfrastructure:
    """测试带所有基础设施的系统"""
    
    def test_all_modules_initialization(self):
        """测试所有模块初始化"""
        logger = get_logger("init_test")
        
        cache = default_cache
        monitor = monitoring_system
        
        logger.info("所有模块初始化检查", 
                    cache_available=cache is not None,
                    monitor_available=monitor is not None)
        
        assert cache is not None
        assert monitor is not None
    
    def test_error_handling_flow(self):
        """测试错误处理流程"""
        logger = get_logger("error_test")
        
        try:
            cache = CacheManager(maxsize=10)
            cache.get("nonexistent_key")
            
            raise ValueError("模拟错误")
        except Exception as e:
            logger.error("错误处理测试", error=str(e))
            monitoring_system.record_task("failed")
            assert True
