/**
 * Agent类型定义
 * Agent永续自进化系统 - 前端应用
 */

export type AgentStatus = 'idle' | 'running' | 'paused' | 'stopped' | 'error';

export interface Agent {
  id: string;
  name: string;
  description?: string;
  status: AgentStatus;
  state: string;
  genome_data: Record<string, any>;
  fitness_score: number;
  generation: number;
  population_rank: number;
  is_active: boolean;
  is_evolving: boolean;
  extra_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  last_evolution_at?: string;
  user_id: string;
}

export interface AgentCreate {
  name: string;
  description?: string;
  genome_data?: Record<string, any>;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  status?: AgentStatus;
  genome_data?: Record<string, any>;
}

export interface AgentListParams {
  skip?: number;
  limit?: number;
  status?: AgentStatus;
  search?: string;
}

export interface AgentListResponse {
  total: number;
  agents: Agent[];
}

export interface PopulationStats {
  total_agents: number;
  avg_fitness: number;
  max_fitness: number;
  min_fitness: number;
}

export interface EvolutionConfig {
  max_generations: number;
  population_size: number;
  mutation_rate: number;
  crossover_rate: number;
}

export interface EvolutionResult {
  success: boolean;
  generations_completed: number;
  best_fitness: number;
  message: string;
}
