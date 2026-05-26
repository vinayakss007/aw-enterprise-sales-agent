import React from 'react';
import { useQuery } from '@tanstack/react-query';

import adminService from '../../services/adminService';
import type { User } from '../../types';

const UsersPage: React.FC = () => {
  const usersQuery = useQuery<User[]>({
    queryKey: ['admin', 'users'],
    queryFn: () => adminService.listUsers({ limit: 200 }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Users</h1>
        <p className="mt-2 text-sm text-gray-700">All users across all tenants.</p>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {usersQuery.isLoading ? (
          <div className="p-12 text-sm text-gray-500 text-center">Loading…</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Email
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Role
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Tenant
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Active
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Last login
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {usersQuery.data?.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="py-4 pl-4 pr-3 text-sm font-medium text-gray-900">
                    {user.name}
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">{user.email}</td>
                  <td className="px-3 py-4 text-sm text-gray-700">{user.role}</td>
                  <td className="px-3 py-4 text-sm text-gray-500 font-mono text-xs">
                    {user.tenant_id.slice(0, 8)}…
                  </td>
                  <td className="px-3 py-4 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-500">
                    {user.last_login_at
                      ? new Date(user.last_login_at).toLocaleDateString()
                      : '—'}
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

export default UsersPage;
