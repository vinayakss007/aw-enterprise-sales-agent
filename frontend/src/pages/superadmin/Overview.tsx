import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  UsersIcon,
  BoltIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import superadminService, {
  SuperadminOverview,
  SuperadminUser,
  TenantLimits,
} from '../../services/superadminService';

const ROLES = ['viewer', 'user', 'admin', 'owner', 'superadmin'];

const SuperadminOverviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [limitsModalOpen, setLimitsModalOpen] = useState(false);
  const [selectedTenantId, setSelectedTenantId] = useState<string>('');
  const [limitsForm, setLimitsForm] = useState<TenantLimits>({});

  const overviewQuery = useQuery<SuperadminOverview>({
    queryKey: ['superadmin', 'overview'],
    queryFn: () => superadminService.getOverview(),
  });

  const usersQuery = useQuery<SuperadminUser[]>({
    queryKey: ['superadmin', 'users'],
    queryFn: () => superadminService.listUsers({ limit: 200 }),
  });

  const setRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      superadminService.setUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin', 'users'] });
      toast('User role updated', 'success');
    },
    onError: () => toast('Failed to update role', 'error'),
  });

  const activateMutation = useMutation({
    mutationFn: (userId: string) => superadminService.activateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin', 'users'] });
      toast('User activated', 'success');
    },
    onError: () => toast('Failed to activate user', 'error'),
  });

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => superadminService.deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin', 'users'] });
      toast('User deactivated', 'success');
    },
    onError: () => toast('Failed to deactivate user', 'error'),
  });

  const tenantLimitsQuery = useQuery<TenantLimits>({
    queryKey: ['superadmin', 'tenant-limits', selectedTenantId],
    queryFn: () => superadminService.getTenantLimits(selectedTenantId),
    enabled: !!selectedTenantId && limitsModalOpen,
  });

  const setLimitsMutation = useMutation({
    mutationFn: ({ tenantId, limits }: { tenantId: string; limits: TenantLimits }) =>
      superadminService.setTenantLimits(tenantId, limits),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin'] });
      setLimitsModalOpen(false);
      toast('Tenant limits updated', 'success');
    },
    onError: () => toast('Failed to update limits', 'error'),
  });

  const openLimitsModal = (tenantId: string) => {
    setSelectedTenantId(tenantId);
    setLimitsForm({});
    setLimitsModalOpen(true);
  };

  // Populate form when limits data loads
  React.useEffect(() => {
    if (tenantLimitsQuery.data) {
      setLimitsForm(tenantLimitsQuery.data);
    }
  }, [tenantLimitsQuery.data]);

  const overview = overviewQuery.data;

  const stats = overview
    ? [
        { name: 'Total Tenants', value: overview.total_tenants, icon: BuildingOfficeIcon },
        { name: 'Total Users', value: overview.total_users, icon: UsersIcon },
        { name: 'Total Leads', value: overview.total_leads, icon: UserGroupIcon },
        { name: 'Total Campaigns', value: overview.total_campaigns, icon: ChartBarIcon },
        { name: 'Agent Runs', value: overview.total_agent_runs, icon: BoltIcon },
        { name: 'Total Cost', value: `$${overview.total_cost.toFixed(2)}`, icon: CurrencyDollarIcon },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Superadmin Overview</h1>
        <p className="mt-1 text-sm text-gray-600">
          Platform-wide statistics, user management, and tenant configuration.
        </p>
      </div>

      {/* Stat cards */}
      {overviewQuery.isLoading ? (
        <div className="text-sm text-gray-500">Loading overview...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:px-6"
            >
              <dt>
                <div className="absolute rounded-md bg-indigo-500 p-3">
                  <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                </div>
                <p className="ml-16 truncate text-sm font-medium text-gray-500">
                  {stat.name}
                </p>
              </dt>
              <dd className="ml-16 flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </dd>
            </div>
          ))}
        </div>
      )}

      {/* Users table */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">All Users</h2>
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          {usersQuery.isLoading ? (
            <div className="p-12 text-sm text-gray-500 text-center">Loading users...</div>
          ) : usersQuery.isError ? (
            <div className="p-12 text-sm text-red-600 text-center">Failed to load users.</div>
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
                    Status
                  </th>
                  <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
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
                    <td className="px-3 py-4 text-sm">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          setRoleMutation.mutate({ userId: user.id, role: e.target.value })
                        }
                        className="rounded-md border-gray-300 text-sm"
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-4 text-sm text-gray-500 font-mono text-xs">
                      <button
                        type="button"
                        className="text-indigo-600 hover:text-indigo-900 underline"
                        onClick={() => openLimitsModal(user.tenant_id)}
                      >
                        {user.tenant_id.slice(0, 8)}...
                      </button>
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
                    <td className="px-3 py-4 text-sm">
                      {user.is_active ? (
                        <button
                          type="button"
                          onClick={() => deactivateMutation.mutate(user.id)}
                          disabled={deactivateMutation.isPending}
                          className="text-red-600 hover:text-red-900 text-sm font-medium disabled:opacity-50"
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => activateMutation.mutate(user.id)}
                          disabled={activateMutation.isPending}
                          className="text-green-600 hover:text-green-900 text-sm font-medium disabled:opacity-50"
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

      {/* Tenant Limits Modal */}
      <Modal
        isOpen={limitsModalOpen}
        onClose={() => setLimitsModalOpen(false)}
        title={`Tenant Limits: ${selectedTenantId.slice(0, 8)}...`}
        size="lg"
      >
        {tenantLimitsQuery.isLoading ? (
          <div className="p-4 text-sm text-gray-500">Loading limits...</div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setLimitsMutation.mutate({ tenantId: selectedTenantId, limits: limitsForm });
            }}
            className="space-y-4"
          >
            {[
              ['max_users', 'Max Users'],
              ['max_leads', 'Max Leads'],
              ['max_campaigns', 'Max Campaigns'],
              ['max_agent_runs_per_day', 'Max Agent Runs / Day'],
              ['max_cost_per_month', 'Max Cost / Month ($)'],
            ].map(([key, label]) => (
              <label key={key} className="block">
                <span className="block text-sm font-medium text-gray-700">{label}</span>
                <input
                  type="number"
                  value={limitsForm[key] ?? ''}
                  onChange={(e) =>
                    setLimitsForm({
                      ...limitsForm,
                      [key]: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  placeholder="No limit"
                />
              </label>
            ))}
            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded-md"
                onClick={() => setLimitsModalOpen(false)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={setLimitsMutation.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md disabled:opacity-50"
              >
                {setLimitsMutation.isPending ? 'Saving...' : 'Save Limits'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default SuperadminOverviewPage;
