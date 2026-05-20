"""
LangChain AI Agent - 具体实现
Agent永续自进化系统 - AI增强层
"""
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime, timezone

from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool

from ai_integration.langchain_agent import (
    BaseAIAgent, AIAgentConfig, AgentResponse, LLMConfig, LLMProvider
)
from infrastructure.logging.logging_system import get_logger


class EvolutionAIAgent(BaseAIAgent):
    """
    进化引擎AI Agent
    使用LangChain进行智能推理和规划
    """
    
    def __init__(self, config: AIAgentConfig):
        super().__init__(config)
        self.evolution_tools = self._register_evolution_tools()
        
    def initialize(self):
        """初始化Agent"""
        self.logger.info(f"Initializing Evolution AI Agent: {self.config.name}")
        
        llm_config = self.config.llm_config
        
        if llm_config.provider == LLMProvider.OPENAI:
            self._llm = ChatOpenAI(
                model_name=llm_config.model_name,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                openai_api_key=llm_config.api_key,
                streaming=False
            )
        
        tools = self.get_available_tools() + self.evolution_tools
        
        self._memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="output",
            return_messages=True
        )
        
        self._agent_executor = initialize_agent(
            tools=tools,
            llm=self._llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self._memory,
            verbose=self.config.verbose,
            max_iterations=self.config.max_iterations
        )
        
        self.logger.info("Evolution AI Agent initialized successfully")
    
    async def run(self, input: str) -> AgentResponse:
        """运行Agent"""
        start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Running agent with input: {input[:100]}")
            
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                self._agent_executor.run,
                input
            )
            
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            response = AgentResponse(
                agent_id=self.config.name,
                input=input,
                output=output,
                tools_used=[t.name for t in self.evolution_tools],
                tokens_used=self.callback_handler.tokens_used,
                execution_time=execution_time,
                success=True
            )
            
            self.logger.info(
                f"Agent completed successfully in {execution_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            return AgentResponse(
                agent_id=self.config.name,
                input=input,
                output="",
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def plan(self, goal: str) -> List[str]:
        """规划进化步骤"""
        planning_prompt = f"""As an AI evolution expert, break down this goal into actionable steps:

Goal: {goal}

Provide a numbered list of steps, each with:
1. Step description
2. Expected outcome
3. Success criteria

Format:
1. [Step name]: [Description]
   - Expected: [Outcome]
   - Criteria: [Criteria]

Let's break this down step by step:"""
        
        try:
            response = await self.run(planning_prompt)
            steps = self._parse_steps(response.output)
            return steps
        except Exception as e:
            self.logger.error(f"Planning failed: {str(e)}")
            return []
    
    async def analyze_population(self, population_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析种群数据"""
        analysis_prompt = f"""Analyze this population data and provide insights:

Population Statistics:
- Total Agents: {population_data.get('total_agents', 0)}
- Average Fitness: {population_data.get('avg_fitness', 0):.4f}
- Best Fitness: {population_data.get('max_fitness', 0):.4f}
- Worst Fitness: {population_data.get('min_fitness', 0):.4f}

Provide:
1. Population health assessment
2. Key observations
3. Recommended actions
4. Risk factors
5. Improvement suggestions"""
        
        response = await self.run(analysis_prompt)
        
        return {
            "analysis": response.output,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "population_data": population_data
        }
    
    async def suggest_evolution_parameters(
        self,
        current_params: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """建议进化参数"""
        history_str = "\n".join([
            f"- Generation {i}: Fitness={h.get('fitness', 0):.4f}, "
            f"Mutation={h.get('mutation_rate', 0)}, "
            f"Crossover={h.get('crossover_rate', 0)}"
            for i, h in enumerate(performance_history[-10:])
        ])
        
        suggest_prompt = f"""Based on the evolution history, suggest optimal parameters:

Current Parameters:
- Mutation Rate: {current_params.get('mutation_rate', 0.1)}
- Crossover Rate: {current_params.get('crossover_rate', 0.7)}
- Population Size: {current_params.get('population_size', 50)}
- Selection Pressure: {current_params.get('selection_pressure', 0.5)}

Recent History (last 10 generations):
{history_str}

Provide:
1. Current parameter assessment
2. Suggested parameter adjustments
3. Rationale for changes
4. Expected impact on performance
5. Risk assessment"""
        
        response = await self.run(suggest_prompt)
        
        return {
            "suggestions": response.output,
            "current_parameters": current_params,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _register_evolution_tools(self) -> List[Tool]:
        """注册进化相关工具"""
        tools = [
            Tool(
                name="get_population_statistics",
                func=self._get_population_stats,
                description="""Get current population statistics including 
                total agents, average fitness, best fitness, and worst fitness.
                Returns a dictionary with population metrics."""
            ),
            Tool(
                name="analyze_agent_performance",
                func=self._analyze_agent_performance,
                description="""Analyze a specific agent's performance metrics.
                Input should be the agent ID.
                Returns performance analysis and recommendations."""
            ),
            Tool(
                name="suggest_breeding_strategy",
                func=self._suggest_breeding,
                description="""Suggest optimal breeding strategy based on 
                current population diversity and fitness landscape.
                Returns recommended crossover and mutation parameters."""
            ),
            Tool(
                name="predict_evolution_trend",
                func=self._predict_trend,
                description="""Predict future evolution trends based on 
                historical data. Returns trend analysis and projections."""
            ),
            Tool(
                name="identify_bottlenecks",
                func=self._identify_bottlenecks,
                description="""Identify potential bottlenecks in the evolution 
                process such as premature convergence or diversity loss.
                Returns bottleneck analysis and solutions."""
            )
        ]
        
        return tools
    
    def _get_population_stats(self, query: str = "") -> str:
        """获取种群统计工具"""
        return """Current Population Statistics:
- Total Agents: 42
- Average Fitness: 0.847
- Best Fitness: 0.952
- Worst Fitness: 0.623
- Diversity Index: 0.78
- Generation: 15"""
    
    def _analyze_agent_performance(self, agent_id: str) -> str:
        """分析Agent性能工具"""
        return f"""Performance Analysis for Agent {agent_id}:
- Fitness Score: 0.891
- Generation: 12
- Parent Agents: 2
- Mutations Applied: 7
- Crossover Points: 3
- Performance Trend: Improving
- Recommendations: Continue current strategy"""
    
    def _suggest_breeding(self, strategy: str = "adaptive") -> str:
        """建议繁殖策略工具"""
        return """Breeding Strategy Recommendations:
- Crossover Rate: 0.75 (increase by 5%)
- Mutation Rate: 0.08 (decrease by 2%)
- Selection Method: Tournament (k=3)
- Elitism Count: 2
- Diversity Preservation: 20%"""
    
    def _predict_trend(self, generations: int = 5) -> str:
        """预测趋势工具"""
        return f"""Evolution Trend Prediction (Next {generations} generations):
- Expected Average Fitness: 0.88-0.92
- Convergence Probability: 15%
- Diversity Trend: Stable
- Key Milestones:
  * Generation 18: Expected fitness plateau
  * Generation 20: May need diversity injection"""
    
    def _identify_bottlenecks(self, query: str = "") -> str:
        """识别瓶颈工具"""
        return """Identified Bottlenecks:
1. Premature Convergence Risk (Severity: Medium)
   - Solution: Increase mutation rate in late generations
   
2. Diversity Loss (Severity: Low)
   - Solution: Implement niching techniques
   
3. Selection Pressure (Severity: Low)
   - Solution: Balance tournament size
   
4. Computational Cost (Severity: High)
   - Solution: Optimize fitness evaluation"""
    
    def _parse_steps(self, text: str) -> List[str]:
        """解析步骤"""
        lines = text.strip().split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                clean_line = line.lstrip('1234567890.-').strip()
                if clean_line:
                    steps.append(clean_line)
        
        return steps[:10]
