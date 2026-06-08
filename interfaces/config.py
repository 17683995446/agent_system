"""
配置模块抽象接口定义

提供环境配置管理的标准接口。
支持多环境配置加载、切换和管理。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class Environment(Enum):
    """运行环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigManagerInterface(ABC):
    """配置管理器接口

    提供多环境配置的加载、切换和管理功能。
    支持从文件、环境变量等多种来源加载配置。
    """

    @abstractmethod
    def get_config(self, env: Optional[Environment] = None) -> Dict[str, Any]:
        """获取配置

        Args:
            env: 环境类型，None表示当前环境

        Returns:
            配置字典，包含所有配置项
        """
        pass

    @abstractmethod
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前环境配置

        Returns:
            当前环境的完整配置
        """
        pass

    @abstractmethod
    def set_environment(self, env: Environment) -> None:
        """设置当前环境

        Args:
            env: 环境类型
        """
        pass

    @abstractmethod
    def get_environment(self) -> Environment:
        """获取当前环境

        Returns:
            当前环境类型
        """
        pass

    @abstractmethod
    def is_development(self) -> bool:
        """是否开发环境

        Returns:
            是否是开发环境
        """
        pass

    @abstractmethod
    def is_testing(self) -> bool:
        """是否测试环境

        Returns:
            是否是测试环境
        """
        pass

    @abstractmethod
    def is_staging(self) -> bool:
        """是否预发布环境

        Returns:
            是否是预发布环境
        """
        pass

    @abstractmethod
    def is_production(self) -> bool:
        """是否生产环境

        Returns:
            是否是生产环境
        """
        pass

    @abstractmethod
    def reload_config(self) -> None:
        """重新加载配置

        从配置文件或环境变量重新加载配置。
        """
        pass

    @abstractmethod
    def save_config(self, env: Environment, config: Dict[str, Any]) -> bool:
        """保存配置到文件

        Args:
            env: 环境类型
            config: 配置字典

        Returns:
            保存是否成功
        """
        pass
