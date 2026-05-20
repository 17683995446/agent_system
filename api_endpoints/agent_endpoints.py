"""
API端点层 - Agent管理API
提供Agent的完整生命周期管理
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from enum import Enum
import random

from domain_logic.evolution_engine_core import (
    EvolutionEngine, AgentGenome
)
from application_service.evolution_application_service import (
    EvolutionApplicationService, EvolutionConfig
)
from infrastructure.logging.logging_system import get_logger


class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentResponse:
    """Agent响应对象"""
    agent_id: str
    status: AgentStatus
    genome: Optional[Dict[str, Any]] = None
    fitness: Optional[float] = None
    created_at: str = ""
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentEndpoints:
    """Agent管理API端点"""

    def __init__(self, evolution_service: Optional[EvolutionApplicationService] = None):
        self.logger = get_logger("AgentEndpoints")
        self.evolution_service = evolution_service or EvolutionApplicationService()
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.logger.info("AgentEndpoints initialized")

    async def create_agent(self, config: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """创建新Agent"""
        from domain_logic.evolution_engine_core import AgentGenome
        import uuid
        
        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        genome = AgentGenome(
            genome_id=agent_id,
            genes={
                "learning_rate": random.uniform(0.01, 0.1),
                "memory_size": random.randint(100, 1000)
            }
        )
        self.agents[agent_id] = {
            "agent_id": agent_id,
            "status": AgentStatus.IDLE,
            "genome": genome,
            "fitness": 0.0,
            "created_at": now,
            "updated_at": now,
            "metadata": {}
        }
        
        self.logger.info(f"Agent created: {agent_id}")
        
        return AgentResponse(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            genome=genome.__dict__,
            fitness=0.0,
            created_at=now,
            updated_at=now,
            metadata={}
        )

    async def get_agent(self, agent_id: str) -> Optional[AgentResponse]:
        """获取指定Agent"""
        if agent_id not in self.agents:
            return None
        
        agent_data = self.agents[agent_id]
        return AgentResponse(
            agent_id=agent_data["agent_id"],
            status=agent_data["status"],
            genome=agent_data["genome"].__dict__,
            fitness=agent_data["fitness"],
            created_at=agent_data["created_at"],
            updated_at=agent_data["updated_at"],
            metadata=agent_data["metadata"]
        )

    async def list_agents(self, status: Optional[AgentStatus] = None, limit: int = 100) -> List[AgentResponse]:
        """列出所有Agent"""
        agents = []
        
        for agent_data in list(self.agents.values())[:limit]:
            if status is None or agent_data["status"] == status:
                agents.append(AgentResponse(
                    agent_id=agent_data["agent_id"],
                    status=agent_data["status"],
                    genome=agent_data["genome"].__dict__,
                    fitness=agent_data["fitness"],
                    created_at=agent_data["created_at"],
                    updated_at=agent_data["updated_at"],
                    metadata=agent_data["metadata"]
                ))
        
        return agents

    async def update_agent_status(self, agent_id: str, new_status: AgentStatus) -> Optional[AgentResponse]:
        """更新Agent状态"""
        if agent_id not in self.agents:
            return None
        
        self.agents[agent_id]["status"] = new_status
        self.agents[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        self.logger.info(f"Agent {agent_id} status updated to {new_status}")
        
        agent_data = self.agents[agent_id]
        return AgentResponse(
            agent_id=agent_data["agent_id"],
            status=agent_data["status"],
            genome=agent_data["genome"].__dict__,
            fitness=agent_data["fitness"],
            created_at=agent_data["created_at"],
            updated_at=agent_data["updated_at"],
            metadata=agent_data["metadata"]
        )

    async def delete_agent(self, agent_id: str) -> bool:
        """删除Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Agent deleted: {agent_id}")
            return True
        return False

    async def start_evolution(self, config: Optional[EvolutionConfig] = None) -> Any:
        """启动进化"""
        from application_service.evolution_application_service import EvolutionResult
        
        evolution_config = config or EvolutionConfig()
        
        result = self.evolution_service.run_evolution(evolution_config)
        
        self.logger.info(f"Evolution completed: {result.success}")
        
        class SimpleEvolutionResult:
            def __init__(self, result):
                self.success = result.success
                self.generations_completed = result.generations_used
                self.best_fitness = result.final_fitness
                self.message = f"Evolution completed with fitness {result.final_fitness:.4f}"
        
        return SimpleEvolutionResult(result)

    async def get_best_agent(self) -> Optional[AgentResponse]:
        """获取最佳Agent"""
        if not self.agents:
            return None
        
        best_agent_id = max(self.agents.keys(), 
                          key=lambda aid: self.agents[aid]["fitness"])
        
        return await self.get_agent(best_agent_id)

    async def get_population_stats(self) -> Dict[str, Any]:
        """获取种群统计"""
        population_stats = self.evolution_service.get_population_stats()
        
        return {
            "total_agents": len(self.agents),
            "avg_fitness": population_stats.get("avg_fitness", 0.0),
            "best_fitness": population_stats.get("best_fitness", 0.0),
            "population_size": population_stats.get("population_size", 0)
        }
