import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, Clock, Search, Download } from 'lucide-react';
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
import { useAppStore } from '../store';
import { api } from '../services/api';
import { LogEntry } from '../types/models';
import { cn } from '../lib/utils';

const mockMetricsData = [
  { time: '10:00', cpu: 45, memory: 62, network: 38 },
  { time: '10:05', cpu: 52, memory: 65, network: 42 },
  { time: '10:10', cpu: 48, memory: 63, network: 40 },
  { time: '10:15', cpu: 55, memory: 68, network: 45 },
  { time: '10:20', cpu: 62, memory: 72, network: 52 },
  { time: '10:25', cpu: 58, memory: 70, network: 48 },
  { time: '10:30', cpu: 54, memory: 67, network: 44 },
];

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: '2024-05-16T10:32:15Z',
    level: 'info',
    service: 'Agent Orchestrator',
    message: 'Successfully processed 1247 requests in the last minute',
  },
  {
    id: '2',
    timestamp: '2024-05-16T10:31:42Z',
    level: 'warn',
    service: 'Memory Service',
    message: 'High memory usage detected: 85% of capacity',
  },
  {
    id: '3',
    timestamp: '2024-05-16T10:30:18Z',
    level: 'info',
    service: 'Evolution Engine',
    message: 'Generation 8 evaluation completed successfully',
  },
  {
    id: '4',
    timestamp: '2024-05-16T10:29:05Z',
    level: 'error',
    service: 'Metrics Collector',
    message: 'Failed to connect to Prometheus endpoint',
  },
  {
    id: '5',
    timestamp: '2024-05-16T10:28:33Z',
    level: 'info',
    service: 'API Gateway',
    message: 'Rate limit threshold reset for tenant "acme"',
  },
];

const levelColors: Record<string, string> = {
  debug: 'bg-slate-100 text-slate-700',
  info: 'bg-blue-100 text-blue-700',
  warn: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
};

const levelIcons: Record<string, typeof Activity> = {
  debug: Clock,
  info: CheckCircle,
  warn: AlertTriangle,
  error: AlertTriangle,
};

export function Monitoring() {
  const { logs, setLogs, setLoading } = useAppStore();
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await api.getLogs();
        setLogs(data);
      } catch {
        setLogs(mockLogs);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredLogs = (logs.length ? logs : mockLogs).filter((log) => {
    const matchesSearch =
      log.message.toLowerCase().includes(search.toLowerCase()) ||
      log.service.toLowerCase().includes(search.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Monitoring</h1>
          <p className="text-slate-500 mt-1">Real-time system metrics and logs</p>
        </div>
        <button className="flex items-center gap-2 bg-slate-100 text-slate-700 px-4 py-2 rounded-lg hover:bg-slate-200 transition-colors">
          <Download size={20} />
          Export
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="text-center">
          <div className="text-3xl font-bold text-blue-600">99.98%</div>
          <div className="text-sm text-slate-500">Uptime</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-green-600">142</div>
          <div className="text-sm text-slate-500">Healthy Services</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-orange-600">1.2K</div>
          <div className="text-sm text-slate-500">Avg Requests/Min</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-purple-600">45ms</div>
          <div className="text-sm text-slate-500">Avg Latency</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="CPU & Memory" subtitle="Resource utilization over time">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={mockMetricsData}>
              <defs>
                <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
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
                dataKey="cpu"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorCpu)"
                name="CPU %"
              />
              <Area
                type="monotone"
                dataKey="memory"
                stroke="#8b5cf6"
                fillOpacity={1}
                fill="url(#colorMemory)"
                name="Memory %"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Network Traffic" subtitle="Inbound & outbound bandwidth">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={mockMetricsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="time" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              />
              <Line type="monotone" dataKey="network" stroke="#06b6d4" strokeWidth={2} name="MB/s" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Logs" subtitle="System activity logs">
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search logs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Levels</option>
            <option value="error">Error</option>
            <option value="warn">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
          </select>
        </div>

        <div className="space-y-3">
          {filteredLogs.map((log) => {
            const Icon = levelIcons[log.level] || Activity;
            return (
              <div key={log.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <div className={cn('p-2 rounded-lg', levelColors[log.level])}>
                  <Icon size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{log.service}</span>
                    <span className={cn('px-2 py-0.5 rounded text-xs font-medium', levelColors[log.level])}>
                      {log.level}
                    </span>
                    <span className="text-xs text-slate-400">{log.timestamp}</span>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">{log.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
