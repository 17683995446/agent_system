"""
领域逻辑层 - 进化引擎核心模块
实现Agent的自进化逻辑，包括学习、优化和适应机制
"""
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import random
import hashlib


class EvolutionState(str, Enum):
    """进化状态"""
    IDLE = "idle"
    LEARNING = "learning"
    OPTIMIZING = "optimizing"
    ADAPTING = "adapting"
    COMPLETED = "completed"
    FAILED = "failed"


class EvolutionStrategy(str, Enum):
    """进化策略"""
    GRADUAL = "gradual"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"


@dataclass
class EvolutionMetrics:
    """进化指标"""
    generation: int = 0
    fitness_score: float = 0.0
    diversity_score: float = 0.0
    stability_score: float = 0.0
    adaptation_rate: float = 0.0
    learning_progress: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AgentGenome:
    """Agent基因组"""
    genome_id: str
    genes: Dict[str, Any] = field(default_factory=dict)
    fitness: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mutate(self, mutation_rate: float = 0.1) -> "AgentGenome":
        """基因突变"""
        new_genes = self.genes.copy()
        
        for key in new_genes:
            if random.random() < mutation_rate:
                if isinstance(new_genes[key], (int, float)):
                    new_genes[key] *= random.uniform(0.8, 1.2)
                elif isinstance(new_genes[key], str):
                    new_genes[key] = new_genes[key][::-1]
        
        return AgentGenome(
            genome_id=self._generate_id(),
            genes=new_genes,
            generation=self.generation + 1,
            parent_ids=[self.genome_id],
            metadata={"mutation_time": datetime.now(timezone.utc).isoformat()}
        )
    
    def crossover(self, other: "AgentGenome") -> "AgentGenome":
        """基因交叉"""
        new_genes = {}
        
        for key in set(self.genes.keys()) | set(other.genes.keys()):
            if random.random() < 0.5:
                new_genes[key] = self.genes.get(key, other.genes.get(key))
            else:
                new_genes[key] = other.genes.get(key, self.genes.get(key))
        
        return AgentGenome(
            genome_id=self._generate_id(),
            genes=new_genes,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.genome_id, other.genome_id],
            metadata={"crossover_time": datetime.now(timezone.utc).isoformat()}
        )
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        content = f"{self.genes}_{time.time()}_{random.random()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


