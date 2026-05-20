import { useEffect, useState } from 'react';
import { Plus, Search, MoreVertical, Edit, Trash2, Eye } from 'lucide-react';
import { Card } from '../components/Card';
import { useAppStore } from '../store';
import { api } from '../services/api';
import { Tenant } from '../types/models';
import { cn } from '../lib/utils';

const tierColors: Record<string, string> = {
  free: 'bg-slate-100 text-slate-700',
  basic: 'bg-blue-100 text-blue-700',
  pro: 'bg-purple-100 text-purple-700',
  enterprise: 'bg-orange-100 text-orange-700',
  unlimited: 'bg-green-100 text-green-700',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-slate-100 text-slate-700',
  suspended: 'bg-red-100 text-red-700',
  trial: 'bg-yellow-100 text-yellow-700',
  archived: 'bg-gray-100 text-gray-700',
};

const mockTenants: Tenant[] = [
  {
    id: '1',
    name: 'Acme Corp',
    slug: 'acme',
    email: 'admin@acme.com',
    tier: 'enterprise',
    status: 'active',
    quota: { max_agents: 100, max_storage_mb: 10000, max_requests_per_minute: 10000 },
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-05-10T00:00:00Z',
  },
  {
    id: '2',
    name: 'TechStart Inc',
    slug: 'techstart',
    email: 'hello@techstart.io',
    tier: 'pro',
    status: 'active',
    quota: { max_agents: 50, max_storage_mb: 5000, max_requests_per_minute: 5000 },
    created_at: '2024-02-20T00:00:00Z',
    updated_at: '2024-05-15T00:00:00Z',
  },
  {
    id: '3',
    name: 'Beta Labs',
    slug: 'betalabs',
    email: 'contact@betalabs.ai',
    tier: 'trial',
    status: 'active',
    quota: { max_agents: 10, max_storage_mb: 1000, max_requests_per_minute: 1000 },
    created_at: '2024-05-01T00:00:00Z',
    updated_at: '2024-05-15T00:00:00Z',
  },
];

export function Tenants() {
  const { tenants, setTenants, setLoading } = useAppStore();
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await api.getTenants();
        setTenants(data);
      } catch {
        setTenants(mockTenants);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredTenants = (tenants.length ? tenants : mockTenants).filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tenants</h1>
          <p className="text-slate-500 mt-1">Manage your tenant organizations</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          <Plus size={20} />
          New Tenant
        </button>
      </div>

      <Card>
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search tenants..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Name</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Email</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Tier</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Status</th>
                <th className="text-left py-3 px-4 font-semibold text-slate-700">Agents</th>
                <th className="text-right py-3 px-4 font-semibold text-slate-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTenants.map((tenant) => (
                <tr key={tenant.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-4 px-4">
                    <div className="font-medium text-slate-900">{tenant.name}</div>
                    <div className="text-sm text-slate-500">{tenant.slug}</div>
                  </td>
                  <td className="py-4 px-4 text-slate-600">{tenant.email}</td>
                  <td className="py-4 px-4">
                    <span className={cn('px-2.5 py-1 rounded-full text-xs font-medium', tierColors[tenant.tier])}>
                      {tenant.tier}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={cn('px-2.5 py-1 rounded-full text-xs font-medium', statusColors[tenant.status])}>
                      {tenant.status}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-slate-600">{tenant.quota.max_agents}</td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
                        <Eye size={16} />
                      </button>
                      <button className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
                        <Edit size={16} />
                      </button>
                      <button className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
