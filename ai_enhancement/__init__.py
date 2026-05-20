"""
Agent 永续自进化运行系统 - AI 智能增强模块
Version: v6.0.0
优化点: 12个AI增强功能
"""

from .ai_core import (
    # 枚举
    AITaskType, ModelStatus, EvolutionStrategyV2,
    # 数据类
    Feature, KnowledgeNode, KnowledgeEdge, AIModelVersion, Experience,
    # 核心引擎
    EnhancedEvolutionEngine, QLearningAgent, KnowledgeGraph,
    IntelligentDiagnosis, AdaptiveParameterTuner, AIModelRegistry,
    # 全局实例
    enhanced_evolution_engine, knowledge_graph,
    intelligent_diagnosis, adaptive_tuner, ai_model_registry
)

__all__ = [
    # 枚举
    "AITaskType", "ModelStatus", "EvolutionStrategyV2",
    # 数据类
    "Feature", "KnowledgeNode", "KnowledgeEdge", "AIModelVersion", "Experience",
    # 核心引擎
    "EnhancedEvolutionEngine", "QLearningAgent", "KnowledgeGraph",
    "IntelligentDiagnosis", "AdaptiveParameterTuner", "AIModelRegistry",
    # 全局实例
    "enhanced_evolution_engine", "knowledge_graph",
    "intelligent_diagnosis", "adaptive_tuner", "ai_model_registry"
]
