"""
LangChain AI Agent集成 - 核心架构
Agent永续自进化系统 - AI增强层
"""
from typing import Optional, List, Dict, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from langchain.agents import Agent, AgentExecutor, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain.tools import Tool, BaseTool
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from infrastructure.logging.logging_system import get_logger


class LLMProvider(str, Enum):
    """LLM提供者"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class AgentCapability(str, Enum):
    """Agent能力"""
    REASONING = "reasoning"
    PLANNING = "planning"
    EXECUTION = "execution"
    LEARNING = "learning"
    MEMORY = "memory"
    TOOL_USE = "tool_use"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    func: Callable
    args_schema: Optional[type] = None
    
    def to_langchain_tool(self) -> Tool:
        """转换为LangChain Tool"""
        return Tool(
            name=self.name,
            func=self.func,
            description=self.description
        )


@dataclass
class AIAgentConfig:
    """AI Agent配置"""
    name: str
    description: str
    llm_config: LLMConfig
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[ToolDefinition] = field(default_factory=list)
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    verbose: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "llm_config": self.llm_config.to_dict(),
            "capabilities": [c.value for c in self.capabilities],
            "max_iterations": self.max_iterations,
            "verbose": self.verbose
        }


@dataclass
class AgentResponse:
    """Agent响应"""
    agent_id: str
    input: str
    output: str
    reasoning: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)
    tokens_used: int = 0
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "input": self.input,
            "output": self.output,
            "reasoning": self.reasoning,
            "tools_used": self.tools_used,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class LangChainCallbackHandler(BaseCallbackHandler):
    """LangChain回调处理器"""
    
    def __init__(self):
        self.logger = get_logger("LangChainCallback")
        self.tool_calls: List[Dict[str, Any]] = []
        self.tokens_used: int = 0
        
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs
    ):
        self.tool_calls.append({
            "tool": serialized.get("name"),
            "input": input_str,
            "start_time": datetime.now(timezone.utc).isoformat()
        })
        self.logger.info(f"Tool started: {serialized.get('name')}")
    
    def on_tool_end(
        self,
        output: str,
        **kwargs
    ):
        if self.tool_calls:
            self.tool_calls[-1]["output"] = output
            self.tool_calls[-1]["end_time"] = datetime.now(timezone.utc).isoformat()
        self.logger.info(f"Tool ended: {output[:100]}")
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs
    ):
        self.logger.info(f"LLM started with {len(prompts)} prompts")
    
    def on_llm_end(
        self,
        response,
        **kwargs
    ):
        try:
            if hasattr(response, 'llm_output'):
                self.tokens_used = response.llm_output.get('token_usage', {}).get('total', 0)
        except:
            pass
        self.logger.info(f"LLM ended, tokens used: {self.tokens_used}")


class BaseAIAgent(ABC):
    """AI Agent基类"""
    
    def __init__(self, config: AIAgentConfig):
        self.config = config
        self.logger = get_logger(f"AIAgent_{config.name}")
        self.callback_handler = LangChainCallbackHandler()
        self._llm = None
        self._agent_executor = None
        
    @abstractmethod
    def initialize(self):
        """初始化Agent"""
        pass
    
    @abstractmethod
    async def run(self, input: str) -> AgentResponse:
        """运行Agent"""
        pass
    
    @abstractmethod
    async def plan(self, goal: str) -> List[str]:
        """规划步骤"""
        pass
    
    def get_available_tools(self) -> List[Tool]:
        """获取可用工具"""
        return [tool.to_langchain_tool() for tool in self.config.tools]
    
    def get_system_message(self) -> SystemMessage:
        """获取系统消息"""
        if self.config.system_prompt:
            return SystemMessage(content=self.config.system_prompt)
        
        base_prompt = f"""You are {self.config.name}, {self.config.description}.

Your capabilities:
{', '.join([c.value for c in self.config.capabilities])}

You have access to the following tools:
{chr(10).join([f"- {tool.name}: {tool.description}" for tool in self.config.tools])}

Always be helpful, accurate, and concise in your responses."""
        
        return SystemMessage(content=base_prompt)
