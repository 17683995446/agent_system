"""
AI驱动的自动进化引擎
Phase 8.2: AI驱动的自动进化引擎
"""

from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timezone
import uuid
import json
import asyncio
from collections import defaultdict


class EvolutionStrategy(Enum):
    """进化策略"""
    GENETIC_ALGORITHM = auto()
    NEURAL_EVOLUTION = auto()
    REINFORCEMENT_LEARNING = auto()
    BAYESIAN_OPTIMIZATION = auto()
    SWARM_INTELLIGENCE = auto()
    HILL_CLIMBING = auto()
    SIMULATED_ANNEALING = auto()


class EvolutionPhase(Enum):
    """进化阶段"""
    INITIALIZATION = auto()
    SELECTION = auto()
    CROSSOVER = auto()
    MUTATION = auto()
    EVALUATION = auto()
    SURVIVAL = auto()
    OPTIMIZATION = auto()
    TERMINATION = auto()


class OptimizationType(Enum):
    """优化类型"""
    MAXIMIZE_FITNESS = auto()
    MINIMIZE_LOSS = auto()
    MAXIMIZE_DIVERSITY = auto()
    MINIMIZE_COMPLEXITY = auto()
    MULTI_OBJECTIVE = auto()


@dataclass
class EvolutionConfig:
    """进化配置"""
    population_size: int = 100
    max_generations: int = 1000
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elitism_rate: float = 0.05
    selection_pressure: float = 1.5
    mutation_step_size: float = 0.1
    strategy: EvolutionStrategy = EvolutionStrategy.GENETIC_ALGORITHM
    optimization_type: OptimizationType = OptimizationType.MAXIMIZE_FITNESS
    convergence_threshold: float = 0.001
    stagnation_threshold: int = 50
    parallel_evaluation: bool = True
    enable_novelty_search: bool = False
    novelty_weight: float = 0.3
    enable_adaptive_parameters: bool = True


@dataclass
class Genome:
    """基因组"""
    genome_id: str
    fitness: float = 0.0
    genes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __hash__(self):
        return hash(self.genome_id)
    
    def clone(self) -> 'Genome':
        """克隆基因组"""
        return Genome(
            genome_id=str(uuid.uuid4()),
            fitness=self.fitness,
            genes=self.genes.copy(),
            metadata=self.metadata.copy(),
            generation=self.generation
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "fitness": self.fitness,
            "genes": self.genes,
            "generation": self.generation,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PopulationStats:
    """种群统计"""
    generation: int
    population_size: int
    avg_fitness: float
    best_fitness: float
    worst_fitness: float
    fitness_std: float
    diversity_score: float
    best_genome: Optional[Genome] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "population_size": self.population_size,
            "avg_fitness": self.avg_fitness,
            "best_fitness": self.best_fitness,
            "worst_fitness": self.worst_fitness,
            "fitness_std": self.fitness_std,
            "diversity_score": self.diversity_score,
            "best_genome": self.best_genome.to_dict() if self.best_genome else None,
            "timestamp": self.timestamp.isoformat()
        }


class BaseEvolutionaryOperator(ABC):
    """进化操作基类"""
    
    @abstractmethod
    async def mutate(self, genome: Genome) -> Genome:
        """变异操作"""
        pass
    
    @abstractmethod
    async def crossover(self, parent1: Genome, parent2: Genome) -> List[Genome]:
        """交叉操作"""
        pass
    
    @abstractmethod
    async def select(self, population: List[Genome], num_parents: int) -> List[Genome]:
        """选择操作"""
        pass


