import {
  Tenant,
  ServiceInstance,
  SystemMetrics,
  EvolutionMetric,
  LogEntry,
} from '../types/models';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getTenants(): Promise<Tenant[]> {
    return this.request<Tenant[]>('/tenants');
  }

  async createTenant(tenant: Omit<Tenant, 'id' | 'created_at' | 'updated_at'>): Promise<Tenant> {
    return this.request<Tenant>('/tenants', {
      method: 'POST',
      body: JSON.stringify(tenant),
    });
  }

  async getTenant(id: string): Promise<Tenant> {
    return this.request<Tenant>(`/tenants/${id}`);
  }

  async updateTenant(id: string, tenant: Partial<Tenant>): Promise<Tenant> {
    return this.request<Tenant>(`/tenants/${id}`, {
      method: 'PUT',
      body: JSON.stringify(tenant),
    });
  }

  async deleteTenant(id: string): Promise<void> {
    return this.request<void>(`/tenants/${id}`, {
      method: 'DELETE',
    });
  }

  async getServices(): Promise<ServiceInstance[]> {
    return this.request<ServiceInstance[]>('/services');
  }

  async registerService(service: Omit<ServiceInstance, 'started_at'>): Promise<ServiceInstance> {
    return this.request<ServiceInstance>('/services/register', {
      method: 'POST',
      body: JSON.stringify(service),
    });
  }

  async getService(id: string): Promise<ServiceInstance> {
    return this.request<ServiceInstance>(`/services/${id}`);
  }

  async heartbeat(id: string): Promise<ServiceInstance> {
    return this.request<ServiceInstance>(`/services/${id}/heartbeat`, {
      method: 'PUT',
    });
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.request<SystemMetrics>('/metrics/system');
  }

  async getServiceMetrics(): Promise<Record<string, any>> {
    return this.request<Record<string, any>>('/metrics/services');
  }

  async getLogs(): Promise<LogEntry[]> {
    return this.request<LogEntry[]>('/logs');
  }
}

export const api = new ApiClient();
