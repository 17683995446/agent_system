"""
应用服务层 - 进化应用服务
提供进化相关的业务逻辑编排
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from domain_logic.evolution_engine_core import EvolutionEngine, AgentGenome
from infrastructure.cache.cache_manager import CacheManager
from infrastructure.logging.logging_system import get_logger
from infrastructure.monitoring.monitoring_system import MonitoringSystem


class EvolutionPhase(str, Enum):
    """进化阶段"""
    INITIALIZATION = "initialization"
    SELECTION = "selection"
    CROSSOVER = "crossover"
    MUTATION = "mutation"
    EVALUATION = "evaluation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvolutionConfig:
    """进化配置"""
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_ratio: float = 0.1
    early_stopping_rounds: int = 10
    target_fitness: Optional[float] = 0.95


@dataclass
class EvolutionResult:
    """进化结果"""
    best_genome: AgentGenome
    final_population: List[AgentGenome]
    generations_used: int
    fitness_history: List[float]
    metrics: Dict[str, Any]
    success: bool
    final_fitness: float


@dataclass
class EvolutionProgress:
    """进化进度"""
    current_generation: int
    total_generations: int
    current_best_fitness: float
    avg_fitness: float
    phase: EvolutionPhase
    start_time: datetime
    elapsed_seconds: float


class EvolutionApplicationService:
    """进化应用服务"""
    
    def __init__(
        self,
        evolution_engine: Optional[EvolutionEngine] = None,
        cache_manager: Optional[CacheManager] = None,
        monitoring_system: Optional[MonitoringSystem] = None
    ):
        self.logger = get_logger("EvolutionApplicationService")
        self.evolution_engine = evolution_engine or EvolutionEngine()
        self.cache_manager = cache_manager or CacheManager(
            cache_type="lru", maxsize=500
        )
        self.monitoring_system = monitoring_system or MonitoringSystem()
        
        # 进化历史记录
        self._evolution_history: List[Dict[str, Any]] = []
        
        self.logger.info("EvolutionApplicationService initialized")
    
    def run_evolution(
        self,
        config: EvolutionConfig,
        fitness_function: Optional[Callable[[AgentGenome], float]] = None,
        callbacks: Optional[List[Callable[[EvolutionProgress], None]]] = None
    ) -> EvolutionResult:
        """运行完整进化过程"""
        
        self.logger.info(f"Starting evolution with config: {config}")
        
        start_time = datetime.now(timezone.utc)
        
        # 如果没有适应度函数，使用默认
        if fitness_function is None:
            def default_fitness(genome: AgentGenome) -> float:
                base_fitness = 0.5
                gene_sum = sum(genome.genes.values()) if genome.genes else 0
                return min(1.0, base_fitness + gene_sum * 0.05)
            fitness_function = default_fitness
        
        fitness_history = []
        best_fitness = 0.0
        best_genome = None
        generations_without_improvement = 0
        success = False
        
        # 重新初始化引擎
        self.evolution_engine.population_size = config.population_size
        self.evolution_engine._initialize_population()
        
        for generation in range(config.generations):
            # 更新进度
            if callbacks and generation % 10 == 0:
                progress = self._create_progress(
                    generation, config.generations, best_fitness, start_time, 
                    EvolutionPhase.EVALUATION if generation > 0 else EvolutionPhase.INITIALIZATION
                )
                for callback in callbacks:
                    try:
                        callback(progress)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
            
            # 评估适应度
            metrics = self.evolution_engine.evolve_generation(fitness_function)
            
            # 记录历史
            current_best = metrics.fitness_score
            fitness_history.append(current_best)
            
            # 更新最佳
            if current_best > best_fitness:
                best_fitness = current_best
                best_genome = self.evolution_engine.best_genome
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # 早期停止检查
            if config.target_fitness and current_best >= config.target_fitness:
                success = True
                self.logger.info(f"Target fitness reached: {current_best}")
                break
            
            if generations_without_improvement >= config.early_stopping_rounds:
                self.logger.info(f"Early stopping after {generations_without_improvement} generations")
                break
        
        # 完成进化
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # 创建结果
        result = EvolutionResult(
            best_genome=best_genome or self.evolution_engine.best_genome,
            final_population=self.evolution_engine.population,
            generations_used=generation + 1,
            fitness_history=fitness_history,
            metrics={
                "total_time": elapsed,
                "best_fitness": best_fitness,
                "avg_fitness": sum(fitness_history) / len(fitness_history) if fitness_history else 0
            },
            success=success or best_fitness >= (config.target_fitness or 0.9),
            final_fitness=best_fitness
        )
        
        # 记录历史
        self._evolution_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "population_size": config.population_size,
                "generations": config.generations,
                "mutation_rate": config.mutation_rate
            },
            "result": {
                "generations": result.generations_used,
                "best_fitness": best_fitness,
                "success": result.success
            }
        })
        
        self.logger.info(f"Evolution completed: {result.success}, generations: {result.generations_used}")
        return result
    
    def get_evolution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取进化历史"""
        return self._evolution_history[-limit:]
    
    def get_best_agent(self) -> Optional[AgentGenome]:
        """获取当前最佳Agent"""
        return self.evolution_engine.best_genome
    
    def get_population_stats(self) -> Dict[str, Any]:
        """获取种群统计"""
        population = self.evolution_engine.population
        
        if not population:
            return {"total": 0}
        
        fitnesses = [agent.fitness for agent in population if hasattr(agent, "fitness")]
        
        return {
            "total": len(population),
            "avg_fitness": sum(fitnesses) / len(fitnesses) if fitnesses else 0,
            "max_fitness": max(fitnesses) if fitnesses else 0,
            "min_fitness": min(fitnesses) if fitnesses else 0
        }
    
    def save_genome_to_cache(self, genome_id: str, genome: AgentGenome) -> None:
        """保存基因组到缓存"""
        cache_key = f"genome:{genome_id}"
        self.cache_manager.set(cache_key, genome)
        self.logger.debug(f"Saved genome to cache: {genome_id}")
    
    def load_genome_from_cache(self, genome_id: str) -> Optional[AgentGenome]:
        """从缓存加载基因组"""
        cache_key = f"genome:{genome_id}"
        return self.cache_manager.get(cache_key)
    
    def _create_progress(
        self,
        current_generation: int,
        total_generations: int,
        current_best_fitness: float,
        start_time: datetime,
        phase: EvolutionPhase
    ) -> EvolutionProgress:
        """创建进度对象"""
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        return EvolutionProgress(
            current_generation=current_generation,
            total_generations=total_generations,
            current_best_fitness=current_best_fitness,
            avg_fitness=self.get_population_stats().get("avg_fitness", 0),
            phase=phase,
            start_time=start_time,
            elapsed_seconds=elapsed
        )
