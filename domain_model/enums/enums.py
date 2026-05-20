"""
第五层：领域模型层 - 枚举类型
定义所有业务枚举
"""
from enum import Enum


class TaskStatusEnum(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def is_terminal(self) -> bool:
        """判断是否为终态"""
        return self in [self.COMPLETED, self.FAILED, self.CANCELLED]
    
    def is_active(self) -> bool:
        """判断是否为活跃状态"""
        return self in [self.PENDING, self.RUNNING]


class MemoryTypeEnum(str, Enum):
    """记忆类型枚举"""
    EXPERIENCE = "experience"
    REFLECTION = "reflection"
    KNOWLEDGE = "knowledge"
    STRATEGY = "strategy"
    HOT_MEMORY = "hot_memory"
    
    def requires_processing(self) -> bool:
        """是否需要进一步处理"""
        return self in [self.EXPERIENCE, self.REFLECTION]


class KnowledgeCategoryEnum(str, Enum):
    """知识分类枚举"""
    LEARNING = "learning"
    REFLECTION = "reflection"
    EXPERIENCE = "experience"
    OPTIMIZATION = "optimization"
    GENERAL = "general"


class EvolutionPhaseEnum(str, Enum):
    """进化阶段枚举"""
    MEMORY_GOVERNANCE = "memory_governance"
    REFLECTION = "reflection"
    KNOWLEDGE_LEARNING = "knowledge_learning"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        names = {
            self.MEMORY_GOVERNANCE: "记忆治理",
            self.REFLECTION: "复盘反思",
            self.KNOWLEDGE_LEARNING: "知识学习",
            self.STRATEGY_OPTIMIZATION: "策略优化"
        }
        return names.get(self, self.value)


class SystemModeEnum(str, Enum):
    """系统模式枚举"""
    TASK_MODE = "task_mode"
    IDLE_MODE = "idle_mode"
    EVOLUTION_MODE = "evolution_mode"


class PriorityLevelEnum(int, Enum):
    """优先级级别枚举"""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3
    MINIMAL = 1


class MemoryImportanceLevelEnum(int, Enum):
    """记忆重要性级别枚举"""
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 5
    LOW = 3
    MINIMAL = 0
