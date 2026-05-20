import { create } from 'zustand';
import { Tenant, ServiceInstance, SystemMetrics, EvolutionMetric, LogEntry } from '../types/models';

interface AppState {
  tenants: Tenant[];
  currentTenant: Tenant | null;
  services: ServiceInstance[];
  metrics: SystemMetrics | null;
  evolutionMetrics: EvolutionMetric[];
  logs: LogEntry[];
  loading: boolean;
  sidebarOpen: boolean;

  setTenants: (tenants: Tenant[]) => void;
  setCurrentTenant: (tenant: Tenant | null) => void;
  setServices: (services: ServiceInstance[]) => void;
  setMetrics: (metrics: SystemMetrics) => void;
  setEvolutionMetrics: (metrics: EvolutionMetric[]) => void;
  setLogs: (logs: LogEntry[]) => void;
  setLoading: (loading: boolean) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  tenants: [],
  currentTenant: null,
  services: [],
  metrics: null,
  evolutionMetrics: [],
  logs: [],
  loading: false,
  sidebarOpen: true,

  setTenants: (tenants) => set({ tenants }),
  setCurrentTenant: (tenant) => set({ currentTenant: tenant }),
  setServices: (services) => set({ services }),
  setMetrics: (metrics) => set({ metrics }),
  setEvolutionMetrics: (evolutionMetrics) => set({ evolutionMetrics }),
  setLogs: (logs) => set({ logs }),
  setLoading: (loading) => set({ loading }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
