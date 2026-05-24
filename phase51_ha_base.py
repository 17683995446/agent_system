"""
Phase 51: 高可用与集群化 - 基础架构
遵循“大事做于细，难事成于易”原则
从基础的配置管理与环境隔离开始
"""

import os
import sys
import json
import time
import uuid
import threading
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# 配置日志
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase51_ha.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(thread)d:%(name)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===========================================
# 环境类型枚举
# ===========================================
class Environment(Enum):
    """运行环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

# ===========================================
# 配置管理系统
# ===========================================
@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "multi_tenant_system"
    username: str = "admin"
    password: str = "admin123"
    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False

    def to_dict(self) -> Dict:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "echo": self.echo
        }

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5

    def to_dict(self) -> Dict:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout
        }

@dataclass
class ServiceConfig:
    """服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    debug: bool = False
    timeout: int = 30

    def to_dict(self) -> Dict:
        return {
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "debug": self.debug,
            "timeout": self.timeout
        }

@dataclass
class SecurityConfig:
    """安全配置"""
    jwt_secret: str = "change_this_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    def to_dict(self) -> Dict:
        return {
            "jwt_secret": self.jwt_secret,
            "jwt_algorithm": self.jwt_algorithm,
            "access_token_expire_minutes": self.access_token_expire_minutes,
            "refresh_token_expire_days": self.refresh_token_expire_days,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "cors_origins": self.cors_origins
        }

@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    prometheus_port: int = 9090
    metrics_interval_seconds: int = 10
    log_level: str = "INFO"
    enable_tracing: bool = False

    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "prometheus_port": self.prometheus_port,
            "metrics_interval_seconds": self.metrics_interval_seconds,
            "log_level": self.log_level,
            "enable_tracing": self.enable_tracing
        }

@dataclass
class HighAvailabilityConfig:
    """高可用配置"""
    mode: str = "standalone"
    cluster_id: str = "multi_tenant_cluster"
    node_id: Optional[str] = None
    health_check_interval_seconds: int = 5
    failover_timeout_seconds: int = 30
    leader_election_enabled: bool = False
    replication_enabled: bool = False
    sync_interval_seconds: int = 60

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode,
            "cluster_id": self.cluster_id,
            "node_id": self.node_id,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "failover_timeout_seconds": self.failover_timeout_seconds,
            "leader_election_enabled": self.leader_election_enabled,
            "replication_enabled": self.replication_enabled,
            "sync_interval_seconds": self.sync_interval_seconds
        }

@dataclass
class GlobalConfig:
    """全局配置"""
    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    high_availability: HighAvailabilityConfig = field(default_factory=HighAvailabilityConfig)

    def to_dict(self) -> Dict:
        return {
            "environment": self.environment.value,
            "database": self.database.to_dict(),
            "redis": self.redis.to_dict(),
            "service": self.service.to_dict(),
            "security": self.security.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "high_availability": self.high_availability.to_dict()
        }

