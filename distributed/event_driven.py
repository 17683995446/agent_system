"""
消息队列与事件驱动架构
Phase 8.3: 消息队列与事件驱动
"""

from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timezone
import asyncio
import uuid
import json
from collections import deque


class MessageType(Enum):
    """消息类型"""
    COMMAND = auto()
    EVENT = auto()
    QUERY = auto()
    RESPONSE = auto()
    ERROR = auto()


class EventType(Enum):
    """事件类型"""
    AGENT_CREATED = auto()
    AGENT_UPDATED = auto()
    AGENT_DELETED = auto()
    MEMORY_ADDED = auto()
    MEMORY_UPDATED = auto()
    EVOLUTION_STARTED = auto()
    EVOLUTION_COMPLETED = auto()
    SYSTEM_ALERT = auto()
    METRIC_RECORDED = auto()
    USER_ACTION = auto()
    SCHEDULED_TASK = auto()
    WEBHOOK = auto()


class MessageStatus(Enum):
    """消息状态"""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    DEAD_LETTER = auto()


@dataclass
class Message:
    """消息数据类"""
    message_id: str
    message_type: MessageType
    event_type: Optional[EventType] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: Optional[str] = None
    destination: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: int = 5
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.name,
            "event_type": self.event_type.name if self.event_type else None,
            "payload": self.payload,
            "metadata": self.metadata,
            "status": self.status.name,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "destination": self.destination,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "ttl_seconds": self.ttl_seconds
        }
    
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > self.ttl_seconds


@dataclass
class Subscription:
    """订阅数据类"""
    subscription_id: str
    event_types: List[EventType]
    callback: Callable[[Message], Any]
    queue_name: str
    max_concurrency: int = 1
    enabled: bool = True


class MessageQueue(ABC):
    """消息队列基类"""
    
    @abstractmethod
    async def publish(self, message: Message) -> bool:
        """发布消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, subscription: Subscription) -> str:
        """订阅消息"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        pass
    
    @abstractmethod
    async def consume(self, queue_name: str, count: int = 10) -> List[Message]:
        """消费消息"""
        pass
    
    @abstractmethod
    async def ack(self, message_id: str) -> bool:
        """确认消息"""
        pass
    
    @abstractmethod
    async def nack(self, message_id: str, requeue: bool = True) -> bool:
        """拒绝消息"""
        pass


class InMemoryMessageQueue(MessageQueue):
    """内存消息队列实现"""
    
    def __init__(self):
        self._queues: Dict[str, deque] = {}
        self._subscriptions: Dict[str, Subscription] = {}
        self._pending_messages: Dict[str, Message] = {}
        self._processing_messages: Dict[str, Message] = {}
        self._dead_letters: List[Message] = []
        self._lock = asyncio.Lock()
    
    async def publish(self, message: Message) -> bool:
        queue_name = message.destination or "default"
        
        if queue_name not in self._queues:
            self._queues[queue_name] = deque()
        
        async with self._lock:
            self._queues[queue_name].append(message)
            self._pending_messages[message.message_id] = message
        
        await self._deliver_to_subscribers(message)
        return True
    
    async def subscribe(self, subscription: Subscription) -> str:
        async with self._lock:
            self._subscriptions[subscription.subscription_id] = subscription
        return subscription.subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        async with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                return True
        return False
    
    async def consume(self, queue_name: str, count: int = 10) -> List[Message]:
        if queue_name not in self._queues:
            return []
        
        messages = []
        async with self._lock:
            queue = self._queues[queue_name]
            for _ in range(min(count, len(queue))):
                if queue:
                    msg = queue.popleft()
                    if not msg.is_expired():
                        msg.status = MessageStatus.PROCESSING
                        self._processing_messages[msg.message_id] = msg
                        messages.append(msg)
                    else:
                        self._dead_letters.append(msg)
        
        return messages
    
    async def ack(self, message_id: str) -> bool:
        async with self._lock:
            if message_id in self._processing_messages:
                msg = self._processing_messages[message_id]
                msg.status = MessageStatus.COMPLETED
                del self._processing_messages[message_id]
                if message_id in self._pending_messages:
                    del self._pending_messages[message_id]
                return True
        return False
    
    async def nack(self, message_id: str, requeue: bool = True) -> bool:
        async with self._lock:
            if message_id in self._processing_messages:
                msg = self._processing_messages[message_id]
                if requeue and msg.retry_count < msg.max_retries:
                    msg.retry_count += 1
                    msg.status = MessageStatus.PENDING
                    queue_name = msg.destination or "default"
                    if queue_name not in self._queues:
                        self._queues[queue_name] = deque()
                    self._queues[queue_name].append(msg)
                else:
                    msg.status = MessageStatus.DEAD_LETTER
                    self._dead_letters.append(msg)
                
                del self._processing_messages[message_id]
                return True
        return False
    
    async def _deliver_to_subscribers(self, message: Message):
        """分发消息给订阅者"""
        if not message.event_type:
            return
        
        for subscription in list(self._subscriptions.values()):
            if not subscription.enabled:
                continue
            
            if message.event_type in subscription.event_types:
                try:
                    if asyncio.iscoroutinefunction(subscription.callback):
                        asyncio.create_task(subscription.callback(message))
                    else:
                        subscription.callback(message)
                except Exception as e:
                    print(f"Subscription error: {e}")


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._queue = InMemoryMessageQueue()
        self._subscriptions: Dict[str, Subscription] = {}
        self._listeners: Dict[EventType, List[Callable]] = {}
    
    async def emit(self, event_type: EventType, payload: Dict[str, Any], 
                  source: Optional[str] = None, priority: int = 5) -> str:
        """发送事件"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.EVENT,
            event_type=event_type,
            payload=payload,
            source=source,
            priority=priority
        )
        
        await self._queue.publish(message)
        return message.message_id
    
    def on(self, event_type: EventType, callback: Callable[[Message], Any], 
          max_concurrency: int = 1) -> str:
        """注册事件监听"""
        subscription_id = str(uuid.uuid4())
        
        subscription = Subscription(
            subscription_id=subscription_id,
            event_types=[event_type],
            callback=callback,
            queue_name=f"event-{event_type.name.lower()}",
            max_concurrency=max_concurrency
        )
        
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        self._listeners[event_type].append(callback)
        self._subscriptions[subscription_id] = subscription
        asyncio.create_task(self._queue.subscribe(subscription))
        
        return subscription_id
    
    def off(self, subscription_id: str) -> bool:
        """取消事件监听"""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
            return True
        return False
    
    async def send_command(self, command_name: str, payload: Dict[str, Any],
                         target: str, correlation_id: Optional[str] = None) -> str:
        """发送命令"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.COMMAND,
            payload={"command": command_name, **payload},
            destination=target,
            correlation_id=correlation_id or str(uuid.uuid4()),
            priority=7
        )
        
        await self._queue.publish(message)
        return message.message_id
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            "pending_count": len(self._queue._pending_messages),
            "processing_count": len(self._queue._processing_messages),
            "dead_letter_count": len(self._queue._dead_letters),
            "subscription_count": len(self._subscriptions),
            "listener_count": sum(len(v) for v in self._listeners.values())
        }


