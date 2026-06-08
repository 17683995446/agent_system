"""
单元测试 - 日志系统
"""
import pytest
import sys
import io
from unittest.mock import MagicMock, patch

from infrastructure.logging.logging_system import (
    setup_logging,
    get_logger,
    StructuredLogger
)


class TestLoggingSystem:
    """测试日志系统"""
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        logger = get_logger("test_logger")
        assert logger is not None
    
    def test_structured_logger(self):
        """测试结构化日志记录器"""
        logger = StructuredLogger("test_structured")
        logger.info("test message", extra="value")
        assert True
    
    def test_logger_bind(self):
        """测试日志记录器绑定上下文"""
        logger = StructuredLogger("test_bind")
        bound_logger = logger.bind(user_id=123)
        assert bound_logger is not None
    
    def test_logger_all_methods(self):
        """测试所有日志方法"""
        logger = StructuredLogger("test_methods")
        
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")
        
        assert True
