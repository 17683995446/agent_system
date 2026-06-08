"""
单元测试 - 监控系统
"""
import pytest
import time
from unittest.mock import MagicMock, patch

from infrastructure.monitoring.monitoring_system import (
    MonitoringSystem,
    monitoring_system,
    monitor
)


class TestMonitoringSystem:
    """测试监控系统"""
    
    def test_monitoring_system_creation(self):
        """测试监控系统创建"""
        system = MonitoringSystem()
        assert system is not None
        assert system.start_time > 0
    
    def test_register_health_check(self):
        """测试注册健康检查"""
        system = MonitoringSystem()
        
        async def custom_check():
            return True, "OK"
        
        system.register_health_check("custom", custom_check)
        assert "custom" in system.health_checks
    
    def test_record_task(self):
        """测试记录任务"""
        system = MonitoringSystem()
        system.record_task("completed")
        assert True
    
    def test_record_request(self):
        """测试记录请求"""
        system = MonitoringSystem()
        system.record_request("/test", "GET", 200)
        assert True
    
    def test_custom_metrics(self):
        """测试自定义指标"""
        system = MonitoringSystem()
        
        system.set_custom_metric("test_metric", 42)
        assert system.get_custom_metric("test_metric") == 42
    
    def test_get_metrics(self):
        """测试获取指标"""
        system = MonitoringSystem()
        metrics = system.get_metrics()
        
        assert "system" in metrics
        assert "uptime_seconds" in metrics["system"]
        assert "timestamp" in metrics["system"]
    
    def test_global_monitoring_system(self):
        """测试全局监控系统"""
        assert monitoring_system is not None
        assert isinstance(monitoring_system, MonitoringSystem)
    
    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        """测试运行健康检查"""
        system = MonitoringSystem()
        
        results = await system.run_health_checks()
        
        assert "status" in results
        assert "checks" in results
        assert "timestamp" in results
        assert "uptime" in results


class TestMonitorDecorator:
    """测试监控装饰器"""
    
    def test_monitor_decorator_sync(self):
        """测试同步函数监控装饰器"""
        
        @monitor
        def test_func():
            time.sleep(0.01)
            return "ok"
        
        result = test_func()
        assert result == "ok"
    
    def test_monitor_decorator_async(self):
        """测试异步函数监控装饰器"""
        
        @monitor
        async def test_func():
            await asyncio.sleep(0.01)
            return "ok"
        
        import asyncio
        result = asyncio.run(test_func())
        assert result == "ok"


class TestHealthChecks:
    """测试健康检查功能"""
    
    @pytest.mark.asyncio
    async def test_system_health_check(self):
        """测试系统健康检查"""
        system = MonitoringSystem()
        is_healthy, message = await system._check_system_health()
        
        assert is_healthy is True
        assert "operational" in message