class EvolutionEngine:
    """进化引擎"""
    
    def __init__(
        self,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elite_ratio: float = 0.1,
        strategy: EvolutionStrategy = EvolutionStrategy.ADAPTIVE
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        self.strategy = strategy
        
        self.population: List[AgentGenome] = []
        self.best_genome: Optional[AgentGenome] = None
        self.generation = 0
        self.state = EvolutionState.IDLE
        self.metrics_history: List[EvolutionMetrics] = []
        
        self._initialize_population()
    
    def initialize_population(self, population_size: Optional[int] = None) -> List[AgentGenome]:
        """初始化种群 - 公共方法"""
        if population_size is not None:
            self.population_size = population_size
        self._initialize_population()
        return self.population
    
    def evolve(
        self,
        population_size: int = 50,
        generations: int = 10,
        mutation_rate: float = 0.1,
        fitness_func: Optional[Callable[[AgentGenome], float]] = None
    ) -> List[AgentGenome]:
        """
        执行进化过程 - 公共同步方法
        
        Args:
            population_size: 种群大小
            generations: 进化代数
            mutation_rate: 突变率
            fitness_func: 适应度评估函数（可选，默认使用随机适应度）
        
        Returns:
            最终种群列表
        """
        # 如果提供了fitness_func，使用它；否则使用默认的随机适应度
        if fitness_func is None:
            def default_fitness(genome: AgentGenome) -> float:
                """默认适应度函数 - 基于基因值的随机评估"""
                base_fitness = 0.5
                gene_factor = sum(genome.genes.values()) / len(genome.genes) if genome.genes else 0
                return min(1.0, base_fitness + gene_factor * 0.3 + random.uniform(-0.1, 0.1))
            fitness_func = default_fitness
        
        # 重新初始化种群（如果大小改变）
        if population_size != self.population_size:
            self.population_size = population_size
            self._initialize_population()
        
        # 更新突变率
        self.mutation_rate = mutation_rate
        
        # 执行多代进化
        for gen in range(generations):
            metrics = self.evolve_generation(fitness_func)
            
            # 可选：早期停止如果适应度足够高
            if metrics.fitness_score >= 0.95:
                break
        
        return self.population
    
    def _initialize_population(self):
        """初始化种群"""
        self.population = []
        
        for i in range(self.population_size):
            genome = AgentGenome(
                genome_id=f"gen_{self.generation}_{i}",
                genes={
                    "learning_rate": random.uniform(0.001, 0.1),
                    "memory_size": random.randint(100, 1000),
                    "attention_span": random.uniform(0.5, 1.0),
                    "creativity": random.uniform(0.0, 1.0),
                    "focus": random.uniform(0.5, 1.0),
                    "patience": random.uniform(0.3, 0.9),
                    "exploration": random.uniform(0.2, 0.8),
                }
            )
            self.population.append(genome)
    
    def evaluate_fitness(
        self,
        genome: AgentGenome,
        fitness_func: Callable[[AgentGenome], float]
    ) -> float:
        """评估适应度"""
        return fitness_func(genome)
    
    def select_parents(self) -> List[AgentGenome]:
        """选择父代"""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        
        elite_count = max(1, int(self.population_size * self.elite_ratio))
        elite = sorted_pop[:elite_count]
        
        tournament_size = 5
        parents = elite.copy()
        
        while len(parents) < 2:
            tournament = random.sample(self.population, min(tournament_size, len(self.population)))
            winner = max(tournament, key=lambda g: g.fitness)
            if winner not in parents:
                parents.append(winner)
        
        return parents[:2]
    
    def evolve_generation(
        self,
        fitness_func: Callable[[AgentGenome], float]
    ) -> EvolutionMetrics:
        """进化一代"""
        self.state = EvolutionState.LEARNING
        
        for genome in self.population:
            genome.fitness = self.evaluate_fitness(genome, fitness_func)
        
        self.population.sort(key=lambda g: g.fitness, reverse=True)
        
        self.best_genome = self.population[0]
        
        elite_count = max(1, int(self.population_size * self.elite_ratio))
        new_population = self.population[:elite_count].copy()
        
        while len(new_population) < self.population_size:
            parents = self.select_parents()
            
            if random.random() < self.crossover_rate:
                child = parents[0].crossover(parents[1])
            else:
                child = random.choice(parents).mutate(self.mutation_rate)
            
            if random.random() < self.mutation_rate:
                child = child.mutate(self.mutation_rate)
            
            new_population.append(child)
        
        self.population = new_population[:self.population_size]
        self.generation += 1
        
        metrics = self._calculate_metrics()
        self.metrics_history.append(metrics)
        
        self.state = EvolutionState.COMPLETED
        return metrics
    
    def _calculate_metrics(self) -> EvolutionMetrics:
        """计算进化指标"""
        fitness_scores = [g.fitness for g in self.population]
        
        avg_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
        diversity = self._calculate_diversity()
        stability = 1.0 - (max(fitness_scores) - min(fitness_scores)) if fitness_scores else 0
        
        adaptation_rate = 0.0
        if len(self.metrics_history) > 1:
            prev_avg = self.metrics_history[-1].fitness_score
            curr_avg = avg_fitness
            adaptation_rate = max(0, min(1, (curr_avg - prev_avg) / prev_avg)) if prev_avg > 0 else 0
        
        learning_progress = self.generation / 100.0
        
        return EvolutionMetrics(
            generation=self.generation,
            fitness_score=avg_fitness,
            diversity_score=diversity,
            stability_score=stability,
            adaptation_rate=adaptation_rate,
            learning_progress=min(1.0, learning_progress),
        )
    
    def _calculate_diversity(self) -> float:
        """计算种群多样性"""
        if not self.population:
            return 0.0
        
        total_gene_values = {}
        
        for genome in self.population:
            for key, value in genome.genes.items():
                if key not in total_gene_values:
                    total_gene_values[key] = []
                total_gene_values[key].append(value)
        
        diversity_scores = []
        
        for key, values in total_gene_values.items():
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                diversity_scores.append(variance)
        
        return sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0.0
    
    async def run_evolution(
        self,
        fitness_func: Callable[[AgentGenome], float],
        max_generations: int = 100,
        target_fitness: Optional[float] = None,
        convergence_threshold: float = 0.001
    ) -> Dict[str, Any]:
        """运行进化过程"""
        self.state = EvolutionState.ADAPTING
        
        start_time = time.time()
        best_fitness = 0.0
        generations_without_improvement = 0
        
        for gen in range(max_generations):
            metrics = self.evolve_generation(fitness_func)
            
            if metrics.fitness_score > best_fitness:
                best_fitness = metrics.fitness_score
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            if target_fitness and metrics.fitness_score >= target_fitness:
                break
            
            if generations_without_improvement > 20:
                self.state = EvolutionState.FAILED
                break
            
            if gen > 0 and gen % 10 == 0:
                await asyncio.sleep(0.01)
        
        elapsed = time.time() - start_time
        
        return {
            "success": self.state == EvolutionState.COMPLETED,
            "generations": self.generation,
            "best_fitness": best_fitness,
            "elapsed_time": elapsed,
            "final_metrics": self.metrics_history[-1].__dict__ if self.metrics_history else {},
            "best_genome": self.best_genome.genes if self.best_genome else {},
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取进化状态"""
        return {
            "state": self.state.value,
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": self.best_genome.fitness if self.best_genome else 0.0,
            "strategy": self.strategy.value,
            "metrics_history_size": len(self.metrics_history),
        }


evolution_engine = EvolutionEngine()
