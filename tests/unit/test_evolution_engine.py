"""
测试 - 进化引擎核心模块单元测试
"""
import pytest
from domain_logic.evolution_engine_core import (
    EvolutionEngine,
    AgentGenome,
    EvolutionState,
    EvolutionStrategy,
)


class TestAgentGenome:
    """测试Agent基因组"""
    
    def test_create_genome(self):
        """测试创建基因组"""
        genome = AgentGenome(
            genome_id="test_genome",
            genes={"learning_rate": 0.1, "memory_size": 100}
        )
        
        assert genome.genome_id == "test_genome"
        assert genome.genes["learning_rate"] == 0.1
        assert genome.generation == 0
        assert genome.fitness == 0.0
    
    def test_genome_mutation(self):
        """测试基因突变"""
        original = AgentGenome(
            genome_id="original",
            genes={"learning_rate": 0.1, "count": 5}
        )
        
        mutated = original.mutate(mutation_rate=1.0)
        
        assert mutated.generation == 1
        assert mutated.parent_ids == ["original"]
        assert mutated.genome_id != "original"
    
    def test_genome_crossover(self):
        """测试基因交叉"""
        parent1 = AgentGenome(
            genome_id="parent1",
            genes={"gene_a": 1, "gene_b": 2}
        )
        parent2 = AgentGenome(
            genome_id="parent2",
            genes={"gene_a": 10, "gene_c": 30}
        )
        
        child = parent1.crossover(parent2)
        
        assert child.generation == 1
        assert len(child.parent_ids) == 2
        assert "gene_a" in child.genes
        assert "gene_b" in child.genes or "gene_c" in child.genes


class TestEvolutionEngine:
    """测试进化引擎"""
    
    def test_create_evolution_engine(self):
        """测试创建进化引擎"""
        engine = EvolutionEngine(
            population_size=20,
            mutation_rate=0.1,
            strategy=EvolutionStrategy.GRADUAL
        )
        
        assert engine.population_size == 20
        assert engine.mutation_rate == 0.1
        assert engine.strategy == EvolutionStrategy.GRADUAL
        assert len(engine.population) == 20
        assert engine.state == EvolutionState.IDLE
    
    def test_evolution_engine_default_values(self):
        """测试进化引擎默认值"""
        engine = EvolutionEngine()
        
        assert engine.population_size == 50
        assert engine.mutation_rate == 0.1
        assert engine.crossover_rate == 0.7
        assert engine.elite_ratio == 0.1
        assert engine.generation == 0
    
    def test_evolve_generation(self):
        """测试进化一代"""
        engine = EvolutionEngine(population_size=10)
        
        def fitness_function(genome):
            return sum(genome.genes.values()) if genome.genes else 0
        
        metrics = engine.evolve_generation(fitness_function)
        
        assert engine.generation == 1
        assert engine.state == EvolutionState.COMPLETED
        assert metrics is not None
        assert metrics.generation == 1
        assert len(engine.metrics_history) == 1
        assert engine.best_genome is not None
    
    def test_select_parents(self):
        """测试选择父代"""
        engine = EvolutionEngine(population_size=10)
        
        parents = engine.select_parents()
        
        assert len(parents) == 2
        assert parents[0] in engine.population
        assert parents[1] in engine.population
    
    @pytest.mark.asyncio
    async def test_run_evolution(self):
        """测试运行进化过程"""
        engine = EvolutionEngine(population_size=10)
        
        def fitness_func(genome):
            base = sum(genome.genes.values()) if genome.genes else 0
            return base + 0.01
        
        result = await engine.run_evolution(
            fitness_func=fitness_func,
            max_generations=5
        )
        
        assert "success" in result
        assert "generations" in result
        assert "best_fitness" in result
        assert result["generations"] <= 5
    
    def test_get_status(self):
        """测试获取状态"""
        engine = EvolutionEngine(population_size=20)
        
        status = engine.get_status()
        
        assert status["state"] == EvolutionState.IDLE.value
        assert status["generation"] == 0
        assert status["population_size"] == 20
        assert status["strategy"] == EvolutionStrategy.ADAPTIVE.value
    
    def test_evolution_metrics_calculation(self):
        """测试进化指标计算"""
        engine = EvolutionEngine(population_size=10)
        
        def simple_fitness(genome):
            return 1.0
        
        engine.evolve_generation(simple_fitness)
        
        metrics = engine.metrics_history[0]
        
        assert metrics.generation == 1
        assert metrics.fitness_score >= 0
        assert metrics.diversity_score >= 0
        assert metrics.stability_score >= 0
        assert 0 <= metrics.learning_progress <= 1
