import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ArrowTrendingUpIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

import adminService from '../../services/adminService';
import healthService from '../../services/healthService';

const StatCard: React.FC<{
  label: string;
  value: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  bg: string;
}> = ({ label, value, icon: Icon, bg }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="px-4 py-5 sm:p-6 flex items-center">
      <div className={`flex-shrink-0 ${bg} rounded-md p-3`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div className="ml-5">
        <dt className="text-sm font-medium text-gray-500">{label}</dt>
        <dd className="text-2xl font-semibold text-gray-900">{value}</dd>
      </div>
    </div>
  </div>
);

const AdminDashboard: React.FC = () => {
  const tenantsQuery = useQuery({
    queryKey: ['admin', 'tenants'],
    queryFn: () => adminService.listTenants({ limit: 1000 }),
  });
  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminService.listUsers({ limit: 1000 }),
  });
  const usageQuery = useQuery({
    queryKey: ['admin', 'usage'],
    queryFn: () => adminService.getUsage({ granularity: 'day' }),
  });
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => healthService.check(),
  });

  const totalTenants = tenantsQuery.data?.length ?? '—';
  const totalUsers = usersQuery.data?.length ?? '—';
  const totalCost = usageQuery.data?.totals.total_cost ?? 0;
  const totalTasks = usageQuery.data?.totals.total_tasks ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Admin Dashboard</h1>
        <p className="mt-2 text-sm text-gray-700">
          Live platform metrics. Health status reflects /api/v1/health.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Tenants"
          value={tenantsQuery.isLoading ? '…' : totalTenants}
          icon={BuildingOfficeIcon}
          bg="bg-indigo-500"
        />
        <StatCard
          label="Users"
          value={usersQuery.isLoading ? '…' : totalUsers}
          icon={UsersIcon}
          bg="bg-green-500"
        />
        <StatCard
          label="Total tasks"
          value={usageQuery.isLoading ? '…' : totalTasks}
          icon={ChartBarIcon}
          bg="bg-blue-500"
        />
        <StatCard
          label="Total cost"
          value={
            usageQuery.isLoading
              ? '…'
              : `$${totalCost.toFixed(2)}`
          }
          icon={CurrencyDollarIcon}
          bg="bg-purple-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-2">System health</h2>
          {healthQuery.isLoading ? (
            <p className="text-sm text-gray-500">Loading…</p>
          ) : healthQuery.data ? (
            <dl className="space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Service</dt>
                <dd className="text-gray-900">{healthQuery.data.service}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd
                  className={`font-semibold ${
                    healthQuery.data.status === 'healthy'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {healthQuery.data.status}
                </dd>
              </div>
              {healthQuery.data.version && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Version</dt>
                  <dd className="text-gray-900">{healthQuery.data.version}</dd>
                </div>
              )}
            </dl>
          ) : (
            <p className="text-sm text-red-600">Health probe failed.</p>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
            <ArrowTrendingUpIcon className="h-5 w-5 mr-2 text-gray-500" />
            Quick links
          </h2>
          <ul className="space-y-2 text-sm">
            <li>
              <Link to="/admin/tenants" className="text-indigo-600 hover:text-indigo-500">
                Manage tenants
              </Link>
            </li>
            <li>
              <Link to="/admin/users" className="text-indigo-600 hover:text-indigo-500">
                Manage users
              </Link>
            </li>
            <li>
              <Link to="/admin/usage" className="text-indigo-600 hover:text-indigo-500">
                View usage details
              </Link>
            </li>
            <li>
              <Link to="/admin/settings" className="text-indigo-600 hover:text-indigo-500">
                Settings &amp; campaign worker
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
