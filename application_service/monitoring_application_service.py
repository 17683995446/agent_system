"""
应用服务层 - 监控应用服务
提供完整的监控、告警和数据分析功能
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time

from infrastructure.monitoring.monitoring_system import MonitoringSystem
from infrastructure.logging.logging_system import get_logger
from infrastructure.cache.cache_manager import CacheManager


class AlertSeverity(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    cooldown_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警事件"""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsQuery:
    """指标查询"""
    metric_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregator: str = "avg"
    tags: Optional[Dict[str, str]] = None


@dataclass
class MetricsResult:
    """指标查询结果"""
    values: List[Dict[str, Any]]
    summary: Dict[str, Any]
    statistics: Dict[str, float]


@dataclass
class DashboardSnapshot:
    """仪表板快照"""
    timestamp: str
    metrics: Dict[str, Any]
    health_status: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class MonitoringApplicationService:
    """监控应用服务"""
    
    def __init__(
        self,
        monitoring_system: Optional[MonitoringSystem] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        self.logger = get_logger("MonitoringApplicationService")
        self.monitoring_system = monitoring_system or MonitoringSystem()
        self.cache_manager = cache_manager or CacheManager(
            cache_type="ttl",
            maxsize=1000,
            ttl=300
        )
        
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.last_alert_check: Dict[str, float] = {}
        
        self._register_default_rules()
        self.logger.info("MonitoringApplicationService initialized")
    
    def _register_default_rules(self):
        """注册默认告警规则"""
        
        def high_memory_alert(context: Dict[str, Any]) -> bool:
            """高内存使用率告警"""
            metrics = context.get("metrics", {})
            memory_usage = metrics.get("memory_usage", 0)
            return memory_usage > 80
        
        def slow_response_alert(context: Dict[str, Any]) -> bool:
            """响应慢告警"""
            metrics = context.get("metrics", {})
            avg_response_time = metrics.get("avg_response_time", 0)
            return avg_response_time > 2.0
        
        self.register_alert_rule(AlertRule(
            name="high_memory_usage",
            description="内存使用率超过80%",
            condition=high_memory_alert,
            severity=AlertSeverity.WARNING,
            cooldown_seconds=600
        ))
        
        self.register_alert_rule(AlertRule(
            name="slow_response_time",
            description="平均响应时间超过2秒",
            condition=slow_response_alert,
            severity=AlertSeverity.ERROR,
            cooldown_seconds=300
        ))
    
    # ==================== 健康监控 ====================
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        return await self.monitoring_system.run_health_checks()
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        cache_key = "system_metrics"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        health = await self.get_health_status()
        metrics = self.monitoring_system.get_metrics()
        
        result = {
            "health": health,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.cache_manager.set(cache_key, result)
        return result
    
    async def get_dashboard_snapshot(self) -> DashboardSnapshot:
        """获取仪表板快照"""
        health = await self.get_health_status()
        metrics = await self.get_system_metrics()
        
        active_alerts = [
            alert for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]
        
        return DashboardSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
            health_status=health,
            alerts=[
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "message": alert.message
                }
                for alert in active_alerts
            ]
        )
    
    # ==================== 告警系统 ====================
    
    def register_alert_rule(self, rule: AlertRule):
        """注册告警规则"""
        self.alert_rules[rule.name] = rule
        self.logger.info(f"Registered alert rule: {rule.name}")
    
    async def check_and_trigger_alerts(self):
        """检查并触发告警"""
        context = await self.get_system_metrics()
        
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            last_check = self.last_alert_check.get(rule_name, 0)
            if (time.time() - last_check) < rule.cooldown_seconds:
                continue
            
            try:
                if rule.condition(context):
                    await self._trigger_alert(rule, context)
                    self.last_alert_check[rule_name] = time.time()
            except Exception as e:
                self.logger.error(f"Error checking alert rule {rule_name}: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, context: Dict[str, Any]):
        """触发告警"""
        import uuid
        
        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=rule.description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"context": context}
        )
        
        self.alerts[alert_id] = alert
        self.alert_history.append({
            "alert_id": alert_id,
            "rule_name": rule.name,
            "severity": rule.severity.value,
            "timestamp": alert.timestamp,
            "status": "triggered"
        })
        
        self.logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
        return alert
    
    def acknowledge_alert(self, alert_id: str, acknowledger: str = "system") -> Optional[Alert]:
        """确认告警"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledger
            alert.acknowledged_at = datetime.now(timezone.utc).isoformat()
            self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledger}")
            return alert
        return None
    
    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """解决告警"""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc).isoformat()
            self.logger.info(f"Alert resolved: {alert_id}")
            return alert
        return None
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[Alert]:
        """获取告警列表"""
        results = list(self.alerts.values())
        
        if status:
            results = [a for a in results if a.status == status]
        
        if severity:
            results = [a for a in results if a.severity == severity]
        
        return results[-limit:]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return self.alert_history[-limit:]
    
    # ==================== 指标系统 ====================
    
    def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标"""
        if metric_name not in self.metrics_history:
            self.metrics_history[metric_name] = []
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": value,
            "tags": tags or {}
        }
        
        self.metrics_history[metric_name].append(entry)
        
        if len(self.metrics_history[metric_name]) > 10000:
            self.metrics_history[metric_name] = self.metrics_history[metric_name][-10000:]
    
    def query_metrics(self, query: MetricsQuery) -> MetricsResult:
        """查询指标"""
        history = self.metrics_history.get(query.metric_name, [])
        
        filtered = []
        for entry in history:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            
            if query.start_time and entry_time < query.start_time:
                continue
            if query.end_time and entry_time > query.end_time:
                continue
            
            if query.tags:
                tag_match = all(
                    entry.get("tags", {}).get(k) == v
                    for k, v in query.tags.items()
                )
                if not tag_match:
                    continue
            
            filtered.append(entry)
        
        values = [e["value"] for e in filtered]
        
        if not values:
            return MetricsResult(values=[], summary={}, statistics={})
        
        statistics = {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
        
        if query.aggregator == "avg":
            summary = {"value": statistics["avg"]}
        elif query.aggregator == "sum":
            summary = {"value": sum(values)}
        elif query.aggregator == "max":
            summary = {"value": statistics["max"]}
        elif query.aggregator == "min":
            summary = {"value": statistics["min"]}
        else:
            summary = {"value": statistics["avg"]}
        
        return MetricsResult(
            values=filtered,
            summary=summary,
            statistics=statistics
        )
    
    # ==================== 统计与分析 ====================
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取统计信息"""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=hours)
        
        alert_count = sum(
            1 for alert in self.alerts.values()
            if datetime.fromisoformat(alert.timestamp) >= start_time
        )
        
        active_alerts = sum(
            1 for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        )
        
        metrics_stats = {}
        for metric_name in self.metrics_history.keys():
            stats = self.query_metrics(MetricsQuery(
                metric_name=metric_name,
                start_time=start_time
            )).statistics
            if stats:
                metrics_stats[metric_name] = stats
        
        return {
            "period_hours": hours,
            "total_alerts": alert_count,
            "active_alerts": active_alerts,
            "total_rules": len(self.alert_rules),
            "metrics": metrics_stats,
            "timestamp": now.isoformat()
        }
    
    async def export_dashboard_report(self) -> Dict[str, Any]:
        """导出仪表板报告"""
        dashboard = await self.get_dashboard_snapshot()
        statistics = self.get_statistics()
        alerts = self.get_alerts(limit=20)
        
        return {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "dashboard": {
                "health_status": dashboard.health_status,
                "metrics": dashboard.metrics
            },
            "alerts": [
                {
                    "id": a.id,
                    "rule": a.rule_name,
                    "severity": a.severity.value,
                    "status": a.status.value,
                    "timestamp": a.timestamp
                }
                for a in alerts
            ],
            "statistics": statistics
        }
