import React from 'react';
import { useQuery } from '@tanstack/react-query';

import adminService from '../../services/adminService';
import type { UsageMetrics } from '../../types';

const UsagePage: React.FC = () => {
  const usageQuery = useQuery<UsageMetrics>({
    queryKey: ['admin', 'usage', 'system'],
    queryFn: () => adminService.getUsage({ granularity: 'day' }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Usage</h1>
        <p className="mt-2 text-sm text-gray-700">
          Daily aggregate usage across all tenants for the last 30 days.
        </p>
      </div>

      {usageQuery.isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : usageQuery.data ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-xs text-gray-500">Total usage</p>
              <p className="text-xl font-semibold">
                {usageQuery.data.totals.total_usage}
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-xs text-gray-500">Total cost</p>
              <p className="text-xl font-semibold">
                ${usageQuery.data.totals.total_cost.toFixed(2)}
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-xs text-gray-500">Tenants</p>
              <p className="text-xl font-semibold">
                {usageQuery.data.totals.total_tenants}
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-xs text-gray-500">Users</p>
              <p className="text-xl font-semibold">
                {usageQuery.data.totals.total_users}
              </p>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-xs text-gray-500">Tasks</p>
              <p className="text-xl font-semibold">
                {usageQuery.data.totals.total_tasks}
              </p>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Active tenants
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Usage
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {usageQuery.data.metrics.map((point) => (
                  <tr key={point.date}>
                    <td className="px-4 py-2 text-sm text-gray-700">
                      {new Date(point.date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-700">
                      {point.active_tenants}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-700">{point.value}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">
                      ${point.cost.toFixed(2)}
                    </td>
                  </tr>
                ))}
                {usageQuery.data.metrics.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">
                      No usage recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="text-sm text-red-600">Failed to load usage.</p>
      )}
    </div>
  );
};

export default UsagePage;
