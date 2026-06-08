"""
监控模块抽象接口定义

提供指标收集、告警管理和健康检查的标准接口。
所有监控相关实现必须遵循此接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from enum import Enum


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricsCollectorInterface(ABC):
    """指标收集器接口

    提供Prometheus风格的指标收集功能。
    支持Counter、Gauge、Histogram三种指标类型。
    """

    @abstractmethod
    def increment_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        value: float = 1.0
    ) -> None:
        """计数器递增

        Args:
            name: 指标名称
            labels: 标签字典
            value: 递增值（默认1.0）
        """
        pass

    @abstractmethod
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """设置Gauge值

        Args:
            name: 指标名称
            value: 当前值
            labels: 标签字典
        """
        pass

    @abstractmethod
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """观察直方图值

        Args:
            name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        pass

    @abstractmethod
    def export_metrics(self) -> str:
        """导出Prometheus格式指标

        Returns:
            Prometheus文本格式字符串
        """
        pass

    @abstractmethod
    def get_current_values(self) -> Dict[str, float]:
        """获取当前指标值

        Returns:
            指标名称到当前值的映射
        """
        pass


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertRule:
    """告警规则数据类"""

    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: Callable[[float], bool],
        level: AlertLevel,
        message: str,
        duration_seconds: float = 30.0
    ):
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.level = level
        self.message = message
        self.duration_seconds = duration_seconds
        self.active = True


class AlertManagerInterface(ABC):
    """告警管理器接口

    提供告警规则的注册、检查和通知功能。
    """

    @abstractmethod
    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则

        Args:
            rule: 告警规则对象
        """
        pass

    @abstractmethod
    def remove_rule(self, name: str) -> bool:
        """移除告警规则

        Args:
            name: 规则名称

        Returns:
            移除是否成功
        """
        pass

    @abstractmethod
    def check_rules(self) -> List[Dict[str, Any]]:
        """检查所有告警规则

        Returns:
            触发的告警列表
        """
        pass

    @abstractmethod
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警

        Returns:
            活跃告警列表
        """
        pass

    @abstractmethod
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史

        Args:
            limit: 返回数量限制

        Returns:
            告警历史列表
        """
        pass

    @abstractmethod
    def start_monitoring(self, check_interval: float = 5.0) -> None:
        """启动监控循环

        Args:
            check_interval: 检查间隔（秒）
        """
        pass

    @abstractmethod
    def stop_monitoring(self) -> None:
        """停止监控循环"""
        pass


class HealthCheckerInterface(ABC):
    """健康检查器接口

    提供系统健康状态的检查功能。
    """

    @abstractmethod
    def add_check(
        self,
        name: str,
        check_func: Callable[[], Dict[str, Any]],
        critical: bool = False
    ) -> None:
        """添加健康检查项

        Args:
            name: 检查项名称
            check_func: 检查函数，返回检查结果字典
            critical: 是否为关键检查项
        """
        pass

    @abstractmethod
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查

        Returns:
            健康检查结果字典，包含：
            - overall_status: 整体状态（healthy/degraded/unhealthy）
            - health_score: 健康评分（0-100）
            - checks: 各检查项结果
            - timestamp: 检查时间
        """
        pass

    @abstractmethod
    def start(self, interval: int = 5) -> None:
        """启动定期健康检查

        Args:
            interval: 检查间隔（秒）
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止健康检查"""
        pass
