"""
第四层：领域逻辑层 - 记忆领域逻辑单元测试
测试记忆核心业务规则
"""
import pytest
from datetime import datetime, timedelta

from domain_logic.memory_domain_logic import MemoryDomainLogic
from domain_model.enums.enums import MemoryTypeEnum, MemoryImportanceLevelEnum


class MockMemoryEntity:
    """模拟记忆实体类"""
    
    def __init__(
        self,
        memory_identifier: str = "test-memory-id",
        memory_content: str = "测试记忆内容",
        memory_type: MemoryTypeEnum = MemoryTypeEnum.EXPERIENCE,
        importance_score: int = 5,
        created_at: datetime = None,
        last_accessed_at: datetime = None,
        access_count: int = 0,
        tags: str = None
    ):
        self.memory_identifier = memory_identifier
        self.memory_content = memory_content
        self.memory_type = memory_type
        self.importance_score = importance_score
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed_at = last_accessed_at or datetime.utcnow()
        self.access_count = access_count
        self.tags = tags


class TestMemoryDomainLogicValidation:
    """测试记忆领域逻辑 - 验证方法"""
    
    def test_validate_memory_content_with_valid_content(self):
        """测试验证有效记忆内容"""
        valid_contents = [
            "简单记忆",
            "这是一个稍微复杂的记忆内容",
            "A" * 5000,
            "记忆包含特殊字符 !@#$%^&*()",
            "记忆包含中文内容测试"
        ]
        
        for content in valid_contents:
            assert MemoryDomainLogic.validate_memory_content(content) is True
    
    def test_validate_memory_content_with_empty_content(self):
        """测试验证空记忆内容"""
        invalid_contents = [
            "",
            "   ",
            "\t",
            "\n"
        ]
        
        for content in invalid_contents:
            assert MemoryDomainLogic.validate_memory_content(content) is False
    
    def test_validate_memory_content_with_none_content(self):
        """测试验证None记忆内容"""
        assert MemoryDomainLogic.validate_memory_content(None) is False
    
    def test_validate_memory_content_with_too_long_content(self):
        """测试验证超长记忆内容"""
        too_long_content = "A" * 50001
        assert MemoryDomainLogic.validate_memory_content(too_long_content) is False
    
    def test_validate_importance_score_with_valid_score(self):
        """测试验证有效重要性评分"""
        valid_scores = [0, 1, 5, 8, 10]
        
        for score in valid_scores:
            assert MemoryDomainLogic.validate_importance_score(score) is True
    
    def test_validate_importance_score_with_invalid_score(self):
        """测试验证无效重要性评分"""
        invalid_scores = [-1, 11, 100, -100]
        
        for score in invalid_scores:
            assert MemoryDomainLogic.validate_importance_score(score) is False


class TestMemoryDomainLogicImportanceLevel:
    """测试记忆领域逻辑 - 重要性级别"""
    
    def test_get_importance_level_critical(self):
        """测试获取临界重要性"""
        assert MemoryDomainLogic.get_importance_level(10) == MemoryImportanceLevelEnum.CRITICAL
        assert MemoryDomainLogic.get_importance_level(9) == MemoryImportanceLevelEnum.CRITICAL
    
    def test_get_importance_level_high(self):
        """测试获取高重要性"""
        assert MemoryDomainLogic.get_importance_level(8) == MemoryImportanceLevelEnum.HIGH
        assert MemoryDomainLogic.get_importance_level(7) == MemoryImportanceLevelEnum.HIGH
    
    def test_get_importance_level_medium(self):
        """测试获取中等重要性"""
        assert MemoryDomainLogic.get_importance_level(5) == MemoryImportanceLevelEnum.MEDIUM
        assert MemoryDomainLogic.get_importance_level(6) == MemoryImportanceLevelEnum.MEDIUM
    
    def test_get_importance_level_low(self):
        """测试获取低重要性"""
        assert MemoryDomainLogic.get_importance_level(3) == MemoryImportanceLevelEnum.LOW
        assert MemoryDomainLogic.get_importance_level(4) == MemoryImportanceLevelEnum.LOW
    
    def test_get_importance_level_minimal(self):
        """测试获取最低重要性"""
        assert MemoryDomainLogic.get_importance_level(0) == MemoryImportanceLevelEnum.MINIMAL
        assert MemoryDomainLogic.get_importance_level(1) == MemoryImportanceLevelEnum.MINIMAL
        assert MemoryDomainLogic.get_importance_level(2) == MemoryImportanceLevelEnum.MINIMAL


class TestMemoryDomainLogicHotMemory:
    """测试记忆领域逻辑 - 热记忆判断"""
    
    def test_is_hot_memory_with_recent_access(self):
        """测试最近访问的是热记忆"""
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        memory = MockMemoryEntity(last_accessed_at=recent_time)
        assert MemoryDomainLogic.is_hot_memory(memory) is True
    
    def test_is_not_hot_memory_with_old_access(self):
        """测试较早访问的不是热记忆"""
        old_time = datetime.utcnow() - timedelta(days=2)
        memory = MockMemoryEntity(last_accessed_at=old_time)
        assert MemoryDomainLogic.is_hot_memory(memory) is False
    
    def test_is_hot_memory_with_high_importance(self):
        """测试高重要性是热记忆"""
        old_time = datetime.utcnow() - timedelta(days=3)
        memory = MockMemoryEntity(
            last_accessed_at=old_time,
            importance_score=9
        )
        assert MemoryDomainLogic.is_hot_memory(memory) is True
    
    def test_is_not_hot_memory_with_low_importance_and_old_access(self):
        """测试低重要性和旧访问不是热记忆"""
        old_time = datetime.utcnow() - timedelta(days=3)
        memory = MockMemoryEntity(
            last_accessed_at=old_time,
            importance_score=3
        )
        assert MemoryDomainLogic.is_hot_memory(memory) is False


