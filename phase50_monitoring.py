"""
Phase 50: Prometheus 监控、告警与可观测性
实现完整的监控指标体系和告警机制
"""

import os
import sys
import time
import uuid
import random
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib

# 配置日志
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase50_monitoring.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(thread)d:%(name)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 指标类型 ====================

class MetricType(Enum):
    """Prometheus指标类型"""
    COUNTER = "counter"          # 累加计数器
    GAUGE = "gauge"              # 可增可减的仪表
    HISTOGRAM = "histogram"      # 直方图
    SUMMARY = "summary"          # 摘要

# ==================== 指标数据结构 ====================

@dataclass
class HistogramBucket:
    """直方图桶"""
    le: float  # "less than or equal to"
    count: int = 0

@dataclass
class MetricValue:
    """指标值"""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

@dataclass
class Metric:
    """Prometheus风格指标"""
    name: str
    metric_type: MetricType
    help_text: str
    values: List[MetricValue] = field(default_factory=list)
    buckets: List[HistogramBucket] = field(default_factory=list)  # 直方图专用
    sum: float = 0.0  # 直方图/摘要专用
    count: int = 0  # 直方图/摘要专用

# ==================== 指标注册表 ====================

class MetricRegistry:
    """指标注册表"""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.RLock()
        logger.info("[MetricRegistry] 指标注册表初始化")
    
    def register(self, metric: Metric) -> bool:
        """注册指标"""
        with self._lock:
            if metric.name in self._metrics:
                logger.warning(f"[MetricRegistry] 指标已存在: {metric.name}")
                return False
            
            self._metrics[metric.name] = metric
            logger.debug(f"[MetricRegistry] 注册指标: {metric.name} ({metric.metric_type})")
            return True
    
    def get(self, name: str) -> Optional[Metric]:
        """获取指标"""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all(self) -> Dict[str, Metric]:
        """获取所有指标"""
        with self._lock:
            return dict(self._metrics)
    
    def unregister(self, name: str) -> bool:
        """注销指标"""
        with self._lock:
            if name in self._metrics:
                del self._metrics[name]
                logger.debug(f"[MetricRegistry] 注销指标: {name}")
                return True
            return False

# ==================== 核心监控系统 ====================

