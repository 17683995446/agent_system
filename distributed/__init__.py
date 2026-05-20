"""
Distributed System Module
Phase 8: Distributed Architecture & AI-Driven Auto-Evolution
"""

from .distributed_core import (
    ServiceStatus,
    ServiceType,
    ServiceInstance,
    ServiceConfig,
    BaseService,
    ServiceRegistry,
    LoadBalancer,
    CircuitBreaker,
    DistributedSystemConfig,
    global_distributed_config
)

from .auto_evolution import (
    EvolutionStrategy,
    EvolutionPhase,
    OptimizationType,
    EvolutionConfig,
    Genome,
    PopulationStats,
    BaseEvolutionaryOperator,
    EvolutionaryOperator,
    AutoEvolutionEngine
)

from .event_driven import (
    MessageType,
    EventType,
    MessageStatus,
    Message,
    Subscription,
    MessageQueue,
    InMemoryMessageQueue,
    EventBus,
    EventStreamProcessor,
    global_event_bus,
    global_event_processor
)

from .observability import (
    SpanStatus,
    SpanKind,
    Span,
    Trace,
    Tracer,
    Metric,
    MetricsRegistry,
    ObservabilitySystem,
    global_observability
)

__version__ = "5.0.0"

__all__ = [
    # Distributed Core
    "ServiceStatus",
    "ServiceType",
    "ServiceInstance",
    "ServiceConfig",
    "BaseService",
    "ServiceRegistry",
    "LoadBalancer",
    "CircuitBreaker",
    "DistributedSystemConfig",
    "global_distributed_config",
    
    # Auto Evolution
    "EvolutionStrategy",
    "EvolutionPhase",
    "OptimizationType",
    "EvolutionConfig",
    "Genome",
    "PopulationStats",
    "BaseEvolutionaryOperator",
    "EvolutionaryOperator",
    "AutoEvolutionEngine",
    
    # Event Driven
    "MessageType",
    "EventType",
    "MessageStatus",
    "Message",
    "Subscription",
    "MessageQueue",
    "InMemoryMessageQueue",
    "EventBus",
    "EventStreamProcessor",
    "global_event_bus",
    "global_event_processor",
    
    # Observability
    "SpanStatus",
    "SpanKind",
    "Span",
    "Trace",
    "Tracer",
    "Metric",
    "MetricsRegistry",
    "ObservabilitySystem",
    "global_observability"
]
