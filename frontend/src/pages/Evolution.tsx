import { useEffect } from 'react';
import { Brain, TrendingUp, Zap, Target } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { Card } from '../components/Card';
import { useAppStore } from '../store';
import { EvolutionMetric } from '../types/models';

const mockEvolutionData: EvolutionMetric[] = [
  { timestamp: 'Gen 1', performance: 45, diversity: 60, fitness: 52 },
  { timestamp: 'Gen 2', performance: 52, diversity: 58, fitness: 55 },
  { timestamp: 'Gen 3', performance: 58, diversity: 62, fitness: 60 },
  { timestamp: 'Gen 4', performance: 65, diversity: 65, fitness: 65 },
  { timestamp: 'Gen 5', performance: 72, diversity: 63, fitness: 67 },
  { timestamp: 'Gen 6', performance: 78, diversity: 68, fitness: 73 },
  { timestamp: 'Gen 7', performance: 82, diversity: 70, fitness: 76 },
  { timestamp: 'Gen 8', performance: 86, diversity: 72, fitness: 79 },
];

const strategyData = [
  { name: 'Strategy A', success: 85, attempts: 120 },
  { name: 'Strategy B', success: 72, attempts: 95 },
  { name: 'Strategy C', success: 68, attempts: 88 },
  { name: 'Strategy D', success: 91, attempts: 132 },
  { name: 'Strategy E', success: 55, attempts: 67 },
];

export function Evolution() {
  const { evolutionMetrics, setEvolutionMetrics } = useAppStore();

  useEffect(() => {
    setEvolutionMetrics(mockEvolutionData);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">AI Evolution</h1>
        <p className="text-slate-500 mt-1">Monitor the evolutionary progress of your AI agents</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-lg">
            <Brain size={28} className="text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Current Generation</p>
            <p className="text-2xl font-bold text-slate-900">8</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <TrendingUp size={28} className="text-green-600" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Performance Score</p>
            <p className="text-2xl font-bold text-slate-900">86%</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Zap size={28} className="text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Population Size</p>
            <p className="text-2xl font-bold text-slate-900">256</p>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Evolution Progress" subtitle="Performance across generations">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={evolutionMetrics.length ? evolutionMetrics : mockEvolutionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="timestamp" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              />
              <Legend />
              <Line type="monotone" dataKey="performance" stroke="#8b5cf6" strokeWidth={2} name="Performance" />
              <Line type="monotone" dataKey="fitness" stroke="#06b6d4" strokeWidth={2} name="Fitness" />
              <Line type="monotone" dataKey="diversity" stroke="#f59e0b" strokeWidth={2} name="Diversity" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Strategy Success" subtitle="Success rate by strategy type">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={strategyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
              />
              <Legend />
              <Bar dataKey="success" fill="#8b5cf6" name="Success Rate" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Knowledge Graph" subtitle="Entity relationships and connections">
        <div className="h-80 bg-slate-900 rounded-lg flex items-center justify-center text-slate-400">
          <div className="text-center">
            <Target size={48} className="mx-auto mb-3 opacity-50" />
            <p>Knowledge Graph Visualization</p>
            <p className="text-sm mt-1">Interactive force-directed graph would be displayed here</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
