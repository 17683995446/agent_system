export interface Tenant {
  id: string;
  name: string;
  slug: string;
  email: string;
  tier: 'free' | 'basic' | 'pro' | 'enterprise' | 'unlimited' | 'trial';
  status: 'active' | 'inactive' | 'suspended' | 'trial' | 'archived';
  quota: {
    max_agents: number;
    max_storage_mb: number;
    max_requests_per_minute: number;
  };
  created_at: string;
  updated_at: string;
}

export interface ServiceInstance {
  instance_id: string;
  service_name: string;
  service_type: string;
  version: string;
  host: string;
  port: number;
  status: 'starting' | 'healthy' | 'running' | 'paused' | 'stopping' | 'stopped' | 'error' | 'degraded';
  health_score: number;
  load_factor: number;
  started_at: string;
}

export interface SystemMetrics {
  total_tenants: number;
  active_tenants: number;
  total_services: number;
  healthy_services: number;
  evolution_progress: number;
  requests_per_second: number;
  uptime: string;
}

export interface EvolutionMetric {
  timestamp: string;
  performance: number;
  diversity: number;
  fitness: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  service: string;
  message: string;
}

export interface KnowledgeNode {
  id: string;
  label: string;
  type: 'concept' | 'entity' | 'relation';
  size: number;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  type: string;
}