class PrometheusMetrics:
    """Prometheus 指标收集器"""
    
    def __init__(self, registry: MetricRegistry = None):
        self.registry = registry or MetricRegistry()
        self._lock = threading.RLock()
        
        # 初始化基础指标
        self._init_basic_metrics()
        
        logger.info("[PrometheusMetrics] Prometheus指标系统初始化完成")
    
    def _init_basic_metrics(self):
        """初始化基础指标"""
        
        # 1. 系统运行时间
        self.register_metric(
            Metric(
                name="system_uptime_seconds",
                metric_type=MetricType.GAUGE,
                help_text="System uptime in seconds"
            )
        )
        
        # 2. API请求计数
        self.register_metric(
            Metric(
                name="http_requests_total",
                metric_type=MetricType.COUNTER,
                help_text="Total number of HTTP requests"
            )
        )
        
        # 3. API请求延迟直方图
        self.register_metric(
            Metric(
                name="http_request_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                help_text="HTTP request duration in seconds",
                buckets=[
                    HistogramBucket(le=0.005),
                    HistogramBucket(le=0.01),
                    HistogramBucket(le=0.025),
                    HistogramBucket(le=0.05),
                    HistogramBucket(le=0.1),
                    HistogramBucket(le=0.25),
                    HistogramBucket(le=0.5),
                    HistogramBucket(le=1.0),
                    HistogramBucket(le=2.5),
                    HistogramBucket(le=5.0),
                    HistogramBucket(le=10.0),
                ]
            )
        )
        
        # 4. 活跃连接数
        self.register_metric(
            Metric(
                name="active_connections",
                metric_type=MetricType.GAUGE,
                help_text="Number of active connections"
            )
        )
        
        # 5. 错误计数
        self.register_metric(
            Metric(
                name="errors_total",
                metric_type=MetricType.COUNTER,
                help_text="Total number of errors"
            )
        )
        
        # 6. 内存使用
        self.register_metric(
            Metric(
                name="memory_usage_bytes",
                metric_type=MetricType.GAUGE,
                help_text="Memory usage in bytes"
            )
        )
        
        # 7. CPU使用率
        self.register_metric(
            Metric(
                name="cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                help_text="CPU usage percentage"
            )
        )
        
        # 8. 租户数量
        self.register_metric(
            Metric(
                name="tenants_total",
                metric_type=MetricType.GAUGE,
                help_text="Total number of tenants"
            )
        )
        
        # 9. 服务实例数量
        self.register_metric(
            Metric(
                name="service_instances_total",
                metric_type=MetricType.GAUGE,
                help_text="Total number of service instances"
            )
        )
        
        # 10. 缓存命中率
        self.register_metric(
            Metric(
                name="cache_hits_total",
                metric_type=MetricType.COUNTER,
                help_text="Total cache hits"
            )
        )
        
        self.register_metric(
            Metric(
                name="cache_misses_total",
                metric_type=MetricType.COUNTER,
                help_text="Total cache misses"
            )
        )
        
        # 11. 安全审计
        self.register_metric(
            Metric(
                name="security_events_total",
                metric_type=MetricType.COUNTER,
                help_text="Total security events"
            )
        )
        
        # 12. API Key使用
        self.register_metric(
            Metric(
                name="api_key_usage_total",
                metric_type=MetricType.COUNTER,
                help_text="Total API key usage"
            )
        )
    
    def register_metric(self, metric: Metric) -> bool:
        """注册指标"""
        logger.debug(f"[PrometheusMetrics] 注册指标: {metric.name}")
        return self.registry.register(metric)
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1.0):
        """计数器递增"""
        with self._lock:
            metric = self.registry.get(name)
            if not metric or metric.metric_type != MetricType.COUNTER:
                logger.warning(f"[PrometheusMetrics] 无效的Counter: {name}")
                return
            
            metric.values.append(MetricValue(
                value=metric.values[-1].value + value if metric.values else value,
                labels=labels or {}
            ))
            # 保留最近1000个点
            if len(metric.values) > 1000:
                metric.values = metric.values[-1000:]
            
            logger.debug(f"[PrometheusMetrics] Counter {name} += {value} (labels={labels})")
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置Gauge值"""
        with self._lock:
            metric = self.registry.get(name)
            if not metric or metric.metric_type != MetricType.GAUGE:
                logger.warning(f"[PrometheusMetrics] 无效的Gauge: {name}")
                return
            
            metric.values.append(MetricValue(
                value=value,
                labels=labels or {}
            ))
            if len(metric.values) > 1000:
                metric.values = metric.values[-1000:]
            
            logger.debug(f"[PrometheusMetrics] Gauge {name} = {value} (labels={labels})")
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """观察直方图值"""
        with self._lock:
            metric = self.registry.get(name)
            if not metric or metric.metric_type != MetricType.HISTOGRAM:
                logger.warning(f"[PrometheusMetrics] 无效的Histogram: {name}")
                return
            
            # 更新桶计数
            for bucket in metric.buckets:
                if value <= bucket.le:
                    bucket.count += 1
            
            # 更新总和和计数
            metric.sum += value
            metric.count += 1
            
            # 记录原始值
            metric.values.append(MetricValue(
                value=value,
                labels=labels or {}
            ))
            if len(metric.values) > 1000:
                metric.values = metric.values[-1000:]
            
            logger.debug(f"[PrometheusMetrics] Histogram {name} observe {value}")
    
    def export_metrics(self) -> str:
        """导出Prometheus格式指标"""
        lines = []
        with self._lock:
            for name, metric in self.registry.get_all().items():
                if not metric.values:
                    continue
                
                # HELP行
                lines.append(f"# HELP {metric.name} {metric.help_text}")
                lines.append(f"# TYPE {metric.name} {metric.metric_type.value}")
                
                # 值行
                for val in metric.values:
                    label_str = ""
                    if val.labels:
                        label_parts = []
                        for k, v in val.labels.items():
                            label_parts.append(f'{k}="{v}"')
                        label_str = "{" + ",".join(label_parts) + "}"
                    
                    timestamp = int(val.timestamp * 1000)
                    lines.append(f"{metric.name}{label_str} {val.value} {timestamp}")
                
                # 直方图特殊处理
                if metric.metric_type == MetricType.HISTOGRAM:
                    for bucket in metric.buckets:
                        label_str = "{le=\"" + str(bucket.le) + "\"}"
                        lines.append(f"{metric.name}_bucket{label_str} {bucket.count}")
                    lines.append(f"{metric.name}_sum {metric.sum}")
                    lines.append(f"{metric.name}_count {metric.count}")
            
            return "\n".join(lines)
    
    def get_current_values(self) -> Dict[str, Any]:
        """获取当前指标值（JSON格式）"""
        result = {}
        with self._lock:
            for name, metric in self.registry.get_all().items():
                if metric.values:
                    current_val = metric.values[-1].value
                    result[name] = current_val
        return result

# ==================== 告警规则 ====================

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_name: str
    condition: Callable[[float], bool]
    level: AlertLevel
    message: str
    duration_seconds: float = 30.0
    active: bool = True

@dataclass
class Alert:
    """告警事件"""
    rule_name: str
    level: AlertLevel
    message: str
    start_time: datetime
    resolved: bool = False
    resolve_time: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)

# ==================== 告警管理器 ====================

class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
        self._rules: List[AlertRule] = []
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._lock = threading.RLock()
        self._check_thread = None
        self._running = False
        
        # 初始化基础告警规则
        self._init_basic_rules()
        
        logger.info("[AlertManager] 告警管理器初始化完成")
    
    def _init_basic_rules(self):
        """初始化基础告警规则"""
        
        # 1. 错误率过高告警
        self.add_rule(AlertRule(
            name="HighErrorRate",
            metric_name="errors_total",
            condition=lambda x: x > 100,
            level=AlertLevel.WARNING,
            message="Error rate is too high"
        ))
        
        # 2. CPU使用率过高
        self.add_rule(AlertRule(
            name="HighCPUUsage",
            metric_name="cpu_usage_percent",
            condition=lambda x: x > 80,
            level=AlertLevel.WARNING,
            message="CPU usage is high (>80%)"
        ))
        
        # 3. CPU使用率危急
        self.add_rule(AlertRule(
            name="CriticalCPUUsage",
            metric_name="cpu_usage_percent",
            condition=lambda x: x > 95,
            level=AlertLevel.CRITICAL,
            message="CPU usage is critically high (>95%)"
        ))
        
        # 4. 活跃连接数过多
        self.add_rule(AlertRule(
            name="HighConnectionCount",
            metric_name="active_connections",
            condition=lambda x: x > 1000,
            level=AlertLevel.WARNING,
            message="Active connection count is too high (>1000)"
        ))
        
        # 5. 缓存命中率过低
        self.add_rule(AlertRule(
            name="LowCacheHitRate",
            metric_name="cache_misses_total",
            condition=lambda x: x > 500,
            level=AlertLevel.WARNING,
            message="Cache miss rate is too high"
        ))
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self._rules.append(rule)
            logger.debug(f"[AlertManager] 添加告警规则: {rule.name}")
    
    def check_rules(self) -> List[Alert]:
        """检查告警规则"""
        new_alerts = []
        current_values = self.metrics.get_current_values()
        
        with self._lock:
            for rule in self._rules:
                if not rule.active:
                    continue
                
                if rule.metric_name not in current_values:
                    continue
                
                value = current_values[rule.metric_name]
                
                try:
                    condition_met = rule.condition(value)
                except Exception as e:
                    logger.error(f"[AlertManager] 告警规则检查失败: {rule.name} - {e}")
                    continue
                
                if condition_met:
                    if rule.name not in self._active_alerts:
                        # 新告警触发
                        alert = Alert(
                            rule_name=rule.name,
                            level=rule.level,
                            message=rule.message,
                            start_time=datetime.now(),
                            labels={"metric": rule.metric_name, "value": str(value)}
                        )
                        self._active_alerts[rule.name] = alert
                        self._alert_history.append(alert)
                        new_alerts.append(alert)
                        
                        logger.warning(f"[AlertManager] 告警触发: {rule.name} - {rule.message}")
                        
                        # 记录安全事件
                        self.metrics.increment_counter(
                            "security_events_total",
                            {"type": "alert", "rule": rule.name, "level": rule.level.value}
                        )
                else:
                    if rule.name in self._active_alerts:
                        # 告警解除
                        alert = self._active_alerts[rule.name]
                        alert.resolved = True
                        alert.resolve_time = datetime.now()
                        del self._active_alerts[rule.name]
                        
                        logger.info(f"[AlertManager] 告警解除: {rule.name}")
            
            return new_alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            return list(self._active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            return self._alert_history[-limit:]
    
    def start_monitoring(self, check_interval: float = 5.0):
        """启动监控"""
        if self._running:
            logger.warning("[AlertManager] 监控已在运行")
            return
        
        self._running = True
        
        def monitor_loop():
            while self._running:
                try:
                    self.check_rules()
                except Exception as e:
                    logger.error(f"[AlertManager] 监控循环错误: {e}")
                time.sleep(check_interval)
        
        self._check_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._check_thread.start()
        logger.info("[AlertManager] 告警监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=1.0)
        logger.info("[AlertManager] 告警监控已停止")

# ==================== 监控收集器 ====================

class SystemMonitor:
    """系统监控收集器"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
        self._start_time = time.time()
        self._lock = threading.RLock()
        self._collector_thread = None
        self._running = False
        
        logger.info("[SystemMonitor] 系统监控收集器初始化完成")
    
    def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # 1. 更新运行时间
            uptime = time.time() - self._start_time
            self.metrics.set_gauge("system_uptime_seconds", uptime)
            
            # 2. 模拟内存使用
            import psutil
            try:
                process = psutil.Process()
                mem_info = process.memory_info()
                self.metrics.set_gauge("memory_usage_bytes", mem_info.rss)
                
                cpu_percent = process.cpu_percent()
                self.metrics.set_gauge("cpu_usage_percent", cpu_percent)
            except (ImportError, Exception):
                # 没有psutil时使用模拟值
                import random
                self.metrics.set_gauge("memory_usage_bytes", 100000000 + random.randint(0, 50000000))
                self.metrics.set_gauge("cpu_usage_percent", 30 + random.randint(0, 40))
            
            logger.debug("[SystemMonitor] 系统指标收集完成")
            
        except Exception as e:
            logger.error(f"[SystemMonitor] 系统指标收集失败: {e}")
    
    def start_collection(self, interval: float = 10.0):
        """启动指标收集"""
        if self._running:
            logger.warning("[SystemMonitor] 收集已在运行")
            return
        
        self._running = True
        
        def collect_loop():
            while self._running:
                try:
                    self.collect_system_metrics()
                except Exception as e:
                    logger.error(f"[SystemMonitor] 收集循环错误: {e}")
                time.sleep(interval)
        
        self._collector_thread = threading.Thread(target=collect_loop, daemon=True)
        self._collector_thread.start()
        logger.info("[SystemMonitor] 系统指标收集已启动")
    
    def stop_collection(self):
        """停止指标收集"""
        self._running = False
        if self._collector_thread:
            self._collector_thread.join(timeout=1.0)
        logger.info("[SystemMonitor] 系统指标收集已停止")

