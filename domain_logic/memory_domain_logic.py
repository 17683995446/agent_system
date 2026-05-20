"""
第四层：领域逻辑层 - 记忆领域逻辑
定义记忆的核心业务规则和逻辑
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from domain_model.entities.memory_entity import MemoryEntity
from domain_model.enums.enums import MemoryTypeEnum, MemoryImportanceLevelEnum


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """确保datetime对象是时区感知的"""
    if dt is None:
        return None
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class MemoryDomainLogic:
    """记忆领域逻辑类 - 封装记忆的核心业务规则"""
    
    @staticmethod
    def validate_memory_content(content: str) -> bool:
        """验证记忆内容"""
        if not content or len(content.strip()) == 0:
            return False
        if len(content) > 50000:
            return False
        return True
    
    @staticmethod
    def validate_importance_score(score: int) -> bool:
        """验证重要性评分"""
        return 0 <= score <= 10
    
    @staticmethod
    def get_importance_level(score: int) -> str:
        """获取重要性级别"""
        if score >= 9:
            return MemoryImportanceLevelEnum.CRITICAL.value
        elif score >= 7:
            return MemoryImportanceLevelEnum.HIGH.value
        elif score >= 5:
            return MemoryImportanceLevelEnum.MEDIUM.value
        elif score >= 3:
            return MemoryImportanceLevelEnum.LOW.value
        else:
            return MemoryImportanceLevelEnum.MINIMAL.value
    
    @staticmethod
    def is_hot_memory(memory: MemoryEntity) -> bool:
        """判断是否为热记忆"""
        last_accessed = ensure_timezone_aware(memory.last_accessed_at)
        if last_accessed:
            hours_since_access = (datetime.now(timezone.utc) - last_accessed).total_seconds() / 3600
            if hours_since_access < 24:
                return True
        
        if memory.importance_score >= 8:
            return True
        
        return False
    
    @staticmethod
    def should_consolidate(memory: MemoryEntity) -> bool:
        """判断是否应该整合记忆"""
        if memory.memory_type in [MemoryTypeEnum.EXPERIENCE, MemoryTypeEnum.REFLECTION]:
            last_accessed = ensure_timezone_aware(memory.last_accessed_at)
            if not last_accessed:
                return True
            hours_since_access = (datetime.now(timezone.utc) - last_accessed).total_seconds() / 3600
            return hours_since_access >= 1
        return False
    
    @staticmethod
    def calculate_decay(memory: MemoryEntity) -> float:
        """计算记忆衰减系数"""
        created_at = ensure_timezone_aware(memory.created_at)
        if not created_at:
            return 1.0
        
        days_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 86400
        
        base_decay = max(0.1, 1.0 - (days_old / 30))
        
        importance_factor = memory.importance_score / 10.0
        
        decay = base_decay * (0.5 + 0.5 * importance_factor)
        
        return max(0.0, min(1.0, decay))
    
    @staticmethod
    def extract_tags(tags_str: Optional[str]) -> List[str]:
        """从字符串提取标签"""
        if not tags_str:
            return []
        return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    
    @staticmethod
    def has_tag(memory: MemoryEntity, tag: str) -> bool:
        """检查是否包含标签"""
        if not memory.tags:
            return False
        tags = MemoryDomainLogic.extract_tags(memory.tags)
        return tag in tags
    
    @staticmethod
    def calculate_relevance(memory: MemoryEntity) -> float:
        """计算记忆相关性评分"""
        importance_factor = memory.importance_score * 5
        access_factor = min(memory.access_count * 0.5, 25)
        
        last_accessed = ensure_timezone_aware(memory.last_accessed_at)
        if last_accessed:
            hours_since_access = (datetime.now(timezone.utc) - last_accessed).total_seconds() / 3600
            recency_factor = max(0, 10 - hours_since_access / 24)
        else:
            recency_factor = 0
        
        return importance_factor + access_factor + recency_factor
    
    @staticmethod
    def is_stale_memory(memory: MemoryEntity, max_age_days: int = 30) -> bool:
        """判断记忆是否过期"""
        created_at = ensure_timezone_aware(memory.created_at)
        if not created_at:
            return True
        
        days_old = (datetime.now(timezone.utc) - created_at).total_seconds() / 86400
        return days_old > max_age_days
