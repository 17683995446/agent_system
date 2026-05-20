import { useEffect, useState } from 'react';
import { Users, Server, Brain, Activity, TrendingUp } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { Card } from '../components/Card';
import { StatCard } from '../components/StatCard';
import { useAppStore } from '../store';
import { api } from '../services/api';
import { SystemMetrics, EvolutionMetric } from '../types/models';

const mockChartData = [
  { time: '00:00', requests: 120, latency: 45 },
  { time: '04:00', requests: 80, latency: 32 },
  { time: '08:00', requests: 250, latency: 68 },
  { time: '12:00', requests: 450, latency: 92 },
  { time: '16:00', requests: 520, latency: 105 },
  { time: '20:00', requests: 380, latency: 78 },
  { time: '23:59', requests: 200, latency: 55 },
];

const mockEvolutionData = [
  { timestamp: '1', performance: 65, diversity: 45, fitness: 55 },
  { timestamp: '2', performance: 68, diversity: 48, fitness: 58 },
  { timestamp: '3', performance: 72, diversity: 52, fitness: 62 },
  { timestamp: '4', performance: 78, diversity: 55, fitness: 66 },
  { timestamp: '5', performance: 82, diversity: 58, fitness: 70 },
  { timestamp: '6', performance: 85, diversity: 60, fitness: 73 },
  { timestamp: '7', performance: 88, diversity: 62, fitness: 75 },
];

export function Dashboard() {
  const { metrics, setMetrics, setLoading } = useAppStore();
  const [localMetrics, setLocalMetrics] = useState<SystemMetrics>({
    total_tenants: 24,
    active_tenants: 18,
    total_services: 156,
    healthy_services: 142,
    evolution_progress: 73,
    requests_per_second: 1247,
    uptime: '99.98%',
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await api.getSystemMetrics();
        setMetrics(data);
        setLocalMetrics(data);
      } catch {
        setLocalMetrics(localMetrics);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Welcome back! Here's what's happening.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Tenants"
          value={localMetrics.total_tenants}
          icon={Users}
          color="blue"
          trend={{ value: '12% from last month', positive: true }}
        />
        <StatCard
          title="Healthy Services"
          value={`${localMetrics.healthy_services}/${localMetrics.total_services}`}
          icon={Server}
          color="green"
          trend={{ value: '91% healthy', positive: true }}
        />
        <StatCard
          title="Evolution Progress"
          value={`${localMetrics.evolution_progress}%`}
          icon={Brain}
          color="purple"
          trend={{ value: '+5% this week', positive: true }}
        />
        <StatCard
          title="Requests/Second"
          value={localMetrics.requests_per_second.toLocaleString()}
          icon={Activity}
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Traffic Overview" subtitle="Real-time request statistics">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={mockChartData}>
              <defs>
                <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="time" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              />
              <Area
                type="monotone"
                dataKey="requests"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorRequests)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="AI Evolution" subtitle="Performance metrics over time">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockEvolutionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="timestamp" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              />
              <Line type="monotone" dataKey="performance" stroke="#8b5cf6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="fitness" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
