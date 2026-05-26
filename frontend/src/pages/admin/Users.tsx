import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PlusIcon } from '@heroicons/react/24/outline';

import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import adminService from '../../services/adminService';
import { api } from '../../services/api';
import type { User } from '../../types';

const UsersPage: React.FC = () => {
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<string>('user');
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const usersQuery = useQuery<User[]>({
    queryKey: ['admin', 'users'],
    queryFn: () => adminService.listUsers({ limit: 200 }),
  });

  const inviteMutation = useMutation({
    mutationFn: async (payload: { email: string; role: string }) => {
      const response = await api.post<{ invite_token: string; invite_link?: string }>(
        '/auth/invite',
        payload
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      setInviteOpen(false);
      setInviteEmail('');
      setInviteRole('user');
      const link = data.invite_link || data.invite_token;
      toast(`Invite sent! Token: ${link}`, 'success');
    },
    onError: (err: unknown) => {
      toast(err instanceof Error ? err.message : 'Failed to send invite', 'error');
    },
  });

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">Users</h1>
          <p className="mt-2 text-sm text-gray-700">All users across all tenants.</p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setInviteOpen(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            Invite User
          </button>
        </div>
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
      {/* Invite User Modal */}
      <Modal
        isOpen={inviteOpen}
        onClose={() => setInviteOpen(false)}
        title="Invite User"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            inviteMutation.mutate({ email: inviteEmail, role: inviteRole });
          }}
          className="space-y-4"
        >
          <label className="block">
            <span className="block text-sm font-medium text-gray-700">Email</span>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="user@example.com"
            />
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700">Role</span>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="viewer">Viewer</option>
              <option value="user">User</option>
              <option value="admin">Admin</option>
              <option value="owner">Owner</option>
            </select>
          </label>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              className="px-4 py-2 text-sm border rounded-md"
              onClick={() => setInviteOpen(false)}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={inviteMutation.isPending}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md disabled:opacity-50"
            >
              {inviteMutation.isPending ? 'Sending...' : 'Send Invite'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default UsersPage;