class EvolutionaryOperator(BaseEvolutionaryOperator):
    """进化操作实现"""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.rng = __import__('random')
        
    async def mutate(self, genome: Genome) -> Genome:
        """变异操作"""
        mutated = genome.clone()
        
        for gene_key in mutated.genes:
            if self.rng.random() < self.config.mutation_rate:
                original_value = mutated.genes[gene_key]
                
                if isinstance(original_value, (int, float)):
                    mutation = self.rng.gauss(0, self.config.mutation_step_size)
                    mutated.genes[gene_key] = original_value + mutation
                elif isinstance(original_value, bool):
                    mutated.genes[gene_key] = not original_value
                elif isinstance(original_value, str):
                    mutated.genes[gene_key] = self._mutate_string(original_value)
        
        return mutated
    
    async def crossover(self, parent1: Genome, parent2: Genome) -> List[Genome]:
        """交叉操作"""
        if self.rng.random() >= self.config.crossover_rate:
            return [parent1.clone(), parent2.clone()]
        
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        all_genes = set(parent1.genes.keys()) | set(parent2.genes.keys())
        
        for gene_key in all_genes:
            if self.rng.random() < 0.5:
                if gene_key in parent2.genes:
                    child1.genes[gene_key] = parent2.genes[gene_key]
            else:
                if gene_key in parent1.genes:
                    child2.genes[gene_key] = parent1.genes[gene_key]
        
        return [child1, child2]
    
    async def select(self, population: List[Genome], num_parents: int) -> List[Genome]:
        """锦标赛选择"""
        selected = []
        tournament_size = 3
        
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        
        while len(selected) < num_parents:
            tournament = self.rng.sample(population, tournament_size)
            tournament.sort(key=lambda x: x.fitness, reverse=True)
            winner = tournament[0]
            selected.append(winner.clone())
        
        return selected
    
    def _mutate_string(self, s: str) -> str:
        """字符串变异"""
        chars = list(s)
        if len(chars) > 0:
            idx = self.rng.randint(0, len(chars) - 1)
            chars[idx] = chr(self.rng.randint(32, 126))
        return ''.join(chars)


