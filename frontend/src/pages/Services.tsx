import { useEffect, useState } from 'react';
import { Server, Activity, RefreshCw, Search } from 'lucide-react';
import { Card } from '../components/Card';
import { useAppStore } from '../store';
import { api } from '../services/api';
import { ServiceInstance } from '../types/models';
import { cn } from '../lib/utils';

const statusColors: Record<string, string> = {
  starting: 'bg-yellow-100 text-yellow-700',
  healthy: 'bg-green-100 text-green-700',
  running: 'bg-blue-100 text-blue-700',
  paused: 'bg-orange-100 text-orange-700',
  stopping: 'bg-orange-100 text-orange-700',
  stopped: 'bg-slate-100 text-slate-700',
  error: 'bg-red-100 text-red-700',
  degraded: 'bg-red-100 text-red-700',
};

const mockServices: ServiceInstance[] = [
  {
    instance_id: 'svc-001',
    service_name: 'Agent Orchestrator',
    service_type: 'core',
    version: 'v2.1.0',
    host: '10.0.1.10',
    port: 8080,
    status: 'healthy',
    health_score: 0.98,
    load_factor: 0.45,
    started_at: '2024-05-10T08:00:00Z',
  },
  {
    instance_id: 'svc-002',
    service_name: 'Memory Service',
    service_type: 'storage',
    version: 'v1.5.2',
    host: '10.0.1.11',
    port: 8081,
    status: 'healthy',
    health_score: 0.95,
    load_factor: 0.62,
    started_at: '2024-05-10T08:01:00Z',
  },
  {
    instance_id: 'svc-003',
    service_name: 'Evolution Engine',
    service_type: 'ai',
    version: 'v3.0.0',
    host: '10.0.1.12',
    port: 8082,
    status: 'running',
    health_score: 0.92,
    load_factor: 0.85,
    started_at: '2024-05-10T08:02:00Z',
  },
  {
    instance_id: 'svc-004',
    service_name: 'API Gateway',
    service_type: 'gateway',
    version: 'v2.3.1',
    host: '10.0.1.13',
    port: 8000,
    status: 'healthy',
    health_score: 0.99,
    load_factor: 0.32,
    started_at: '2024-05-10T08:00:00Z',
  },
  {
    instance_id: 'svc-005',
    service_name: 'Metrics Collector',
    service_type: 'monitoring',
    version: 'v1.2.0',
    host: '10.0.1.14',
    port: 9090,
    status: 'degraded',
    health_score: 0.65,
    load_factor: 0.95,
    started_at: '2024-05-14T14:30:00Z',
  },
];

export function Services() {
  const { services, setServices, setLoading } = useAppStore();
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await api.getServices();
        setServices(data);
      } catch {
        setServices(mockServices);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredServices = (services.length ? services : mockServices).filter((s) =>
    s.service_name.toLowerCase().includes(search.toLowerCase()) ||
    s.service_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Services</h1>
          <p className="text-slate-500 mt-1">Monitor and manage your service mesh</p>
        </div>
        <button className="flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-lg hover:bg-slate-200 transition-colors">
          <RefreshCw size={20} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="text-center">
          <div className="text-3xl font-bold text-slate-900">{filteredServices.length}</div>
          <div className="text-sm text-slate-500">Total Services</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-green-600">
            {filteredServices.filter((s) => s.status === 'healthy' || s.status === 'running').length}
          </div>
          <div className="text-sm text-slate-500">Healthy</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-orange-600">
            {filteredServices.filter((s) => s.status === 'degraded' || s.status === 'starting').length}
          </div>
          <div className="text-sm text-slate-500">Warning</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-red-600">
            {filteredServices.filter((s) => s.status === 'error' || s.status === 'stopped').length}
          </div>
          <div className="text-sm text-slate-500">Critical</div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search services..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredServices.map((service) => (
            <div
              key={service.instance_id}
              className="border border-slate-200 rounded-xl p-4 hover:border-slate-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">
                    <Server size={20} className="text-slate-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{service.service_name}</h3>
                    <p className="text-sm text-slate-500">{service.service_type}</p>
                  </div>
                </div>
                <span className={cn('px-2.5 py-1 rounded-full text-xs font-medium', statusColors[service.status])}>
                  {service.status}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Version</span>
                  <p className="font-medium text-slate-900">{service.version}</p>
                </div>
                <div>
                  <span className="text-slate-500">Endpoint</span>
                  <p className="font-medium text-slate-900">{service.host}:{service.port}</p>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Health Score</span>
                    <span>{Math.round(service.health_score * 100)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full transition-all duration-500',
                        service.health_score >= 0.9 ? 'bg-green-500' :
                        service.health_score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                      )}
                      style={{ width: `${service.health_score * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Load</span>
                    <span>{Math.round(service.load_factor * 100)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-500"
                      style={{ width: `${service.load_factor * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
