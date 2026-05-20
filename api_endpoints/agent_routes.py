"""
FastAPI路由 - Agent管理
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from api_endpoints.agent_endpoints import AgentEndpoints, AgentStatus

router = APIRouter()

class CreateAgentRequest(BaseModel):
    config: Optional[dict] = None

class UpdateStatusRequest(BaseModel):
    status: AgentStatus

class EvolutionConfigRequest(BaseModel):
    max_generations: int = 10
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7

@router.get("/")
async def list_agents(
    status: Optional[AgentStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000)
) -> dict:
    """List all agents"""
    endpoints = AgentEndpoints()
    agents = await endpoints.list_agents(status=status, limit=limit)
    return {"total": len(agents), "agents": [a.__dict__ for a in agents]}

@router.post("/")
async def create_agent(request: CreateAgentRequest = None) -> dict:
    """Create a new agent"""
    endpoints = AgentEndpoints()
    config = request.config if request else None
    agent = await endpoints.create_agent(config=config)
    return agent.__dict__

@router.get("/stats/population")
async def get_population_stats() -> dict:
    """Get population statistics"""
    endpoints = AgentEndpoints()
    return await endpoints.get_population_stats()

@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    """Get agent by ID"""
    endpoints = AgentEndpoints()
    agent = await endpoints.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent.__dict__

@router.patch("/{agent_id}/status")
async def update_status(agent_id: str, request: UpdateStatusRequest) -> dict:
    """Update agent status"""
    endpoints = AgentEndpoints()
    agent = await endpoints.update_agent_status(agent_id, request.status)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent.__dict__

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict:
    """Delete agent"""
    endpoints = AgentEndpoints()
    success = await endpoints.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "deleted": success}

@router.post("/evolution/start")
async def start_evolution(request: EvolutionConfigRequest = None) -> dict:
    """Start evolution process"""
    from application_service.evolution_application_service import EvolutionConfig
    
    endpoints = AgentEndpoints()
    config = None
    if request:
        config = EvolutionConfig(
            population_size=request.population_size,
            generations=request.max_generations,
            mutation_rate=request.mutation_rate,
            crossover_rate=request.crossover_rate
        )
    
    result = await endpoints.start_evolution(config=config)
    return {
        "success": result.success,
        "generations": result.generations_completed,
        "fitness": result.best_fitness,
        "message": result.message
    }

@router.get("/best")
async def get_best_agent() -> dict:
    """Get best agent"""
    endpoints = AgentEndpoints()
    agent = await endpoints.get_best_agent()
    if not agent:
        raise HTTPException(status_code=404, detail="No best agent found")
    return agent.__dict__