class AutoEvolutionEngine:
    """AI驱动的自动进化引擎"""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.operator = EvolutionaryOperator(config)
        self.population: List[Genome] = []
        self.history: List[PopulationStats] = []
        self.generation = 0
        self.best_fitness_history: List[float] = []
        self.stagnation_counter = 0
        self.is_running = False
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调"""
        self._callbacks[event].append(callback)
    
    async def _emit_event(self, event: str, **kwargs):
        """触发事件"""
        for callback in self._callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(**kwargs)
                else:
                    callback(**kwargs)
            except Exception as e:
                print(f"Callback error: {e}")
    
    async def initialize_population(self, seed_genomes: Optional[List[Genome]] = None) -> int:
        """初始化种群"""
        self.generation = 0
        self.population = []
        
        if seed_genomes:
            self.population = seed_genomes[:self.config.population_size]
        
        while len(self.population) < self.config.population_size:
            genome = await self._create_random_genome()
            self.population.append(genome)
        
        await self._emit_event("population_initialized", population=self.population)
        return len(self.population)
    
    async def evolve(self, fitness_function: Callable[[Genome], float], 
                    num_generations: Optional[int] = None) -> Genome:
        """执行进化"""
        self.is_running = True
        max_gens = num_generations or self.config.max_generations
        
        if not self.population:
            await self.initialize_population()
        
        await self._evaluate_fitness(fitness_function)
        
        while self.generation < max_gens and self.is_running:
            await self._emit_event("phase_start", phase=EvolutionPhase.SELECTION)
            
            parents = await self.operator.select(
                self.population, 
                int(self.config.population_size * 0.5)
            )
            
            await self._emit_event("phase_start", phase=EvolutionPhase.CROSSOVER)
            offspring = []
            for i in range(0, len(parents), 2):
                if i + 1 < len(parents):
                    children = await self.operator.crossover(parents[i], parents[i + 1])
                    offspring.extend(children)
            
            await self._emit_event("phase_start", phase=EvolutionPhase.MUTATION)
            mutated_offspring = []
            for child in offspring:
                mutated = await self.operator.mutate(child)
                mutated_offspring.append(mutated)
            
            combined = self.population + mutated_offspring
            
            await self._emit_event("phase_start", phase=EvolutionPhase.EVALUATION)
            for genome in mutated_offspring:
                genome.fitness = fitness_function(genome)
            
            await self._emit_event("phase_start", phase=EvolutionPhase.SURVIVAL)
            sorted_combined = sorted(combined, key=lambda x: x.fitness, reverse=True)
            elitism_count = int(self.config.elitism_rate * self.config.population_size)
            elites = sorted_combined[:elitism_count]
            rest = sorted_combined[elitism_count:][:self.config.population_size - elitism_count]
            
            self.population = elites + rest
            
            self.generation += 1
            stats = await self._compute_population_stats()
            self.history.append(stats)
            self.best_fitness_history.append(stats.best_fitness)
            
            await self._check_convergence()
            await self._emit_event("generation_complete", stats=stats, generation=self.generation)
            
            if self.config.enable_adaptive_parameters:
                await self._adapt_parameters(stats)
        
        self.is_running = False
        return self._get_best_genome()
    
    async def stop_evolution(self):
        """停止进化"""
        self.is_running = False
        await self._emit_event("evolution_stopped", generation=self.generation)
    
    def get_statistics(self) -> PopulationStats:
        """获取当前统计"""
        if self.history:
            return self.history[-1]
        return PopulationStats(
            generation=0,
            population_size=0,
            avg_fitness=0,
            best_fitness=0,
            worst_fitness=0,
            fitness_std=0,
            diversity_score=0
        )
    
    def get_history(self) -> List[PopulationStats]:
        """获取历史"""
        return self.history
    
    async def _create_random_genome(self) -> Genome:
        """创建随机基因组"""
        import random
        genes = {
            "learning_rate": random.uniform(0.0001, 0.1),
            "batch_size": random.choice([16, 32, 64, 128]),
            "dropout_rate": random.uniform(0, 0.5),
            "hidden_units": random.randint(32, 512),
            "activation": random.choice(["relu", "tanh", "sigmoid", "gelu"])
        }
        
        return Genome(
            genome_id=str(uuid.uuid4()),
            genes=genes,
            generation=self.generation
        )
    
    async def _evaluate_fitness(self, fitness_function: Callable[[Genome], float]):
        """评估适应度"""
        for genome in self.population:
            if genome.fitness == 0:
                genome.fitness = fitness_function(genome)
    
    async def _compute_population_stats(self) -> PopulationStats:
        """计算种群统计"""
        import math
        
        fitnesses = [g.fitness for g in self.population]
        avg_fitness = sum(fitnesses) / len(fitnesses)
        best_fitness = max(fitnesses)
        worst_fitness = min(fitnesses)
        
        fitness_std = math.sqrt(sum((f - avg_fitness) ** 2 for f in fitnesses) / len(fitnesses))
        diversity_score = self._compute_diversity(self.population)
        
        best_genome = max(self.population, key=lambda x: x.fitness)
        
        return PopulationStats(
            generation=self.generation,
            population_size=len(self.population),
            avg_fitness=avg_fitness,
            best_fitness=best_fitness,
            worst_fitness=worst_fitness,
            fitness_std=fitness_std,
            diversity_score=diversity_score,
            best_genome=best_genome
        )
    
    def _compute_diversity(self, population: List[Genome]) -> float:
        """计算多样性"""
        if len(population) < 2:
            return 0
        
        diversity = 0
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                distance = self._genetic_distance(population[i], population[j])
                diversity += distance
        
        num_pairs = len(population) * (len(population) - 1) / 2
        return diversity / num_pairs if num_pairs > 0 else 0
    
    def _genetic_distance(self, genome1: Genome, genome2: Genome) -> float:
        """计算遗传距离"""
        import math
        distance = 0
        
        all_genes = set(genome1.genes.keys()) | set(genome2.genes.keys())
        
        for gene_key in all_genes:
            v1 = genome1.genes.get(gene_key)
            v2 = genome2.genes.get(gene_key)
            
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                distance += (v1 - v2) ** 2
            elif v1 != v2:
                distance += 1
        
        return math.sqrt(distance)
    
    async def _check_convergence(self):
        """检查收敛"""
        if len(self.best_fitness_history) < 2:
            return
        
        improvement = self.best_fitness_history[-1] - self.best_fitness_history[-2]
        
        if abs(improvement) < self.config.convergence_threshold:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0
        
        if self.stagnation_counter >= self.config.stagnation_threshold:
            print(f"Convergence reached after {self.generation} generations")
    
    async def _adapt_parameters(self, stats: PopulationStats):
        """自适应参数"""
        if stats.diversity_score < 0.2:
            self.config.mutation_rate = min(0.3, self.config.mutation_rate * 1.1)
        elif stats.diversity_score > 0.8:
            self.config.mutation_rate = max(0.01, self.config.mutation_rate * 0.9)
        
        if self.stagnation_counter > 10:
            self.config.mutation_rate = min(0.2, self.config.mutation_rate * 1.2)
    
    def _get_best_genome(self) -> Genome:
        """获取最佳基因组"""
        return max(self.population, key=lambda x: x.fitness)
