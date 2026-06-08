"""
监控应用服务

提供系统监控的业务逻辑，包括指标收集、告警管理、健康检查等。
"""

import logging
from typing import Dict, Any, List, Optional

from interfaces.monitoring import (
    MetricsCollectorInterface,
    AlertManagerInterface,
    HealthCheckerInterface,
    AlertRule,
    AlertLevel
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """监控应用服务

    提供系统监控的业务逻辑，包括：
    - 指标收集和查询
    - 告警规则管理
    - 健康状态检查
    - 监控数据导出

    Attributes:
        metrics: 指标收集器接口
        alert_manager: 告警管理器接口
        health_checker: 健康检查器接口
    """

    def __init__(
        self,
        metrics: MetricsCollectorInterface,
        alert_manager: AlertManagerInterface,
        health_checker: HealthCheckerInterface
    ):
        self.metrics = metrics
        self.alert_manager = alert_manager
        self.health_checker = health_checker
        logger.info("[MonitoringService] 初始化完成")

    def record_request(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status_code: int
    ) -> None:
        """记录HTTP请求

        Args:
            method: HTTP方法
            endpoint: 请求端点
            duration: 请求耗时（秒）
            status_code: HTTP状态码
        """
        labels = {"method": method, "endpoint": endpoint}

        # 记录请求数
        self.metrics.increment_counter("http_requests_total", labels)

        # 记录延迟
        self.metrics.observe_histogram("http_request_duration_seconds", duration, labels)

        # 记录错误
        if status_code >= 400:
            error_labels = {**labels, "status": str(status_code)}
            self.metrics.increment_counter("http_errors_total", error_labels)

    def record_cache_operation(
        self,
        operation: str,
        hit: bool
    ) -> None:
        """记录缓存操作

        Args:
            operation: 操作类型（get/set/delete）
            hit: 是否命中
        """
        if hit:
            self.metrics.increment_counter("cache_hits_total", {"operation": operation})
        else:
            self.metrics.increment_counter("cache_misses_total", {"operation": operation})

    def record_database_operation(
        self,
        operation: str,
        duration: float
    ) -> None:
        """记录数据库操作

        Args:
            operation: 操作类型
            duration: 耗时（秒）
        """
        labels = {"operation": operation}
        self.metrics.increment_counter("db_operations_total", labels)
        self.metrics.observe_histogram("db_operation_duration_seconds", duration, labels)

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标

        Returns:
            当前系统指标值
        """
        return self.metrics.get_current_values()

    def export_prometheus_metrics(self) -> str:
        """导出Prometheus格式指标

        Returns:
            Prometheus文本格式
        """
        return self.metrics.export_metrics()

    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        level: str,
        message: str
    ) -> None:
        """添加告警规则

        Args:
            name: 规则名称
            metric_name: 监控指标名
            condition: 条件（gt/lt/eq）
            threshold: 阈值
            level: 级别（info/warning/error/critical）
            message: 告警消息
        """
        # 解析条件
        def condition_func(value: float) -> bool:
            if condition == "gt":
                return value > threshold
            elif condition == "lt":
                return value < threshold
            elif condition == "eq":
                return value == threshold
            elif condition == "gte":
                return value >= threshold
            elif condition == "lte":
                return value <= threshold
            return False

        # 解析级别
        level_enum = AlertLevel.WARNING
        if level == "info":
            level_enum = AlertLevel.INFO
        elif level == "error":
            level_enum = AlertLevel.ERROR
        elif level == "critical":
            level_enum = AlertLevel.CRITICAL

        rule = AlertRule(
            name=name,
            metric_name=metric_name,
            condition=condition_func,
            level=level_enum,
            message=message
        )

        self.alert_manager.add_rule(rule)
        logger.info(f"[MonitoringService] 添加告警规则: {name}")

    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警

        Returns:
            触发的告警列表
        """
        return self.alert_manager.check_rules()

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警

        Returns:
            活跃告警列表
        """
        return self.alert_manager.get_active_alerts()

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史

        Args:
            limit: 返回数量限制

        Returns:
            告警历史列表
        """
        return self.alert_manager.get_alert_history(limit)

    def run_health_checks(self) -> Dict[str, Any]:
        """运行健康检查

        Returns:
            健康检查结果
        """
        return self.health_checker.run_all_checks()

    def start_monitoring(self, check_interval: float = 5.0) -> None:
        """启动监控

        Args:
            check_interval: 检查间隔（秒）
        """
        self.alert_manager.start_monitoring(check_interval)
        self.health_checker.start(check_interval)
        logger.info("[MonitoringService] 监控已启动")

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.alert_manager.stop_monitoring()
        self.health_checker.stop()
        logger.info("[MonitoringService] 监控已停止")