# ==================== 全局实例 ====================

_metrics = None
_alert_manager = None
_system_monitor = None
_lock = threading.Lock()

def get_metrics() -> PrometheusMetrics:
    """获取全局指标实例"""
    global _metrics
    if _metrics is None:
        with _lock:
            if _metrics is None:
                _metrics = PrometheusMetrics()
    return _metrics

def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        with _lock:
            if _alert_manager is None:
                _alert_manager = AlertManager(get_metrics())
    return _alert_manager

def get_system_monitor() -> SystemMonitor:
    """获取全局系统监控器"""
    global _system_monitor
    if _system_monitor is None:
        with _lock:
            if _system_monitor is None:
                _system_monitor = SystemMonitor(get_metrics())
    return _system_monitor

def start_monitoring():
    """启动完整监控"""
    get_system_monitor().start_collection()
    get_alert_manager().start_monitoring()
    logger.info("=" * 80)
    logger.info("Phase 50: 完整监控系统已启动")
    logger.info("=" * 80)

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 50: Prometheus监控、告警与可观测性测试")
    print("=" * 80)
    
    # 初始化
    metrics = get_metrics()
    alert_manager = get_alert_manager()
    monitor = get_system_monitor()
    
    # 模拟一些请求
    print("\n模拟HTTP请求...")
    for i in range(100):
        metrics.increment_counter("http_requests_total", {"method": "GET", "endpoint": "/api/tenant"})
        duration = 0.001 + (i * 0.0001)
        metrics.observe_histogram("http_request_duration_seconds", duration)
    
    # 模拟缓存
    print("\n模拟缓存操作...")
    for i in range(100):
        if random.random() < 0.8:
            metrics.increment_counter("cache_hits_total")
        else:
            metrics.increment_counter("cache_misses_total")
    
    # 模拟租户
    print("\n模拟租户...")
    metrics.set_gauge("tenants_total", 100)
    metrics.set_gauge("service_instances_total", 50)
    metrics.set_gauge("active_connections", 150)
    
    # 导出指标
    print("\n导出Prometheus格式指标:")
    prometheus_output = metrics.export_metrics()
    print(prometheus_output[:500] + ("..." if len(prometheus_output) > 500 else ""))
    
    # 获取当前值
    print("\n当前指标值:")
    current_values = metrics.get_current_values()
    for name, value in current_values.items():
        print(f"  {name} = {value}")
    
    # 检查告警
    print("\n检查告警规则...")
    alerts = alert_manager.check_rules()
    print(f"新触发告警: {len(alerts)}")
    for alert in alert_manager.get_active_alerts():
        print(f"  - [{alert.level.value.upper()}] {alert.rule_name}: {alert.message}")
    
    print("\n" + "=" * 80)
    print("✅ Phase 50 监控系统测试完成！")
    print("=" * 80)
