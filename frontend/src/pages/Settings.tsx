import { Settings as SettingsIcon, Bell, Shield, Database, Palette, User } from 'lucide-react';
import { Card } from '../components/Card';

const settingsSections = [
  {
    icon: User,
    title: 'Profile',
    description: 'Manage your account profile and preferences',
  },
  {
    icon: Bell,
    title: 'Notifications',
    description: 'Configure email and push notification settings',
  },
  {
    icon: Shield,
    title: 'Security',
    description: 'Password, 2FA, and API key management',
  },
  {
    icon: Database,
    title: 'Data & Storage',
    description: 'Backup, retention, and storage configuration',
  },
  {
    icon: Palette,
    title: 'Appearance',
    description: 'Theme, layout, and interface customization',
  },
];

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 mt-1">Manage your account and application settings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {settingsSections.map((section, index) => {
          const Icon = section.icon;
          return (
            <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-slate-100 rounded-lg">
                  <Icon size={24} className="text-slate-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{section.title}</h3>
                  <p className="text-sm text-slate-500 mt-1">{section.description}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <Card title="System Information">
        <div className="space-y-4">
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Version</span>
            <span className="font-medium text-slate-900">v2.1.0</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Environment</span>
            <span className="font-medium text-slate-900">Production</span>
          </div>
          <div className="flex justify-between py-2 border-b border-slate-100">
            <span className="text-slate-500">Last Updated</span>
            <span className="font-medium text-slate-900">2024-05-15</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-slate-500">Build Hash</span>
            <span className="font-medium text-slate-900 font-mono text-sm">a1b2c3d...</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
