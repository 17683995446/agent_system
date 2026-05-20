"""
应用服务层 - 数据分析应用服务
提供数据分析、趋势预测和洞察功能
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import math

from infrastructure.logging.logging_system import get_logger
from infrastructure.cache.cache_manager import CacheManager


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"
    UNCERTAIN = "uncertain"


class InsightSeverity(str, Enum):
    """洞察严重程度"""
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_name: str
    direction: TrendDirection
    slope: float
    confidence: float
    forecast: List[Dict[str, Any]]
    historical_data: List[Dict[str, Any]]


@dataclass
class Insight:
    """数据洞察"""
    id: str
    type: str
    title: str
    description: str
    severity: InsightSeverity
    timestamp: str
    related_metrics: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportConfig:
    """报告配置"""
    title: str
    include_trends: bool = True
    include_insights: bool = True
    include_forecasts: bool = True
    include_statistics: bool = True
    time_range_hours: int = 24


@dataclass
class Report:
    """分析报告"""
    id: str
    title: str
    timestamp: str
    trends: List[TrendAnalysis]
    insights: List[Insight]
    statistics: Dict[str, Any]
    summary: str


class AnalyticsApplicationService:
    """数据分析应用服务"""
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None
    ):
        self.logger = get_logger("AnalyticsApplicationService")
        self.cache_manager = cache_manager or CacheManager(
            cache_type="ttl",
            maxsize=500,
            ttl=3600
        )
        
        self.insights: Dict[str, Insight] = {}
        self.data_sources: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        
        self._register_default_insight_generators()
        self.logger.info("AnalyticsApplicationService initialized")
    
    def _register_default_insight_generators(self):
        """注册默认的洞察生成器"""
        pass
    
    # ==================== 趋势分析 ====================
    
    def analyze_trend(
        self,
        data_points: List[Dict[str, Any]],
        metric_name: str = "metric",
        forecast_points: int = 5
    ) -> TrendAnalysis:
        """分析趋势并生成预测"""
        if not data_points or len(data_points) < 3:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNCERTAIN,
                slope=0,
                confidence=0,
                forecast=[],
                historical_data=data_points
            )
        
        values = [p.get("value", 0) for p in data_points if "value" in p]
        timestamps = [p.get("timestamp", "") for p in data_points if "timestamp" in p]
        
        if len(values) < 3:
            return TrendAnalysis(
                metric_name=metric_name,
                direction=TrendDirection.UNCERTAIN,
                slope=0,
                confidence=0,
                forecast=[],
                historical_data=data_points
            )
        
        # 简单线性回归计算斜率
        n = len(values)
        x = list(range(n))
        y = values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # 确定趋势方向
        if abs(slope) < 0.01:
            direction = TrendDirection.FLAT
        elif slope > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN
        
        # 计算置信度（基于数据波动）
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std_dev = math.sqrt(variance) if variance > 0 else 0
        normalized_std = std_dev / (mean + 1e-10)
        confidence = max(0, min(1, 1 - normalized_std))
        
        # 生成预测
        forecast = []
        last_value = values[-1]
        for i in range(1, forecast_points + 1):
            predicted = last_value + slope * i
            forecast.append({
                "index": i,
                "value": max(0, predicted),
                "timestamp": f"forecast_{i}"
            })
        
        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            confidence=confidence,
            forecast=forecast,
            historical_data=data_points
        )
    
    # ==================== 洞察生成 ====================
    
    def generate_insights(
        self,
        trend_analyses: List[TrendAnalysis],
        statistics: Dict[str, Any]
    ) -> List[Insight]:
        """生成数据洞察"""
        insights = []
        
        for trend in trend_analyses:
            if trend.confidence > 0.7:
                if trend.direction == TrendDirection.UP:
                    insights.append(self._create_insight(
                        type="upward_trend",
                        title=f"{trend.metric_name} 呈上升趋势",
                        description=f"{trend.metric_name} 正在持续上升，斜率为 {trend.slope:.3f}",
                        severity=InsightSeverity.NOTICE,
                        related_metrics=[trend.metric_name]
                    ))
                elif trend.direction == TrendDirection.DOWN:
                    insights.append(self._create_insight(
                        type="downward_trend",
                        title=f"{trend.metric_name} 呈下降趋势",
                        description=f"{trend.metric_name} 正在持续下降，斜率为 {trend.slope:.3f}",
                        severity=InsightSeverity.NOTICE,
                        related_metrics=[trend.metric_name]
                    ))
        
        # 统计异常检测
        for metric_name, stats in statistics.get("metrics", {}).items():
            if isinstance(stats, dict):
                avg = stats.get("avg", 0)
                max_val = stats.get("max", 0)
                
                if max_val > avg * 3:
                    insights.append(self._create_insight(
                        type="spike_detected",
                        title=f"{metric_name} 检测到异常峰值",
                        description=f"{metric_name} 出现异常峰值，最大值是平均值的 {max_val / (avg + 1):.1f} 倍",
                        severity=InsightSeverity.WARNING,
                        related_metrics=[metric_name]
                    ))
        
        return insights
    
    def _create_insight(
        self,
        type: str,
        title: str,
        description: str,
        severity: InsightSeverity,
        related_metrics: List[str]
    ) -> Insight:
        """创建洞察对象"""
        import uuid
        
        insight_id = str(uuid.uuid4())
        insight = Insight(
            id=insight_id,
            type=type,
            title=title,
            description=description,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            related_metrics=related_metrics
        )
        
        self.insights[insight_id] = insight
        return insight
    
    def get_insights(
        self,
        severity: Optional[InsightSeverity] = None,
        type: Optional[str] = None,
        limit: int = 50
    ) -> List[Insight]:
        """获取洞察列表"""
        results = list(self.insights.values())
        
        if severity:
            results = [i for i in results if i.severity == severity]
        
        if type:
            results = [i for i in results if i.type == type]
        
        return results[-limit:]
    
    # ==================== 统计分析 ====================
    
    def calculate_statistics(
        self,
        data_points: List[Dict[str, Any]],
        metric_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """计算统计数据"""
        if not data_points:
            return {}
        
        values = [p.get("value", 0) for p in data_points if "value" in p]
        
        if not values:
            return {}
        
        n = len(values)
        mean = sum(values) / n
        sorted_vals = sorted(values)
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        minimum = min(values)
        maximum = max(values)
        variance = sum((v - mean) ** 2 for v in values) / n
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        percentile_25 = sorted_vals[int(n * 0.25)]
        percentile_75 = sorted_vals[int(n * 0.75)]
        
        result = {
            "count": n,
            "mean": mean,
            "median": median,
            "min": minimum,
            "max": maximum,
            "std_dev": std_dev,
            "variance": variance,
            "percentile_25": percentile_25,
            "percentile_75": percentile_75,
            "range": maximum - minimum
        }
        
        if metric_name:
            self.analysis_results[metric_name] = result
        
        return result
    
    def aggregate_metrics(
        self,
        data_points: List[Dict[str, Any]],
        group_by: str = "hour"
    ) -> List[Dict[str, Any]]:
        """聚合指标数据"""
        import uuid
        
        grouped_data: Dict[str, List[float]] = {}
        
        for point in data_points:
            if "timestamp" not in point or "value" not in point:
                continue
            
            timestamp_str = point["timestamp"]
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = datetime.now(timezone.utc)
            
            if group_by == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = timestamp.strftime("%Y-%m-%d")
            elif group_by == "week":
                year = timestamp.year
                week = timestamp.isocalendar()[1]
                key = f"{year}-W{week}"
            else:
                key = timestamp.strftime("%Y-%m-%d")
            
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(point["value"])
        
        results = []
        for key, values in grouped_data.items():
            if values:
                results.append({
                    "key": key,
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                })
        
        return sorted(results, key=lambda x: x["key"])
    
    # ==================== 报告生成 ====================
    
    async def generate_report(
        self,
        config: ReportConfig,
        data_points: Optional[List[Dict[str, Any]]] = None,
        metric_name: str = "performance"
    ) -> Report:
        """生成分析报告"""
        import uuid
        
        cache_key = f"report_{config.title}_{config.time_range_hours}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        trends = []
        insights = []
        statistics = {}
        
        if data_points:
            statistics = self.calculate_statistics(data_points, metric_name)
            
            if config.include_trends:
                trend = self.analyze_trend(data_points, metric_name)
                trends.append(trend)
            
            if config.include_insights:
                insights = self.generate_insights(trends, {"metrics": {metric_name: statistics}})
        
        # 生成摘要
        summary_parts = []
        if trends:
            up_count = sum(1 for t in trends if t.direction == TrendDirection.UP)
            down_count = sum(1 for t in trends if t.direction == TrendDirection.DOWN)
            summary_parts.append(f"趋势分析: {up_count} 上升, {down_count} 下降")
        
        if insights:
            warning_count = sum(1 for i in insights if i.severity in [InsightSeverity.WARNING, InsightSeverity.ALERT, InsightSeverity.CRITICAL])
            summary_parts.append(f"发现 {len(insights)} 个洞察, 其中 {warning_count} 个警告")
        
        summary = " | ".join(summary_parts) if summary_parts else "报告生成完成"
        
        report = Report(
            id=report_id,
            title=config.title,
            timestamp=timestamp,
            trends=trends,
            insights=insights,
            statistics=statistics,
            summary=summary
        )
        
        self.cache_manager.set(cache_key, report)
        return report
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的报告"""
        # 返回基本信息，实际应该从存储中读取
        return [
            {
                "id": "sample_1",
                "title": "每日性能报告",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            }
        ]
    
    # ==================== 高级分析 ====================
    
    def detect_anomalies(
        self,
        data_points: List[Dict[str, Any]],
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """检测异常值"""
        if len(data_points) < 10:
            return []
        
        values = [p.get("value", 0) for p in data_points if "value" in p]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance) if variance > 0 else 1
        
        anomalies = []
        for point in data_points:
            value = point.get("value", 0)
            z_score = abs(value - mean) / std_dev if std_dev > 0 else 0
            
            if z_score > threshold:
                anomalies.append({
                    "point": point,
                    "z_score": z_score,
                    "mean": mean,
                    "std_dev": std_dev
                })
        
        return anomalies
    
    def calculate_correlation(
        self,
        series_a: List[Dict[str, Any]],
        series_b: List[Dict[str, Any]]
    ) -> float:
        """计算两个序列的相关性"""
        if len(series_a) < 3 or len(series_b) < 3:
            return 0
        
        values_a = [p.get("value", 0) for p in series_a if "value" in p]
        values_b = [p.get("value", 0) for p in series_b if "value" in p]
        
        if not values_a or not values_b:
            return 0
        
        # 简单的相关计算（对齐假设）
        min_len = min(len(values_a), len(values_b))
        a = values_a[:min_len]
        b = values_b[:min_len]
        
        mean_a = sum(a) / min_len
        mean_b = sum(b) / min_len
        
        numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
        denominator = math.sqrt(sum((x - mean_a) ** 2 for x in a) * sum((y - mean_b) ** 2 for y in b))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
