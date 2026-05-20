import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Server,
  Brain,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Cpu,
  TestTube,
} from 'lucide-react';
import { useAppStore } from '../store';
import { cn } from '../lib/utils';

const menuItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/architecture', icon: Cpu, label: 'Architecture' },
  { path: '/tenants', icon: Users, label: 'Tenants' },
  { path: '/services', icon: Server, label: 'Services' },
  { path: '/evolution', icon: Brain, label: 'Evolution' },
  { path: '/monitoring', icon: Activity, label: 'Monitoring' },
  { path: '/test-results', icon: TestTube, label: 'Test Results' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useAppStore();

  return (
    <>
      <aside
        className={cn(
          'fixed left-0 top-0 h-full bg-slate-900 text-white transition-all duration-300 z-50',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-700">
          {sidebarOpen ? (
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AgentOS
            </span>
          ) : (
            <span className="text-xl font-bold">A</span>
          )}
          <button
            onClick={toggleSidebar}
            className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
          >
            {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>

        <nav className="mt-4 px-2">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-3 rounded-lg mb-1 transition-all',
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <item.icon size={20} />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>
      {!sidebarOpen && (
        <div className="fixed left-20 top-0 h-full w-1 bg-transparent hover:w-64 z-40" />
      )}
    </>
  );
}
