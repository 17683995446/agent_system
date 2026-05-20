"""
基础设施 - 监控系统（增强版）
提供健康检查和监控功能
"""
import time
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import wraps
import asyncio


def noop(*args, **kwargs):
    """空函数，用于替代不存在的依赖"""
    return None


try:
    from prometheus_client import Counter, Histogram, Gauge
    
    _request_count = Counter(
        "agent_evolution_requests_total",
        "Total number of requests",
        ["endpoint", "method", "status"]
    )
    
    _request_duration = Histogram(
        "agent_evolution_request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"]
    )
    
    _task_count = Counter(
        "agent_evolution_tasks_total",
        "Total number of tasks processed",
        ["status"]
    )
    
    _memory_usage = Gauge(
        "agent_evolution_memory_usage",
        "Memory usage percentage"
    )
    
    _system_uptime = Gauge(
        "agent_evolution_system_uptime_seconds",
        "System uptime in seconds"
    )
    
    has_prometheus = True
except ImportError:
    has_prometheus = False
    # 使用空的占位符
    _request_count = None
    _request_duration = None
    _task_count = None
    _memory_usage = None
    _system_uptime = None


class MonitoringSystem:
    """监控系统"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        self.custom_metrics: Dict[str, Any] = {}
        self.request_tracking: Dict[str, list] = {}
        
        self.register_health_check("system", self._check_system_health)
        self.register_health_check("memory", self._check_memory_health)
        self.register_health_check("disk", self._check_disk_health)
        self.register_health_check("python", self._check_python_runtime)
    
    def register_health_check(self, name: str, check_func: callable):
        """注册健康检查"""
        self.health_checks[name] = {
            "func": check_func,
            "last_check": None,
            "status": "unknown",
            "message": ""
        }
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        for name, check_info in self.health_checks.items():
            try:
                is_healthy, message = await check_info["func"]()
                status = "healthy" if is_healthy else "unhealthy"
                
                if status == "unhealthy" and results["status"] == "healthy":
                    results["status"] = "degraded"
                
                check_info["last_check"] = datetime.now(timezone.utc).isoformat()
                check_info["status"] = status
                check_info["message"] = message
                
                results["checks"][name] = {
                    "status": status,
                    "message": message,
                    "last_check": check_info["last_check"],
                }
            except Exception as e:
                results["status"] = "unhealthy"
                check_info["status"] = "unhealthy"
                check_info["message"] = str(e)
                check_info["last_check"] = datetime.now(timezone.utc).isoformat()
                results["checks"][name] = {
                    "status": "unhealthy",
                    "message": str(e),
                    "last_check": check_info["last_check"],
                }
        
        results["uptime"] = time.time() - self.start_time
        results["uptime_formatted"] = self._format_uptime(results["uptime"])
        
        return results
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    async def _check_system_health(self):
        """检查系统健康"""
        return True, "System is operational"
    
    async def _check_memory_health(self):
        """检查内存健康"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            message = f"Memory usage: {memory_percent:.1f}%, RSS: {memory_info.rss / 1024 / 1024:.1f}MB"
            
            if memory_percent > 90:
                return False, f"High memory usage: {message}"
            return True, message
        except ImportError:
            return True, "psutil not available, skipping memory check"
        except Exception as e:
            return False, f"Memory check failed: {str(e)}"
    
    async def _check_disk_health(self):
        """检查磁盘健康"""
        try:
            import shutil
            disk_usage = shutil.disk_usage("/")
            total_gb = disk_usage.total / (1024 ** 3)
            used_gb = disk_usage.used / (1024 ** 3)
            free_gb = disk_usage.free / (1024 ** 3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            message = f"Disk: {used_gb:.1f}/{total_gb:.1f}GB used ({usage_percent:.1f}%), {free_gb:.1f}GB free"
            
            if usage_percent > 90:
                return False, f"Low disk space: {message}"
            return True, message
        except Exception as e:
            return False, f"Disk check failed: {str(e)}"
    
    async def _check_python_runtime(self):
        """检查Python运行时"""
        try:
            version = sys.version
            executable = sys.executable
            message = f"Python {version.split()[0]} - {executable}"
            return True, message
        except Exception as e:
            return False, f"Python runtime check failed: {str(e)}"
    
    def record_request(self, endpoint: str, method: str, status_code: int):
        """记录请求"""
        if has_prometheus and _request_count:
            _request_count.labels(endpoint=endpoint, method=method, status=str(status_code)).inc()
        
        # 简单的请求跟踪
        if endpoint not in self.request_tracking:
            self.request_tracking[endpoint] = []
        
        self.request_tracking[endpoint].append({
            "method": method,
            "status": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # 只保留最近100个请求
        if len(self.request_tracking[endpoint]) > 100:
            self.request_tracking[endpoint] = self.request_tracking[endpoint][-100:]
    
    def record_task(self, status: str):
        """记录任务"""
        if has_prometheus and _task_count:
            _task_count.labels(status=status).inc()
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        metrics = {
            "system": {
                "uptime_seconds": time.time() - self.start_time,
                "uptime_formatted": self._format_uptime(time.time() - self.start_time),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "custom": self.custom_metrics,
            "prometheus_available": has_prometheus,
            "request_tracking": self.request_tracking
        }
        
        # 添加系统资源信息
        try:
            import psutil
            process = psutil.Process()
            metrics["system"]["memory"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "percent": process.memory_percent()
            }
            metrics["system"]["cpu"] = {
                "percent": process.cpu_percent(interval=None)
            }
        except ImportError:
            pass
        
        return metrics
    
    def set_custom_metric(self, name: str, value: Any):
        """设置自定义指标"""
        self.custom_metrics[name] = value
    
    def get_custom_metric(self, name: str) -> Any:
        """获取自定义指标"""
        return self.custom_metrics.get(name)


def monitor(func):
    """监控装饰器 - 监控函数执行"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            raise
    
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


monitoring_system = MonitoringSystem()
