"""
应用服务层 - 记忆应用服务
提供记忆相关的业务逻辑编排
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import uuid

from domain_model.entities.memory_entity import MemoryEntity
from domain_logic.memory_domain_logic import MemoryDomainLogic
from infrastructure.cache.cache_manager import CacheManager
from infrastructure.logging.logging_system import get_logger


class MemoryType(str, Enum):
    """记忆类型"""
    EXPERIENCE = "experience"   # 经验记忆
    REFLECTION = "reflection"   # 反思记忆
    KNOWLEDGE = "knowledge"     # 知识记忆
    STRATEGY = "strategy"       # 策略记忆
    HOT_MEMORY = "hot_memory"   # 热记忆


@dataclass
class MemorySearchQuery:
    """记忆搜索查询"""
    query_text: str
    memory_type: Optional[MemoryType] = None
    min_importance: Optional[int] = None
    created_after: Optional[datetime] = None
    tags: Optional[List[str]] = None
    limit: int = 10


@dataclass
class MemoryStats:
    """记忆统计信息"""
    total_memories: int
    by_type: Dict[str, int]
    by_importance: Dict[str, int]
    avg_access_count: float
    recent_access_count: int


class MemoryApplicationService:
    """记忆应用服务"""
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        domain_logic: Optional[MemoryDomainLogic] = None
    ):
        self.logger = get_logger("MemoryApplicationService")
        self.cache_manager = cache_manager or CacheManager(
            cache_type="lru", maxsize=1000
        )
        self.domain_logic = domain_logic or MemoryDomainLogic()
        
        # 内存中的记忆存储
        self._memory_store: Dict[str, MemoryEntity] = {}
        
        self.logger.info("MemoryApplicationService initialized")
    
    def create_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EXPERIENCE,
        importance_score: int = 5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntity:
        """创建新记忆"""
        if not self.domain_logic.validate_memory_content(content):
            raise ValueError(f"Invalid memory content: {content}")
        
        if not self.domain_logic.validate_importance_score(importance_score):
            raise ValueError(f"Invalid importance score: {importance_score}")
        
        from domain_model.enums.enums import MemoryTypeEnum
        
        # 转换枚举
        memory_type_enum = MemoryTypeEnum[memory_type.value.upper()]
        
        # 生成唯一标识符
        memory_id = str(uuid.uuid4())
        
        # 创建记忆实体
        memory = MemoryEntity(
            memory_identifier=memory_id,
            memory_content=content,
            memory_type=memory_type_enum,
            importance_score=importance_score,
            tags=",".join(tags) if tags else "",
            access_count=0
        )
        
        # 存储记忆
        self._memory_store[memory_id] = memory
        
        # 缓存记忆
        self.cache_manager.set(f"memory:{memory_id}", memory)
        
        self.logger.info(f"Created memory: {memory_id}")
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntity]:
        """获取记忆"""
        # 先查缓存
        cached = self.cache_manager.get(f"memory:{memory_id}")
        if cached:
            # 更新访问计数
            if memory_id in self._memory_store:
                self._memory_store[memory_id].access_count += 1
                self._memory_store[memory_id].accessed_at = datetime.now(timezone.utc)
            return cached
        
        # 从存储获取
        memory = self._memory_store.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.accessed_at = datetime.now(timezone.utc)
            self.cache_manager.set(f"memory:{memory_id}", memory)
        
        return memory
    
    def search_memories(self, query: MemorySearchQuery) -> List[MemoryEntity]:
        """搜索记忆"""
        results = []
        
        for memory in self._memory_store.values():
            # 文本匹配
            if query.query_text.lower() not in memory.memory_content.lower():
                continue
            
            # 类型过滤
            if query.memory_type:
                if memory.memory_type.value != query.memory_type.value:
                    continue
            
            # 重要性过滤
            if query.min_importance:
                if memory.importance_score < query.min_importance:
                    continue
            
            results.append(memory)
        
        # 按重要性排序
        results.sort(key=lambda m: -m.importance_score)
        
        return results[:query.limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self._memory_store:
            del self._memory_store[memory_id]
            self.cache_manager.delete(f"memory:{memory_id}")
            self.logger.info(f"Deleted memory: {memory_id}")
            return True
        return False
    
    def get_memory_stats(self) -> MemoryStats:
        """获取记忆统计"""
        total = len(self._memory_store)
        
        by_type: Dict[str, int] = {}
        by_importance: Dict[str, int] = {}
        
        for memory in self._memory_store.values():
            type_key = memory.memory_type.value if memory.memory_type else "unknown"
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            imp_level = str(memory.importance_score)
            by_importance[imp_level] = by_importance.get(imp_level, 0) + 1
        
        access_counts = [m.access_count or 0 for m in self._memory_store.values()]
        avg_access = sum(access_counts) / total if total > 0 else 0
        
        recent_access = sum(1 for m in self._memory_store.values() if (
            m.accessed_at and
            (datetime.now(timezone.utc) - m.accessed_at).total_seconds() < 3600
        ))
        
        return MemoryStats(
            total_memories=total,
            by_type=by_type,
            by_importance=by_importance,
            avg_access_count=avg_access,
            recent_access_count=recent_access
        )
    
    def cleanup_expired_memories(self, max_age_days: int = 30) -> int:
        """清理过期记忆"""
        cleaned_count = 0
        memory_ids = list(self._memory_store.keys())
        
        for memory_id in memory_ids:
            memory = self._memory_store.get(memory_id)
            if memory and self.domain_logic.is_stale_memory(memory, max_age_days):
                self.delete_memory(memory_id)
                cleaned_count += 1
        
        self.logger.info(f"Cleaned up {cleaned_count} expired memories")
        return cleaned_count
