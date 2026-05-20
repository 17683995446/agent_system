"""
数据模型 - Metrics指标模型
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from infrastructure.database.async_database_config import Base


class MetricModel(Base):
    """
    Metric指标数据模型
    存储系统性能指标和监控数据
    """
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    
    tags = Column(JSON, default=dict, nullable=False)
    labels = Column(JSON, default=dict, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    is_alert = Column(Boolean, default=False, nullable=False)
    alert_threshold = Column(Float, nullable=True)
    
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_id = Column(String(100), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    extra_metadata = Column(JSON, default=dict, nullable=False)
    
    __table_args__ = (
        Index('idx_metrics_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_metrics_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_metrics_agent_timestamp', 'agent_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MetricModel(id={self.id}, name={self.metric_name}, value={self.metric_value})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "tags": self.tags,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_alert": self.is_alert,
            "alert_threshold": self.alert_threshold,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "metadata": self.metadata
        }
    
    def to_prometheus_format(self) -> str:
        """转换为Prometheus格式"""
        labels_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()])
        return f"{self.metric_name}{{{labels_str}}} {self.metric_value} {int(self.timestamp.timestamp())}"
    
    def check_threshold(self) -> bool:
        """检查是否超过阈值"""
        if self.alert_threshold is None:
            return False
        return abs(self.metric_value) > self.alert_threshold


class AlertModel(Base):
    """
    Alert告警数据模型
    存储系统告警和异常事件
    """
    __tablename__ = "alerts"

    id = Column(String(100), primary_key=True, index=True)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    severity = Column(String(20), nullable=False, default="warning", index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    
    source = Column(String(100), nullable=True)
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_channels = Column(JSON, default=list, nullable=False)
    
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    tags = Column(JSON, default=list, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    
    __table_args__ = (
        Index('idx_alerts_severity_status', 'severity', 'status'),
        Index('idx_alerts_user_triggered', 'user_id', 'triggered_at'),
        Index('idx_alerts_status_triggered', 'status', 'triggered_at'),
    )
    
    def __repr__(self):
        return f"<AlertModel(id={self.id}, severity={self.severity}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "source": self.source,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "notification_sent": self.notification_sent,
            "notification_channels": self.notification_channels,
            "user_id": self.user_id,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    def acknowledge(self, acknowledged_by: str):
        """确认告警"""
        self.status = "acknowledged"
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = acknowledged_by
    
    def resolve(self, resolved_by: str, notes: str = None):
        """解决告警"""
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by
        if notes:
            self.resolution_notes = notes
    
    def escalate(self):
        """升级告警"""
        severity_levels = ["info", "warning", "error", "critical"]
        current_index = severity_levels.index(self.severity) if self.severity in severity_levels else 1
        if current_index < len(severity_levels) - 1:
            self.severity = severity_levels[current_index + 1]
