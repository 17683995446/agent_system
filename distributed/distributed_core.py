"""
分布式微服务架构核心组件
Phase 8.1: 分布式微服务架构设计
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timezone
import json
import uuid
import threading
import logging
import os

# 配置详细的日志
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase44_detailed.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    STARTING = auto()
    HEALTHY = auto()  # 新增：健康状态
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
    DEGRADED = auto()


class ServiceType(Enum):
    """服务类型枚举"""
    API_GATEWAY = auto()
    AUTH_SERVICE = auto()
    AGENT_SERVICE = auto()
    MEMORY_SERVICE = auto()
    EVOLUTION_SERVICE = auto()
    MONITORING_SERVICE = auto()
    ANALYTICS_SERVICE = auto()
    AI_AGENT_SERVICE = auto()
    TASK_SERVICE = auto()
    NOTIFICATION_SERVICE = auto()
    USER_MANAGEMENT = auto()
    TASK_EXECUTOR = auto()
    MEMORY_MANAGER = auto()
    PROXY = auto()
    LOGGING = auto()
    MONITORING = auto()
    CACHE = auto()
    DATABASE = auto()
    MESSAGE_QUEUE = auto()
    EVENT_BUS = auto()


@dataclass
class ServiceInstance:
    """服务实例数据类"""
    instance_id: str
    service_name: str
    service_type: ServiceType
    version: str
    host: str
    port: int
    status: ServiceStatus
    health_score: float = 1.0
    load_factor: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "service_name": self.service_name,
            "service_type": self.service_type.name,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "status": self.status.name,
            "health_score": self.health_score,
            "load_factor": self.load_factor,
            "started_at": self.started_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ServiceConfig:
    """服务配置"""
    service_name: str
    service_type: ServiceType
    version: str
    max_instances: int = 10
    min_instances: int = 1
    health_check_interval: float = 30.0
    circuit_breaker_threshold: int = 5
    retry_count: int = 3
    timeout_seconds: float = 30.0
    enable_load_balancing: bool = True


class BaseService(ABC):
    """微服务基类"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.instance_id = f"{config.service_name}-{uuid.uuid4().hex[:8]}"
        self.status = ServiceStatus.STARTING
        self.started_at = datetime.now(timezone.utc)
        self.metrics: Dict[str, Any] = {}
        
    @abstractmethod
    async def start(self) -> bool:
        """启动服务"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止服务"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        pass
    
    def get_instance_info(self) -> ServiceInstance:
        """获取服务实例信息"""
        return ServiceInstance(
            instance_id=self.instance_id,
            service_name=self.config.service_name,
            service_type=self.config.service_type,
            version=self.config.version,
            host="0.0.0.0",
            port=8000,
            status=self.status,
            health_score=1.0,
            started_at=self.started_at
        )


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
        self._instance_index: Dict[str, ServiceInstance] = {}
        self._lock = threading.RLock()  # 添加线程安全锁
        
    async def register(self, instance: ServiceInstance) -> bool:
        """注册服务"""
        logger.debug(f"[register] 进入方法，service_name: {instance.service_name}, instance_id: {instance.instance_id}")
        with self._lock:
            service_name = instance.service_name
            if service_name not in self._services:
                self._services[service_name] = []
            
            existing = self._instance_index.get(instance.instance_id)
            if existing:
                # 从旧位置移除
                logger.debug(f"[register] 发现已存在的实例，移除旧实例: {existing.instance_id}")
                self._services[existing.service_name] = [
                    s for s in self._services[existing.service_name]
                    if s.instance_id != existing.instance_id
                ]
            
            self._services[service_name].append(instance)
            self._instance_index[instance.instance_id] = instance
            logger.debug(f"[register] 服务注册成功: {instance.instance_id}")
            return True
    
    async def unregister(self, instance_id: str) -> bool:
        """注销服务"""
        logger.debug(f"[unregister] 进入方法，instance_id: {instance_id}")
        with self._lock:
            instance = self._instance_index.get(instance_id)
            if instance:
                self._services[instance.service_name] = [
                    s for s in self._services[instance.service_name]
                    if s.instance_id != instance_id
                ]
                del self._instance_index[instance_id]
                logger.debug(f"[unregister] 服务注销成功: {instance_id}")
                return True
            logger.debug(f"[unregister] 服务实例不存在: {instance_id}")
            return False
    
    async def discover(self, service_name: str) -> List[ServiceInstance]:
        """发现服务"""
        logger.debug(f"[discover] 进入方法，service_name: {service_name}")
        with self._lock:
            instances = self._services.get(service_name, [])
            healthy = [i for i in instances 
                      if i.status in (ServiceStatus.RUNNING, ServiceStatus.HEALTHY)
                      and i.health_score > 0.5]
            logger.debug(f"[discover] 找到 {len(instances)} 个实例，其中 {len(healthy)} 个健康")
            return sorted(healthy, key=lambda x: x.load_factor)
    
    async def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """获取所有服务"""
        with self._lock:
            return self._services.copy()
    
    async def update_heartbeat(self, instance_id: str) -> bool:
        """更新心跳"""
        with self._lock:
            instance = self._instance_index.get(instance_id)
            if instance:
                instance.last_heartbeat = datetime.now(timezone.utc)
                return True
            return False
    
    def register_service(self, service_name: str, service_type: ServiceType, 
                       host: str, port: int, version: str = "1.0.0") -> ServiceInstance:
        """注册服务 - 同步便捷方法"""
        with self._lock:
            import uuid
            instance = ServiceInstance(
                instance_id=str(uuid.uuid4()),
                service_name=service_name,
                service_type=service_type,
                version=version,
                host=host,
                port=port,
                status=ServiceStatus.HEALTHY
            )
            
            if service_name not in self._services:
                self._services[service_name] = []
            
            existing = self._instance_index.get(instance.instance_id)
            if existing:
                self._services[existing.service_name] = [
                    s for s in self._services[existing.service_name]
                    if s.instance_id != existing.instance_id
                ]
            
            self._services[service_name].append(instance)
            self._instance_index[instance.instance_id] = instance
            return instance
    
    def update_service_health(self, instance_id: str, health_score: float) -> bool:
        """更新服务健康状态"""
        logger.debug(f"[update_service_health] 进入方法，instance_id: {instance_id}, health_score: {health_score}")
        # 验证健康值范围 [0.0, 1.0]
        if health_score < 0.0 or health_score > 1.0:
            logger.error(f"[update_service_health] 健康值超出范围: {health_score}")
            raise ValueError("Health score must be between 0.0 and 1.0")
        
        with self._lock:
            instance = self._instance_index.get(instance_id)
            if instance:
                old_status = instance.status
                instance.health_score = health_score
                
                # 状态转换逻辑
                if instance.status in (ServiceStatus.STARTING, ServiceStatus.STOPPING, 
                                     ServiceStatus.STOPPED, ServiceStatus.ERROR):
                    # 这些状态不应该被健康检查改变
                    logger.debug(f"[update_service_health] 服务处于 {instance.status} 状态，不更新")
                    return True
                
                if health_score < 0.5:
                    new_status = ServiceStatus.DEGRADED
                else:
                    new_status = ServiceStatus.HEALTHY
                
                instance.status = new_status
                logger.debug(f"[update_service_health] 服务状态从 {old_status} 更新为 {new_status}")
                return True
            logger.debug(f"[update_service_health] 服务实例不存在: {instance_id}")
            return False
    
    def get_service_instance(self, instance_id: str) -> Optional[ServiceInstance]:
        """获取服务实例"""
        with self._lock:
            return self._instance_index.get(instance_id)
    
    def discover_service(self, service_type: ServiceType) -> List[ServiceInstance]:
        """发现指定类型的服务实例"""
        with self._lock:
            instances = []
            for service_instances in self._services.values():
                for instance in service_instances:
                    if instance.service_type == service_type and instance.status == ServiceStatus.HEALTHY:
                        instances.append(instance)
            return sorted(instances, key=lambda x: x.load_factor)
    
    def unregister_service(self, instance_id: str) -> bool:
        """注销服务实例 - 同步便捷方法"""
        with self._lock:
            instance = self._instance_index.get(instance_id)
            if instance:
                service_name = instance.service_name
                if service_name in self._services:
                    self._services[service_name] = [
                        s for s in self._services[service_name]
                        if s.instance_id != instance_id
                    ]
                del self._instance_index[instance_id]
                return True
            return False
    
    def update_service_status(self, instance_id: str, status: ServiceStatus) -> bool:
        """更新服务状态"""
        with self._lock:
            instance = self._instance_index.get(instance_id)
            if instance:
                instance.status = status
                return True
            return False


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self._round_robin_index: Dict[str, int] = {}
        
    def select_instance(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """选择服务实例"""
        logger.debug(f"[select_instance] 进入方法，实例数量: {len(instances) if instances else 0}")
        
        if not instances:
            logger.debug("[select_instance] 没有可用实例，返回None")
            return None
        
        # 过滤有效实例
        valid_instances = [
            inst for inst in instances 
            if inst.status in (ServiceStatus.HEALTHY, ServiceStatus.RUNNING)
        ]
        
        logger.debug(f"[select_instance] 有效实例数量: {len(valid_instances)}")
        
        # 如果没有有效实例，降级到次优实例
        if not valid_instances:
            # 尝试降级到 DEGRADED 状态实例
            degraded_instances = [
                inst for inst in instances 
                if inst.status == ServiceStatus.DEGRADED
            ]
            if degraded_instances:
                logger.warning(f"[select_instance] 降级到 DEGRADED 状态实例，选择: {degraded_instances[0].instance_id}")
                return degraded_instances[0]
            
            # 最后尝试其他状态实例
            logger.warning(f"[select_instance] 没有健康实例，选择第一个实例: {instances[0].instance_id}")
            return instances[0]
        
        if self.strategy == "round_robin":
            selected = self._round_robin(valid_instances)
        elif self.strategy == "least_load":
            selected = self._least_load(valid_instances)
        elif self.strategy == "random":
            import random
            selected = random.choice(valid_instances)
        else:
            selected = valid_instances[0]
        
        logger.debug(f"[select_instance] 选择实例: {selected.instance_id}")
        return selected
    
    def _round_robin(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """轮询策略"""
        service_name = instances[0].service_name
        if service_name not in self._round_robin_index:
            self._round_robin_index[service_name] = 0
        
        index = self._round_robin_index[service_name]
        instance = instances[index % len(instances)]
        self._round_robin_index[service_name] = (index + 1) % len(instances)
        return instance
    
    def _least_load(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """最小负载策略"""
        return min(instances, key=lambda x: x.load_factor)


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures: Dict[str, int] = {}
        self._last_failure: Dict[str, datetime] = {}
        self._state: Dict[str, str] = {}  # closed, open, half-open
    
    async def execute(self, service_name: str, func, *args, **kwargs):
        """执行带熔断保护的操作"""
        state = self._state.get(service_name, "closed")
        
        if state == "open":
            last_failure = self._last_failure.get(service_name)
            if last_failure and (datetime.now(timezone.utc) - last_failure).total_seconds() > self.recovery_timeout:
                self._state[service_name] = "half-open"
                state = "half-open"
            else:
                raise Exception(f"Circuit breaker open for {service_name}")
        
        try:
            result = await func(*args, **kwargs)
            if state == "half-open":
                self._state[service_name] = "closed"
                self._failures[service_name] = 0
            return result
        except Exception as e:
            if service_name not in self._failures:
                self._failures[service_name] = 0
            self._failures[service_name] += 1
            self._last_failure[service_name] = datetime.now(timezone.utc)
            
            if self._failures[service_name] >= self.failure_threshold:
                self._state[service_name] = "open"
            
            raise e


class DistributedSystemConfig:
    """分布式系统配置"""
    
    def __init__(self):
        self.service_registry = ServiceRegistry()
        self.load_balancer = LoadBalancer()
        self.circuit_breaker = CircuitBreaker()
        self._services: List[BaseService] = []
        
    async def register_service(self, service: BaseService) -> bool:
        """注册服务到系统"""
        self._services.append(service)
        instance = service.get_instance_info()
        await self.service_registry.register(instance)
        return True
    
    async def unregister_service(self, service: BaseService) -> bool:
        """注销服务"""
        if service in self._services:
            self._services.remove(service)
            await self.service_registry.unregister(service.instance_id)
        return True
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "total_services": len(self._services),
            "registered_services": await self.service_registry.get_all_services(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# 全局分布式系统配置
global_distributed_config = DistributedSystemConfig()
