"""
基础设施 - 日志系统
基于structlog的结构化日志
"""
import sys
import logging
from typing import Any, Dict
from pathlib import Path
from datetime import datetime
from rich.console import Console
import structlog
from structlog.stdlib import ProcessorFormatter


def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """配置结构化日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
    """
    processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if sys.stdout.isatty():
        processors.extend([
            structlog.dev.set_exc_info,
            structlog.processors.EventRenamer(to="msg"),
        ])
        console_renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            force_colors=True,
        )
    else:
        console_renderer = structlog.processors.JSONRenderer()
    
    processors.append(console_renderer)
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer() 
            if sys.stdout.isatty() 
            else structlog.processors.JSONRenderer(),
        )
    )
    root_logger.addHandler(console_handler)
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        )
        root_logger.addHandler(file_handler)
    
    for logger_name in ["uvicorn", "uvicorn.access", "sqlalchemy"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    return structlog.get_logger("agent_evolution_system")


def get_logger(name: str = None) -> Any:
    """获取结构化日志记录器"""
    return structlog.get_logger(name or "agent_evolution_system")


class StructuredLogger:
    """结构化日志记录器包装类"""
    
    def __init__(self, name: str = "agent_evolution_system"):
        self._logger = structlog.get_logger(name)
    
    def debug(self, event: str, **kwargs):
        self._logger.debug(event, **kwargs)
    
    def info(self, event: str, **kwargs):
        self._logger.info(event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        self._logger.warning(event, **kwargs)
    
    def error(self, event: str, **kwargs):
        self._logger.error(event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        self._logger.critical(event, **kwargs)
    
    def exception(self, event: str, **kwargs):
        self._logger.exception(event, **kwargs)
    
    def bind(self, **kwargs):
        self._logger = self._logger.bind(**kwargs)
        return self