class TestMemoryDomainLogicConsolidation:
    """测试记忆领域逻辑 - 记忆整合"""
    
    def test_should_consolidate_with_experience_memory_old(self):
        """测试旧的经验记忆应该整合"""
        old_time = datetime.utcnow() - timedelta(hours=2)
        memory = MockMemoryEntity(
            memory_type=MemoryTypeEnum.EXPERIENCE,
            last_accessed_at=old_time
        )
        assert MemoryDomainLogic.should_consolidate(memory) is True
    
    def test_should_consolidate_with_reflection_memory_old(self):
        """测试旧的反思记忆应该整合"""
        old_time = datetime.utcnow() - timedelta(hours=2)
        memory = MockMemoryEntity(
            memory_type=MemoryTypeEnum.REFLECTION,
            last_accessed_at=old_time
        )
        assert MemoryDomainLogic.should_consolidate(memory) is True
    
    def test_should_not_consolidate_hot_memory(self):
        """测试热记忆不应该整合"""
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        memory = MockMemoryEntity(
            memory_type=MemoryTypeEnum.EXPERIENCE,
            last_accessed_at=recent_time
        )
        assert MemoryDomainLogic.should_consolidate(memory) is False
    
    def test_should_not_consolidate_strategy_memory(self):
        """测试策略记忆不应该整合"""
        memory = MockMemoryEntity(memory_type=MemoryTypeEnum.STRATEGY)
        assert MemoryDomainLogic.should_consolidate(memory) is False


class TestMemoryDomainLogicDecay:
    """测试记忆领域逻辑 - 记忆衰减"""
    
    def test_calculate_decay_with_recent_memory(self):
        """测试新记忆衰减较慢"""
        recent_time = datetime.utcnow() - timedelta(hours=1)
        memory = MockMemoryEntity(
            created_at=recent_time,
            importance_score=5
        )
        decay = MemoryDomainLogic.calculate_decay(memory)
        assert 0.7 < decay <= 1.0
    
    def test_calculate_decay_with_old_memory(self):
        """测试旧记忆衰减较快"""
        old_time = datetime.utcnow() - timedelta(days=30)
        memory = MockMemoryEntity(
            created_at=old_time,
            importance_score=5
        )
        decay = MemoryDomainLogic.calculate_decay(memory)
        assert 0.05 <= decay < 0.15
    
    def test_calculate_decay_with_high_importance(self):
        """测试高重要性记忆衰减较慢"""
        old_time = datetime.utcnow() - timedelta(days=30)
        memory = MockMemoryEntity(
            created_at=old_time,
            importance_score=10
        )
        decay = MemoryDomainLogic.calculate_decay(memory)
        assert 0.08 <= decay < 0.15


class TestMemoryDomainLogicTags:
    """测试记忆领域逻辑 - 标签处理"""
    
    def test_extract_tags_from_string(self):
        """测试从字符串提取标签"""
        tags_str = "python,fastapi,database,test"
        tags = MemoryDomainLogic.extract_tags(tags_str)
        assert len(tags) == 4
        assert "python" in tags
        assert "fastapi" in tags
    
    def test_extract_tags_from_none(self):
        """测试从None提取标签"""
        tags = MemoryDomainLogic.extract_tags(None)
        assert tags == []
    
    def test_extract_tags_from_empty_string(self):
        """测试从空字符串提取标签"""
        tags = MemoryDomainLogic.extract_tags("")
        assert tags == []
    
    def test_has_tag_with_matching_tag(self):
        """测试匹配标签检测"""
        memory = MockMemoryEntity(tags="python,javascript,go")
        assert MemoryDomainLogic.has_tag(memory, "python") is True
    
    def test_has_tag_without_matching_tag(self):
        """测试不匹配标签检测"""
        memory = MockMemoryEntity(tags="python,javascript,go")
        assert MemoryDomainLogic.has_tag(memory, "rust") is False


class TestMemoryDomainLogicRelevance:
    """测试记忆领域逻辑 - 相关性评分"""
    
    def test_calculate_relevance_with_high_importance(self):
        """测试高重要性记忆相关性"""
        memory = MockMemoryEntity(
            importance_score=9,
            access_count=10
        )
        relevance = MemoryDomainLogic.calculate_relevance(memory)
        assert relevance > 50
    
    def test_calculate_relevance_with_high_access_count(self):
        """测试高访问次数记忆相关性"""
        memory = MockMemoryEntity(
            importance_score=5,
            access_count=100
        )
        relevance = MemoryDomainLogic.calculate_relevance(memory)
        assert relevance > 40
    
    def test_calculate_relevance_with_low_scores(self):
        """测试低评分记忆相关性"""
        memory = MockMemoryEntity(
            importance_score=2,
            access_count=1
        )
        relevance = MemoryDomainLogic.calculate_relevance(memory)
        assert relevance < 25
