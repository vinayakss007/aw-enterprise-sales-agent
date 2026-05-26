import React from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import adminService from '../../services/adminService';
import type { Tenant } from '../../types';

const TenantsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const tenantsQuery = useQuery<Tenant[]>({
    queryKey: ['admin', 'tenants'],
    queryFn: () => adminService.listTenants({ limit: 200 }),
  });

  const suspend = useMutation({
    mutationFn: (id: string) => adminService.suspendTenant(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] }),
  });
  const activate = useMutation({
    mutationFn: (id: string) => adminService.activateTenant(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Tenants</h1>
        <p className="mt-2 text-sm text-gray-700">All tenants on the platform.</p>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {tenantsQuery.isLoading ? (
          <div className="p-12 text-sm text-gray-500 text-center">Loading…</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Subdomain
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Plan
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Created
                </th>
                <th className="relative py-3.5 pl-3 pr-4">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tenantsQuery.data?.map((tenant) => (
                <tr key={tenant.id} className="hover:bg-gray-50">
                  <td className="py-4 pl-4 pr-3 text-sm font-medium text-gray-900">
                    {tenant.name}
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">
                    {tenant.subdomain ?? '—'}
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">{tenant.plan}</td>
                  <td className="px-3 py-4 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        tenant.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {tenant.status}
                    </span>
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-500">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-4 pl-3 pr-4 text-right text-sm">
                    {tenant.status === 'active' ? (
                      <button
                        type="button"
                        onClick={() => suspend.mutate(tenant.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Suspend
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => activate.mutate(tenant.id)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Activate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TenantsPage;