class EventStreamProcessor:
    """事件流处理器"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._stream_history: List[Message] = []
        self._aggregates: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._is_replaying = False
    
    async def process_event(self, message: Message):
        """处理事件"""
        if not self._is_replaying:
            self._stream_history.append(message)
        
        await self._apply_event(message)
        await self._check_reaction(message)
    
    async def _apply_event(self, message: Message):
        """应用事件到聚合"""
        if message.event_type and message.payload:
            aggregate_id = message.payload.get("aggregate_id", "global")
            if aggregate_id not in self._aggregates:
                self._aggregates[aggregate_id] = {}
            
            aggregate = self._aggregates[aggregate_id]
            
            if message.event_type == EventType.AGENT_CREATED:
                agent_id = message.payload.get("agent_id")
                if agent_id:
                    aggregate[agent_id] = {
                        "created_at": message.timestamp,
                        "status": "active",
                        **message.payload
                    }
            
            elif message.event_type == EventType.MEMORY_ADDED:
                if "memories" not in aggregate:
                    aggregate["memories"] = []
                aggregate["memories"].append(message.payload)
    
    async def _check_reaction(self, message: Message):
        """检查事件反应"""
        if message.event_type == EventType.SYSTEM_ALERT:
            priority = message.payload.get("priority", "low")
            if priority in ["high", "critical"]:
                print(f"ALERT REACTION: {message.payload}")
    
    async def replay_events(self, from_index: int = 0, to_index: Optional[int] = None):
        """重放事件"""
        self._is_replaying = True
        try:
            events = self._stream_history[from_index:to_index]
            for event in events:
                await self._apply_event(event)
        finally:
            self._is_replaying = False
    
    def get_aggregate(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """获取聚合状态"""
        return self._aggregates.get(aggregate_id)
    
    def create_snapshot(self, aggregate_id: str) -> str:
        """创建快照"""
        snapshot_id = str(uuid.uuid4())
        self._snapshots[snapshot_id] = {
            "aggregate_id": aggregate_id,
            "state": self._aggregates.get(aggregate_id, {}),
            "timestamp": datetime.now(timezone.utc),
            "event_count": len(self._stream_history)
        }
        return snapshot_id
    
    async def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """从快照恢复"""
        if snapshot_id not in self._snapshots:
            return False
        
        snapshot = self._snapshots[snapshot_id]
        aggregate_id = snapshot["aggregate_id"]
        self._aggregates[aggregate_id] = snapshot["state"].copy()
        
        event_count = snapshot["event_count"]
        await self.replay_events(from_index=event_count)
        return True


# 全局事件总线
global_event_bus = EventBus()

# 全局事件流处理器
global_event_processor = EventStreamProcessor(global_event_bus)
