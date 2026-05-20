"""
分布式跟踪与可观测性系统
Phase 8.6: 分布式跟踪与可观测性
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timezone, timedelta
import uuid
import time
import asyncio
from collections import defaultdict


class SpanStatus(Enum):
    """Span状态"""
    UNSET = auto()
    OK = auto()
    ERROR = auto()


class SpanKind(Enum):
    """Span类型"""
    INTERNAL = auto()
    SERVER = auto()
    CLIENT = auto()
    PRODUCER = auto()
    CONSUMER = auto()


@dataclass
class Span:
    """Span数据类"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    status: SpanStatus = SpanStatus.UNSET
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ns: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    service_name: str = "unknown"
    
    def __post_init__(self):
        self._start_ns = time.time_ns()
    
    def end(self):
        """结束Span"""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ns = time.time_ns() - self._start_ns
        if self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """添加事件"""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {}
        })
    
    def add_attribute(self, key: str, value: Any):
        """添加属性"""
        self.attributes[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.name,
            "status": self.status.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ns": self.duration_ns,
            "duration_ms": self.duration_ns / 1_000_000 if self.duration_ns else 0,
            "attributes": self.attributes,
            "events": self.events,
            "service_name": self.service_name
        }


@dataclass
class Trace:
    """Trace数据类"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    root_span: Optional[Span] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    
    def add_span(self, span: Span):
        """添加Span"""
        self.spans.append(span)
        if not self.root_span or not span.parent_span_id:
            self.root_span = span
        if not self.start_time or span.start_time < self.start_time:
            self.start_time = span.start_time
        if span.end_time and (not self.end_time or span.end_time > self.end_time):
            self.end_time = span.end_time
        if span.status == SpanStatus.ERROR:
            self.status = SpanStatus.ERROR
        elif self.status == SpanStatus.UNSET and span.status == SpanStatus.OK:
            self.status = SpanStatus.OK
    
    def get_total_duration(self) -> float:
        """获取总耗时"""
        if not self.start_time or not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_count": len(self.spans),
            "root_span": self.root_span.name if self.root_span else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.get_total_duration(),
            "status": self.status.name,
            "spans": [s.to_dict() for s in self.spans]
        }


class Tracer:
    """分布式跟踪器"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._active_spans: Dict[str, Span] = {}
        self._traces: Dict[str, Trace] = {}
        self._exporters: List[Callable[[Trace], Any]] = []
        self._sampling_rate: float = 1.0
        self._span_counter: int = 0
    
    def add_exporter(self, exporter: Callable[[Trace], Any]):
        """添加导出器"""
        self._exporters.append(exporter)
    
    def set_sampling_rate(self, rate: float):
        """设置采样率"""
        self._sampling_rate = max(0, min(1, rate))
    
    def start_span(self, name: str, parent_trace_id: Optional[str] = None,
                  parent_span_id: Optional[str] = None,
                  kind: SpanKind = SpanKind.INTERNAL,
                  attributes: Optional[Dict[str, Any]] = None) -> Span:
        """启动Span"""
        import random
        
        if self._sampling_rate < 1 and random.random() > self._sampling_rate:
            span_id = str(uuid.uuid4())[:16]
            trace_id = parent_trace_id or str(uuid.uuid4())
            return Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                kind=kind
            )
        
        span_id = str(uuid.uuid4())[:16]
        trace_id = parent_trace_id or str(uuid.uuid4())
        
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            service_name=self.service_name
        )
        
        if attributes:
            span.attributes.update(attributes)
        
        self._active_spans[span_id] = span
        self._span_counter += 1
        
        if trace_id not in self._traces:
            self._traces[trace_id] = Trace(trace_id=trace_id)
        
        self._traces[trace_id].add_span(span)
        
        return span
    
    def end_span(self, span: Span) -> bool:
        """结束Span"""
        span.end()
        
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        
        if not span.parent_span_id:
            if span.trace_id in self._traces:
                trace = self._traces[span.trace_id]
                asyncio.create_task(self._export_trace(trace))
        
        return True
    
    async def _export_trace(self, trace: Trace):
        """导出Trace"""
        for exporter in self._exporters:
            try:
                if asyncio.iscoroutinefunction(exporter):
                    await exporter(trace)
                else:
                    exporter(trace)
            except Exception as e:
                print(f"Trace export error: {e}")
    
    def get_active_trace(self, trace_id: str) -> Optional[Trace]:
        """获取活跃Trace"""
        return self._traces.get(trace_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        completed_spans = [s for s in self._traces.values() for s in s.spans if s.end_time]
        total_duration = sum(s.duration_ns for s in completed_spans)
        
        return {
            "total_spans": self._span_counter,
            "active_spans": len(self._active_spans),
            "completed_traces": len([t for t in self._traces.values() if t.end_time]),
            "total_traces": len(self._traces),
            "avg_span_duration_ns": total_duration / len(completed_spans) if completed_spans else 0,
            "sampling_rate": self._sampling_rate
        }


@dataclass
class Metric:
    """指标数据类"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Dict[str, str] = field(default_factory=dict)
    type: str = "gauge"
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "type": self.type,
            "description": self.description
        }


class MetricsRegistry:
    """指标注册器"""
    
    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._summaries: Dict[str, List[float]] = defaultdict(list)
        self._max_history: int = 1000
    
    def counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """计数器"""
        key = self._make_key(name, labels)
        self._counters[key] += value
        self._record_metric(name, self._counters[key], "counter", labels)
    
    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """仪表盘"""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._record_metric(name, value, "gauge", labels)
    
    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """直方图"""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        
        if len(self._histograms[key]) > self._max_history:
            self._histograms[key] = self._histograms[key][-self._max_history:]
        
        self._record_metric(name, value, "histogram", labels)
    
    def summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """摘要"""
        key = self._make_key(name, labels)
        self._summaries[key].append(value)
        
        if len(self._summaries[key]) > self._max_history:
            self._summaries[key] = self._summaries[key][-self._max_history:]
        
        self._record_metric(name, value, "summary", labels)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        result = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": self._get_histogram_stats(),
            "summaries": self._get_summary_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return result
    
    def get_metric_history(self, name: str) -> List[Metric]:
        """获取指标历史"""
        return self._metrics.get(name, [])
    
    def _record_metric(self, name: str, value: float, metric_type: str,
                      labels: Optional[Dict[str, str]] = None):
        """记录指标"""
        metric = Metric(
            name=name,
            value=value,
            type=metric_type,
            labels=labels or {}
        )
        
        if name not in self._metrics:
            self._metrics[name] = []
        
        self._metrics[name].append(metric)
        
        if len(self._metrics[name]) > self._max_history:
            self._metrics[name] = self._metrics[name][-self._max_history:]
    
    def _get_histogram_stats(self) -> Dict[str, Any]:
        """获取直方图统计"""
        import statistics
        
        stats = {}
        for key, values in self._histograms.items():
            if values:
                stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                }
        return stats
    
    def _get_summary_stats(self) -> Dict[str, Any]:
        """获取摘要统计"""
        import statistics
        
        stats = {}
        for key, values in self._summaries.items():
            if values:
                stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "sum": sum(values)
                }
        return stats
    
    def _percentile(self, values: List[float], p: int) -> float:
        """计算百分位数"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p / 100)
        if index >= len(sorted_values):
            index = len(sorted_values) - 1
        return sorted_values[index]
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """生成键"""
        if not labels:
            return name
        
        label_parts = [f"{k}={v}" for k, v in sorted(labels.items())]
        return f"{name}[{','.join(label_parts)}]"


class ObservabilitySystem:
    """可观测性系统"""
    
    def __init__(self, service_name: str):
        self.tracer = Tracer(service_name)
        self.metrics = MetricsRegistry()
        self._logs: List[Dict[str, Any]] = []
        self._max_logs: int = 10000
        self._alert_rules: List[Dict[str, Any]] = []
    
    def log(self, level: str, message: str, attributes: Optional[Dict[str, Any]] = None):
        """记录日志"""
        log_entry = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {}
        }
        
        self._logs.append(log_entry)
        
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        if level in ["error", "critical"]:
            asyncio.create_task(self._check_alerts(log_entry))
    
    def info(self, message: str, attributes: Optional[Dict[str, Any]] = None):
        self.log("info", message, attributes)
    
    def warning(self, message: str, attributes: Optional[Dict[str, Any]] = None):
        self.log("warning", message, attributes)
    
    def error(self, message: str, attributes: Optional[Dict[str, Any]] = None):
        self.log("error", message, attributes)
    
    def critical(self, message: str, attributes: Optional[Dict[str, Any]] = None):
        self.log("critical", message, attributes)
    
    def add_alert_rule(self, rule: Dict[str, Any]):
        """添加告警规则"""
        self._alert_rules.append(rule)
    
    async def _check_alerts(self, log_entry: Dict[str, Any]):
        """检查告警"""
        pass
    
    def get_snapshot(self) -> Dict[str, Any]:
        """获取系统快照"""
        return {
            "tracer_stats": self.tracer.get_stats(),
            "metrics": self.metrics.get_metrics(),
            "recent_logs": self._logs[-100:],
            "alert_rule_count": len(self._alert_rules),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# 全局可观测性系统
global_observability = ObservabilitySystem("agent-system")