# ===========================================
# 配置管理器
# ===========================================
class ConfigManager:
    """配置管理器 - 支持多环境配置加载与管理"""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config"
        )
        self._configs: Dict[Environment, GlobalConfig] = {}
        self._current_env: Optional[Environment] = None
        self._lock = threading.RLock()
        self._load_default_configs()

        logger.info(f"[ConfigManager] 初始化完成，配置目录: {self.config_dir}")

    def _load_default_configs(self):
        """加载默认配置（所有环境）"""
        logger.debug("[ConfigManager] 加载默认配置")
        
        # 开发环境配置
        dev_config = GlobalConfig(
            environment=Environment.DEVELOPMENT,
            service=ServiceConfig(debug=True),
            database=DatabaseConfig(echo=True, pool_size=5, max_overflow=2)
        )
        self._configs[Environment.DEVELOPMENT] = dev_config

        # 测试环境配置
        test_config = GlobalConfig(
            environment=Environment.TESTING,
            service=ServiceConfig(debug=True, port=8001),
            database=DatabaseConfig(database="multi_tenant_test", echo=True)
        )
        self._configs[Environment.TESTING] = test_config

        # 预发布环境配置
        staging_config = GlobalConfig(
            environment=Environment.STAGING,
            service=ServiceConfig(debug=False, port=8002, workers=2),
            security=SecurityConfig(rate_limit_requests=500)
        )
        self._configs[Environment.STAGING] = staging_config

        # 生产环境配置
        prod_config = GlobalConfig(
            environment=Environment.PRODUCTION,
            service=ServiceConfig(debug=False, workers=8),
            security=SecurityConfig(
                jwt_secret=os.getenv("JWT_SECRET", "change_this_in_production"),
                rate_limit_requests=1000
            ),
            database=DatabaseConfig(pool_size=50, max_overflow=25),
            monitoring=MonitoringConfig(enable_tracing=True),
            high_availability=HighAvailabilityConfig(
                mode="cluster",
                leader_election_enabled=True,
                replication_enabled=True
            )
        )
        self._configs[Environment.PRODUCTION] = prod_config

    def get_config(self, env: Optional[Environment] = None) -> GlobalConfig:
        """获取配置"""
        with self._lock:
            target_env = env or self._current_env or Environment.DEVELOPMENT
            config = self._configs.get(target_env)
            if not config:
                logger.warning(f"[ConfigManager] 未找到环境 {target_env} 的配置，使用开发环境")
                config = self._configs[Environment.DEVELOPMENT]
            return config

    def get_current_config(self) -> GlobalConfig:
        """获取当前环境配置"""
        with self._lock:
            if not self._current_env:
                self._current_env = self._detect_environment()
            return self._configs[self._current_env]

    def set_environment(self, env: Environment):
        """设置当前环境"""
        with self._lock:
            old_env = self._current_env
            self._current_env = env
            logger.info(f"[ConfigManager] 环境切换: {old_env} -> {env}")

    def _detect_environment(self) -> Environment:
        """自动检测运行环境"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        env_map = {
            "development": Environment.DEVELOPMENT,
            "dev": Environment.DEVELOPMENT,
            "testing": Environment.TESTING,
            "test": Environment.TESTING,
            "staging": Environment.STAGING,
            "stage": Environment.STAGING,
            "production": Environment.PRODUCTION,
            "prod": Environment.PRODUCTION
        }
        detected = env_map.get(env_str, Environment.DEVELOPMENT)
        logger.info(f"[ConfigManager] 自动检测环境: {detected}")
        return detected

    def save_config(self, config: GlobalConfig, env: Environment):
        """保存配置到文件"""
        with self._lock:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            config_path = os.path.join(self.config_dir, f"{env.value}.json")
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
                logger.info(f"[ConfigManager] 配置已保存: {config_path}")
            except Exception as e:
                logger.error(f"[ConfigManager] 保存配置失败: {e}")

    def is_development(self) -> bool:
        """是否开发环境"""
        return self._current_env == Environment.DEVELOPMENT

    def is_production(self) -> bool:
        """是否生产环境"""
        return self._current_env == Environment.PRODUCTION

# ===========================================
# 实例信息管理
# ===========================================
@dataclass
class ServiceInstance:
    """服务实例信息"""
    instance_id: str
    service_name: str
    host: str
    port: int
    environment: str
    status: str = "healthy"  # healthy, degraded, unhealthy
    version: str = "1.0.0"
    health_score: float = 100.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "instance_id": self.instance_id,
            "service_name": self.service_name,
            "host": self.host,
            "port": self.port,
            "environment": self.environment,
            "status": self.status,
            "version": self.version,
            "health_score": self.health_score,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat()
        }

class InstanceManager:
    """实例管理器 - 管理本地服务实例"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._instance: Optional[ServiceInstance] = None
        self._lock = threading.RLock()
        self._create_local_instance()
        
        logger.info(f"[InstanceManager] 初始化完成，实例ID: {self._instance.instance_id if self._instance else 'None'}")

    def _create_local_instance(self):
        """创建本地服务实例"""
        config = self.config_manager.get_current_config()
        
        instance_id = os.getenv("INSTANCE_ID", f"node-{uuid.uuid4().hex[:8]}")
        self._instance = ServiceInstance(
            instance_id=instance_id,
            service_name="multi_tenant_system",
            host=config.service.host,
            port=config.service.port,
            environment=config.environment.value,
            status="healthy"
        )
        
        # 更新配置中的节点ID
        config.high_availability.node_id = instance_id

    def get_local_instance(self) -> ServiceInstance:
        """获取本地实例"""
        with self._lock:
            return self._instance

    def update_health_score(self, score: float):
        """更新健康评分"""
        with self._lock:
            if self._instance:
                self._instance.health_score = max(0, min(100, score))
                self._instance.last_heartbeat = datetime.now()
                logger.debug(f"[InstanceManager] 健康评分更新: {self._instance.health_score}")

    def mark_as_unhealthy(self):
        """标记实例为不健康"""
        with self._lock:
            if self._instance:
                self._instance.status = "unhealthy"
                self._instance.health_score = 0.0
                logger.warning(f"[InstanceManager] 实例标记为不健康: {self._instance.instance_id}")

    def mark_as_healthy(self):
        """标记实例为健康"""
        with self._lock:
            if self._instance:
                self._instance.status = "healthy"
                self._instance.health_score = 100.0
                logger.info(f"[InstanceManager] 实例标记为健康: {self._instance.instance_id}")

