"""
AI Agent API端点
Agent永续自进化系统 - AI增强层
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from ai_integration.evolution_agent import EvolutionAIAgent, AIAgentConfig, LLMConfig, LLMProvider, AgentCapability
from auth.dependencies import get_current_user

router = APIRouter()


class CreateAIAgentRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    model_name: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=100, le=4000)
    capabilities: List[str] = Field(default=["reasoning", "planning"])
    max_iterations: int = Field(default=10, ge=1, le=100)


class RunAgentRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None


class PlanRequest(BaseModel):
    goal: str = Field(..., min_length=10, max_length=5000)


class AnalyzePopulationRequest(BaseModel):
    population_data: Dict[str, Any]


class SuggestParamsRequest(BaseModel):
    current_params: Dict[str, Any]
    performance_history: List[Dict[str, Any]]


class AIAgentResponse(BaseModel):
    agent_id: str
    name: str
    description: str
    status: str
    capabilities: List[str]
    created_at: str


class AgentRunResponse(BaseModel):
    agent_id: str
    input: str
    output: str
    reasoning: Optional[str] = None
    tools_used: List[str]
    tokens_used: int
    execution_time: float
    success: bool
    error: Optional[str] = None


_ai_agents: Dict[str, EvolutionAIAgent] = {}


@router.post("/agents", response_model=AIAgentResponse)
async def create_ai_agent(
    request: CreateAIAgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """创建AI Agent"""
    try:
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        capabilities = []
        for cap in request.capabilities:
            try:
                capabilities.append(AgentCapability(cap))
            except ValueError:
                pass
        
        config = AIAgentConfig(
            name=request.name,
            description=request.description,
            llm_config=llm_config,
            capabilities=capabilities,
            max_iterations=request.max_iterations
        )
        
        agent = EvolutionAIAgent(config)
        agent.initialize()
        
        agent_id = f"ai_agent_{len(_ai_agents) + 1}"
        _ai_agents[agent_id] = agent
        
        return AIAgentResponse(
            agent_id=agent_id,
            name=agent.config.name,
            description=agent.config.description,
            status="active",
            capabilities=[c.value for c in agent.config.capabilities],
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI agent: {str(e)}"
        )


@router.get("/agents")
async def list_ai_agents(current_user: dict = Depends(get_current_user)):
    """列出AI Agents"""
    agents = []
    for agent_id, agent in _ai_agents.items():
        agents.append({
            "agent_id": agent_id,
            "name": agent.config.name,
            "description": agent.config.description,
            "status": "active",
            "capabilities": [c.value for c in agent.config.capabilities]
        })
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/{agent_id}")
async def get_ai_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取AI Agent详情"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    agent = _ai_agents[agent_id]
    
    return {
        "agent_id": agent_id,
        "name": agent.config.name,
        "description": agent.config.description,
        "status": "active",
        "capabilities": [c.value for c in agent.config.capabilities],
        "llm_config": agent.config.llm_config.to_dict()
    }


@router.post("/agents/{agent_id}/run", response_model=AgentRunResponse)
async def run_ai_agent(
    agent_id: str,
    request: RunAgentRequest,
    current_user: dict = Depends(get_current_user)
):
    """运行AI Agent"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    try:
        agent = _ai_agents[agent_id]
        response = await agent.run(request.input)
        
        return AgentRunResponse(
            agent_id=agent_id,
            input=response.input,
            output=response.output,
            tools_used=response.tools_used,
            tokens_used=response.tokens_used,
            execution_time=response.execution_time,
            success=response.success,
            error=response.error
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.post("/agents/{agent_id}/plan")
async def plan_with_ai_agent(
    agent_id: str,
    request: PlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """使用AI Agent进行规划"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    try:
        agent = _ai_agents[agent_id]
        steps = await agent.plan(request.goal)
        
        return {
            "agent_id": agent_id,
            "goal": request.goal,
            "steps": steps,
            "total_steps": len(steps)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Planning failed: {str(e)}"
        )


@router.post("/agents/{agent_id}/analyze-population")
async def analyze_population(
    agent_id: str,
    request: AnalyzePopulationRequest,
    current_user: dict = Depends(get_current_user)
):
    """使用AI Agent分析种群"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    try:
        agent = _ai_agents[agent_id]
        analysis = await agent.analyze_population(request.population_data)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Population analysis failed: {str(e)}"
        )


@router.post("/agents/{agent_id}/suggest-params")
async def suggest_evolution_params(
    agent_id: str,
    request: SuggestParamsRequest,
    current_user: dict = Depends(get_current_user)
):
    """使用AI Agent建议进化参数"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    try:
        agent = _ai_agents[agent_id]
        suggestions = await agent.suggest_evolution_parameters(
            request.current_params,
            request.performance_history
        )
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parameter suggestion failed: {str(e)}"
        )


@router.delete("/agents/{agent_id}")
async def delete_ai_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除AI Agent"""
    if agent_id not in _ai_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI agent {agent_id} not found"
        )
    
    del _ai_agents[agent_id]
    
    return {"message": "AI agent deleted successfully", "agent_id": agent_id}


from datetime import datetime, timezone
