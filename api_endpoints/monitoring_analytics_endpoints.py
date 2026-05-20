"""
API端点层 - 监控和分析API
提供系统监控和数据分析功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from application_service.monitoring_application_service import (
    MonitoringApplicationService, AlertSeverity, AlertStatus, AlertRule
)
from application_service.analytics_application_service import (
    AnalyticsApplicationService, ReportConfig
)
from infrastructure.logging.logging_system import get_logger


@dataclass
class AlertResponse:
    """告警响应对象"""
    alert_id: str
    rule_name: str
    severity: str
    status: str
    message: str
    timestamp: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None


@dataclass
class DashboardSnapshotResponse:
    """仪表板快照响应"""
    timestamp: str
    health_status: Dict[str, Any]
    metrics: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]


@dataclass
class AnalyticsReportResponse:
    """分析报告响应"""
    report_id: str
    title: str
    timestamp: str
    summary: str
    trends: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class MonitoringAnalyticsEndpoints:
    """监控和分析API端点"""

    def __init__(
        self,
        monitoring_service: Optional[MonitoringApplicationService] = None,
        analytics_service: Optional[AnalyticsApplicationService] = None
    ):
        self.logger = get_logger("MonitoringAnalyticsEndpoints")
        self.monitoring_service = monitoring_service or MonitoringApplicationService()
        self.analytics_service = analytics_service or AnalyticsApplicationService()
        self.logger.info("MonitoringAnalyticsEndpoints initialized")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        return await self.monitoring_service.get_health_status()

    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return await self.monitoring_service.get_system_metrics()

    async def get_dashboard_snapshot(self) -> DashboardSnapshotResponse:
        """获取仪表板快照"""
        snapshot = await self.monitoring_service.get_dashboard_snapshot()
        return DashboardSnapshotResponse(
            timestamp=snapshot.timestamp,
            health_status=snapshot.health_status,
            metrics=snapshot.metrics,
            active_alerts=snapshot.alerts
        )

    async def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[AlertResponse]:
        """列出告警"""
        alerts = self.monitoring_service.get_alerts(
            status=status,
            severity=severity,
            limit=limit
        )
        return [self._alert_to_response(a) for a in alerts]

    async def acknowledge_alert(self, alert_id: str, acknowledger: str = "system") -> Optional[AlertResponse]:
        """确认告警"""
        alert = self.monitoring_service.acknowledge_alert(alert_id, acknowledger)
        if alert:
            return self._alert_to_response(alert)
        return None

    async def resolve_alert(self, alert_id: str) -> Optional[AlertResponse]:
        """解决告警"""
        alert = self.monitoring_service.resolve_alert(alert_id)
        if alert:
            return self._alert_to_response(alert)
        return None

    async def register_alert_rule(
        self,
        name: str,
        description: str,
        condition: Any,
        severity: AlertSeverity = AlertSeverity.WARNING,
        enabled: bool = True
    ) -> None:
        """注册告警规则"""
        rule = AlertRule(
            name=name,
            description=description,
            condition=condition,
            severity=severity,
            enabled=enabled
        )
        self.monitoring_service.register_alert_rule(rule)
        self.logger.info(f"Registered alert rule: {name}")

    async def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标"""
        self.monitoring_service.record_metric(metric_name, value, tags)

    async def get_metrics_history(
        self,
        metric_name: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取指标历史"""
        from application_service.monitoring_application_service import MetricsQuery
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = MetricsQuery(
            metric_name=metric_name,
            start_time=start_time
        )
        result = self.monitoring_service.query_metrics(query)
        return result.values

    async def analyze_trends(
        self,
        data_points: List[Dict[str, Any]],
        metric_name: str = "metric"
    ) -> Dict[str, Any]:
        """分析趋势"""
        trend = self.analytics_service.analyze_trends(data_points, metric_name)
        return {
            "metric_name": trend.metric_name,
            "direction": trend.direction.value,
            "slope": trend.slope,
            "confidence": trend.confidence,
            "forecast": trend.forecast,
            "historical_data": trend.historical_data
        }

    async def generate_report(
        self,
        title: str,
        data_points: Optional[List[Dict[str, Any]]] = None,
        include_trends: bool = True,
        include_insights: bool = True,
        include_statistics: bool = True
    ) -> AnalyticsReportResponse:
        """生成分析报告"""
        config = ReportConfig(
            title=title,
            include_trends=include_trends,
            include_insights=include_insights,
            include_statistics=include_statistics
        )
        report = await self.analytics_service.generate_report(config, data_points)
        
        return AnalyticsReportResponse(
            report_id=report.id,
            title=report.title,
            timestamp=report.timestamp,
            summary=report.summary,
            trends=[
                {
                    "metric_name": t.metric_name,
                    "direction": t.direction.value,
                    "slope": t.slope,
                    "confidence": t.confidence
                }
                for t in report.trends
            ],
            insights=[
                {
                    "id": i.id,
                    "type": i.type,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity.value,
                    "timestamp": i.timestamp
                }
                for i in report.insights
            ],
            statistics=report.statistics
        )

    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取统计信息"""
        monitoring_stats = self.monitoring_service.get_statistics(hours)
        return {
            "monitoring": monitoring_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def detect_anomalies(
        self,
        data_points: List[Dict[str, Any]],
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """检测异常值"""
        anomalies = self.analytics_service.detect_anomalies(data_points, threshold)
        return anomalies

    async def export_dashboard_report(self) -> Dict[str, Any]:
        """导出仪表板报告"""
        return await self.monitoring_service.export_dashboard_report()

    def _alert_to_response(self, alert: Any) -> AlertResponse:
        """转换告警为响应对象"""
        return AlertResponse(
            alert_id=alert.id,
            rule_name=alert.rule_name,
            severity=alert.severity.value,
            status=alert.status.value,
            message=alert.message,
            timestamp=alert.timestamp,
            acknowledged_by=alert.acknowledged_by,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at
        )