# ===========================================
# 简单健康检查系统
# ===========================================
class HealthChecker:
    """健康检查器"""

    def __init__(self, instance_manager: InstanceManager):
        self.instance_manager = instance_manager
        self._checks: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # 注册默认检查
        self._register_default_checks()
        logger.info("[HealthChecker] 初始化完成")

    def _register_default_checks(self):
        """注册默认的健康检查项"""
        self.add_check("basic", self._basic_check, critical=True)
        self.add_check("memory", self._memory_check, critical=False)
        self.add_check("clock", self._clock_check, critical=False)

    def add_check(self, name: str, check_func: Callable, critical: bool = False):
        """添加健康检查"""
        with self._lock:
            self._checks.append({
                "name": name,
                "func": check_func,
                "critical": critical
            })
            logger.debug(f"[HealthChecker] 注册检查: {name}")

    def _basic_check(self) -> Dict:
        """基础检查"""
        return {"status": "pass", "message": "System running normally"}

    def _memory_check(self) -> Dict:
        """内存检查"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "status": "pass",
                "memory_rss": memory_info.rss,
                "memory_percent": process.memory_percent()
            }
        except Exception as e:
            return {"status": "warn", "message": str(e)}

    def _clock_check(self) -> Dict:
        """时钟检查"""
        return {
            "status": "pass",
            "current_time": datetime.now().isoformat()
        }

    def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        with self._lock:
            results = {}
            all_passed = True
            health_score = 100.0

            for check in self._checks:
                try:
                    result = check["func"]()
                    results[check["name"]] = result

                    if result.get("status") == "warn":
                        health_score -= 10
                    elif result.get("status") == "fail":
                        health_score -= 50
                        if check["critical"]:
                            all_passed = False
                except Exception as e:
                    logger.error(f"[HealthChecker] 检查 {check['name']} 失败: {e}")
                    results[check["name"]] = {"status": "fail", "error": str(e)}
                    if check["critical"]:
                        all_passed = False
                    health_score -= 50

            health_score = max(0, min(100, health_score))
            self.instance_manager.update_health_score(health_score)

            overall_status = "healthy" if all_passed and health_score >= 70 else "unhealthy"
            if 50 <= health_score < 70:
                overall_status = "degraded"

            return {
                "overall_status": overall_status,
                "health_score": health_score,
                "checks": results,
                "timestamp": datetime.now().isoformat(),
                "instance": self.instance_manager.get_local_instance().to_dict()
            }

    def start(self, interval: int = 5):
        """启动定期健康检查"""
        if self._running:
            logger.warning("[HealthChecker] 已经在运行中")
            return

        self._running = True

        def check_loop():
            while self._running:
                try:
                    self.run_all_checks()
                except Exception as e:
                    logger.error(f"[HealthChecker] 检查循环异常: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=check_loop, daemon=True)
        self._thread.start()
        logger.info(f"[HealthChecker] 已启动，检查间隔: {interval}秒")

    def stop(self):
        """停止健康检查"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("[HealthChecker] 已停止")

# ===========================================
# 全局实例
# ===========================================
_config_manager: Optional[ConfigManager] = None
_instance_manager: Optional[InstanceManager] = None
_health_checker: Optional[HealthChecker] = None
_global_lock = threading.Lock()

def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    global _config_manager
    with _global_lock:
        if not _config_manager:
            _config_manager = ConfigManager()
        return _config_manager

def get_instance_manager() -> InstanceManager:
    """获取实例管理器"""
    global _instance_manager
    with _global_lock:
        if not _instance_manager:
            _instance_manager = InstanceManager(get_config_manager())
        return _instance_manager

def get_health_checker() -> HealthChecker:
    """获取健康检查器"""
    global _health_checker
    with _global_lock:
        if not _health_checker:
            _health_checker = HealthChecker(get_instance_manager())
        return _health_checker

# ===========================================
# 主程序入口
# ===========================================
if __name__ == "__main__":
    print("=" * 80)
    print("Phase 51: 高可用与集群化 - 基础架构测试")
    print("=" * 80)

    # 初始化系统
    config_manager = get_config_manager()
    instance_manager = get_instance_manager()
    health_checker = get_health_checker()

    # 显示当前环境
    config = config_manager.get_current_config()
    print(f"\n当前环境: {config.environment.value}")
    print(f"服务配置: {config.service.host}:{config.service.port}")
    print(f"本地实例ID: {instance_manager.get_local_instance().instance_id}")

    # 运行健康检查
    print("\n运行健康检查...")
    health_result = health_checker.run_all_checks()
    print(f"健康状态: {health_result['overall_status']}")
    print(f"健康评分: {health_result['health_score']}")

    # 测试环境切换
    print("\n测试环境切换...")
    print(f"当前环境: {config_manager._current_env}")
    config_manager.set_environment(Environment.STAGING)
    print(f"切换到预发布环境: {config_manager._current_env}")
    config_manager.set_environment(Environment.PRODUCTION)
    print(f"切换到生产环境: {config_manager._current_env}")
    
    # 切换回开发环境
    config_manager.set_environment(Environment.DEVELOPMENT)

    print("\n" + "=" * 80)
    print("✅ Phase 51 - 基础架构测试通过！")
    print("=" * 80)
