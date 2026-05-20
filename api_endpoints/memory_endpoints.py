"""
API端点层 - 记忆管理API
提供记忆的完整生命周期管理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from domain_model.entities.memory_entity import MemoryEntity
from domain_model.enums.enums import MemoryTypeEnum
from application_service.memory_application_service import (
    MemoryApplicationService, MemoryType, MemorySearchQuery
)
from infrastructure.logging.logging_system import get_logger


@dataclass
class MemoryResponse:
    """记忆响应对象"""
    memory_id: str
    content: str
    memory_type: str
    importance_score: int
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: Optional[str] = None
    accessed_at: Optional[str] = None
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySearchResponse:
    """记忆搜索响应"""
    total: int
    results: List[MemoryResponse]
    search_time_ms: float


class MemoryEndpoints:
    """记忆管理API端点"""

    def __init__(self, memory_service: Optional[MemoryApplicationService] = None):
        self.logger = get_logger("MemoryEndpoints")
        self.memory_service = memory_service or MemoryApplicationService()
        self.logger.info("MemoryEndpoints initialized")

    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EXPERIENCE,
        importance_score: int = 5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryResponse:
        """创建新记忆"""
        memory = self.memory_service.create_memory(
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            tags=tags,
            metadata=metadata
        )
        return self._to_response(memory)

    async def get_memory(self, memory_id: str) -> Optional[MemoryResponse]:
        """获取记忆信息"""
        memory = self.memory_service.get_memory(memory_id)
        if memory:
            return self._to_response(memory)
        return None

    async def search_memories(
        self,
        query_text: str,
        memory_type: Optional[MemoryType] = None,
        min_importance: Optional[int] = None,
        created_after: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> MemorySearchResponse:
        """搜索记忆"""
        import time
        start_time = time.time()
        
        created_after_dt = None
        if created_after:
            try:
                created_after_dt = datetime.fromisoformat(created_after)
            except:
                pass
        
        search_query = MemorySearchQuery(
            query_text=query_text,
            memory_type=memory_type,
            min_importance=min_importance,
            created_after=created_after_dt,
            tags=tags,
            limit=limit
        )
        
        results = self.memory_service.search_memories(search_query)
        search_time = (time.time() - start_time) * 1000
        
        return MemorySearchResponse(
            total=len(results),
            results=[self._to_response(r) for r in results],
            search_time_ms=search_time
        )

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance_score: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[MemoryResponse]:
        """更新记忆"""
        memory = self.memory_service.update_memory(
            memory_id=memory_id,
            content=content,
            importance_score=importance_score,
            tags=tags
        )
        if memory:
            return self._to_response(memory)
        return None

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        success = self.memory_service.delete_memory(memory_id)
        return success

    async def get_memory_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = self.memory_service.get_memory_stats()
        return {
            "total_memories": stats.total_memories,
            "by_type": stats.by_type,
            "by_importance": stats.by_importance,
            "avg_access_count": stats.avg_access_count,
            "recent_access_count": stats.recent_access_count,
            "period_hours": hours,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def cleanup_expired_memories(self, max_age_days: int = 30) -> int:
        """清理过期记忆"""
        cleaned = self.memory_service.cleanup_expired_memories(max_age_days)
        self.logger.info(f"Cleaned up {cleaned} expired memories")
        return cleaned

    async def list_recent_memories(self, limit: int = 50, hours: int = 24) -> List[MemoryResponse]:
        """列出最近的记忆"""
        all_memories = await self.search_memories(
            query_text="",
            limit=limit
        )
        return all_memories.results

    def _to_response(self, memory: MemoryEntity) -> MemoryResponse:
        """转换为响应对象"""
        tags_str = memory.tags if isinstance(memory.tags, str) else ""
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
        
        return MemoryResponse(
            memory_id=memory.memory_identifier,
            content=memory.memory_content,
            memory_type=memory.memory_type.value if hasattr(memory.memory_type, "value") else str(memory.memory_type),
            importance_score=memory.importance_score,
            tags=tags_list,
            created_at=memory.created_at.isoformat() if memory.created_at else "",
            updated_at=memory.updated_at.isoformat() if memory.updated_at else None,
            accessed_at=memory.accessed_at.isoformat() if hasattr(memory, "accessed_at") and memory.accessed_at else None,
            access_count=memory.access_count or 0,
            metadata={}
        )
