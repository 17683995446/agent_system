"""
FastAPI路由 - 监控和分析
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api_endpoints.monitoring_analytics_endpoints import MonitoringAnalyticsEndpoints

router = APIRouter()

@router.get("/health")
async def get_health() -> dict:
    """Get system health status"""
    endpoints = MonitoringAnalyticsEndpoints()
    return await endpoints.get_health_status()

@router.get("/metrics")
async def get_system_metrics() -> dict:
    """Get system metrics"""
    endpoints = MonitoringAnalyticsEndpoints()
    return await endpoints.get_system_metrics()

@router.get("/dashboard")
async def get_dashboard() -> dict:
    """Get dashboard snapshot"""
    endpoints = MonitoringAnalyticsEndpoints()
    dashboard = await endpoints.get_dashboard_snapshot()
    return dashboard.__dict__

@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200)
) -> dict:
    """List alerts"""
    from application_service.monitoring_application_service import AlertStatus, AlertSeverity
    
    endpoints = MonitoringAnalyticsEndpoints()
    
    alert_status = AlertStatus(status) if status else None
    alert_severity = AlertSeverity(severity) if severity else None
    
    alerts = await endpoints.list_alerts(
        status=alert_status,
        severity=alert_severity,
        limit=limit
    )
    
    return {"total": len(alerts), "alerts": [a.__dict__ for a in alerts]}

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledger: str = "api") -> dict:
    """Acknowledge alert"""
    endpoints = MonitoringAnalyticsEndpoints()
    alert = await endpoints.acknowledge_alert(alert_id, acknowledger)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert.__dict__

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> dict:
    """Resolve alert"""
    endpoints = MonitoringAnalyticsEndpoints()
    alert = await endpoints.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert.__dict__

@router.post("/metrics/record")
async def record_metric(
    metric_name: str = Query(..., description="Metric name"),
    value: float = Query(..., description="Metric value"),
    tags: Optional[str] = Query(None, description="Comma-separated tags")
) -> dict:
    """Record a metric"""
    endpoints = MonitoringAnalyticsEndpoints()
    
    tag_dict = {}
    if tags:
        for tag in tags.split(","):
            if "=" in tag:
                k, v = tag.split("=", 1)
                tag_dict[k] = v
    
    await endpoints.record_metric(metric_name, value, tag_dict)
    return {"recorded": True, "metric": metric_name, "value": value}

@router.get("/metrics/history")
async def get_metrics_history(
    metric_name: str = Query(..., description="Metric name"),
    hours: int = Query(24, ge=1, le=168)
) -> dict:
    """Get metric history"""
    endpoints = MonitoringAnalyticsEndpoints()
    history = await endpoints.get_metrics_history(metric_name, hours)
    return {"metric": metric_name, "data_points": history}

@router.post("/analytics/trends")
async def analyze_trends(request: dict) -> dict:
    """Analyze trends"""
    endpoints = MonitoringAnalyticsEndpoints()
    data_points = request.get("data_points", [])
    metric_name = request.get("metric_name", "metric")
    trend = await endpoints.analyze_trends(data_points, metric_name)
    return trend

@router.get("/statistics")
async def get_statistics(hours: int = Query(24, ge=1, le=168)) -> dict:
    """Get system statistics"""
    endpoints = MonitoringAnalyticsEndpoints()
    return await endpoints.get_statistics(hours=hours)

@router.post("/analytics/anomalies")
async def detect_anomalies(
    threshold: float = Query(3.0, ge=1.0, le=10.0, description="Detection threshold")
) -> dict:
    """Detect anomalies"""
    endpoints = MonitoringAnalyticsEndpoints()
    
    import random
    test_data = [
        {"timestamp": f"2026-05-16T{str(i).zfill(2)}:00:00Z", "value": 50 + i * 2 + random.uniform(-5, 5)}
        for i in range(10)
    ]
    
    anomalies = await endpoints.detect_anomalies(test_data, threshold)
    return {"anomalies": anomalies, "threshold": threshold}

@router.post("/reports/generate")
async def generate_report(request: dict) -> dict:
    """Generate analytics report"""
    endpoints = MonitoringAnalyticsEndpoints()
    
    title = request.get("title", "Analytics Report")
    include_trends = request.get("include_trends", True)
    include_insights = request.get("include_insights", True)
    include_statistics = request.get("include_statistics", True)
    
    report = await endpoints.generate_report(
        title=title,
        include_trends=include_trends,
        include_insights=include_insights,
        include_statistics=include_statistics
    )
    
    return report.__dict__

@router.get("/export/dashboard")
async def export_dashboard() -> dict:
    """Export dashboard report"""
    endpoints = MonitoringAnalyticsEndpoints()
    return await endpoints.export_dashboard_report()
