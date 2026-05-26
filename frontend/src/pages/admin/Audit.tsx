import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

import adminService, {
  AuditChainResult,
  AuditLogEntry,
} from '../../services/adminService';

const AuditPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [actionFilter, setActionFilter] = useState<string>('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('');
  const [verification, setVerification] = useState<AuditChainResult | null>(null);

  const logsQuery = useQuery<AuditLogEntry[]>({
    queryKey: ['admin', 'audit', actionFilter, resourceTypeFilter],
    queryFn: () =>
      adminService.listAuditLogs({
        action: actionFilter || undefined,
        resource_type: resourceTypeFilter || undefined,
        limit: 200,
      }),
  });

  const verifyMutation = useMutation({
    mutationFn: () => adminService.verifyAuditChain(),
    onSuccess: (result) => setVerification(result),
  });

  const renderHash = (hash: string | null) =>
    hash ? <span className="font-mono text-xs">{hash.slice(0, 12)}…</span> : '—';

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Audit log</h1>
          <p className="mt-2 text-sm text-gray-700">
            Tamper-resistant chain of every security-sensitive action in your tenant.
          </p>
        </div>
        <button
          type="button"
          onClick={() => verifyMutation.mutate()}
          disabled={verifyMutation.isPending}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
        >
          <ShieldCheckIcon className="-ml-1 mr-2 h-5 w-5" />
          {verifyMutation.isPending ? 'Verifying…' : 'Verify chain'}
        </button>
      </div>

      {verification && (
        <div
          className={`rounded-md p-4 ${
            verification.verified
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center">
            {verification.verified ? (
              <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
            )}
            <p
              className={`text-sm font-medium ${
                verification.verified ? 'text-green-800' : 'text-red-800'
              }`}
            >
              {verification.verified
                ? `Chain intact — ${verification.count} entries verified.`
                : `Chain broken at ${verification.broken_at.length} row(s): ${verification.broken_at.join(', ')}`}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        >
          <option value="">All actions</option>
          <option value="login.success">login.success</option>
          <option value="login.failed">login.failed</option>
          <option value="user.create">user.create</option>
          <option value="lead.create">lead.create</option>
          <option value="lead.update">lead.update</option>
          <option value="lead.archive">lead.archive</option>
          <option value="campaign.create">campaign.create</option>
          <option value="campaign.activate">campaign.activate</option>
          <option value="campaign.deactivate">campaign.deactivate</option>
          <option value="campaign.delete">campaign.delete</option>
          <option value="campaign.add_leads">campaign.add_leads</option>
        </select>
        <select
          value={resourceTypeFilter}
          onChange={(e) => setResourceTypeFilter(e.target.value)}
          className="rounded-md border-gray-300 text-sm"
        >
          <option value="">All resource types</option>
          <option value="user">user</option>
          <option value="lead">lead</option>
          <option value="campaign">campaign</option>
        </select>
        <button
          type="button"
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'audit'] });
            setVerification(null);
          }}
          className="inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowPathIcon className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {logsQuery.isLoading ? (
          <div className="p-12 text-sm text-gray-500 text-center">Loading…</div>
        ) : logsQuery.data && logsQuery.data.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Timestamp
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Action
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Resource
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  User
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  IP
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Hash
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logsQuery.data.map((row) => (
                <tr
                  key={row.id}
                  className={
                    verification && verification.broken_at.includes(row.id)
                      ? 'bg-red-50'
                      : undefined
                  }
                >
                  <td className="py-3 pl-4 pr-3 text-xs text-gray-500 font-mono">
                    {new Date(row.timestamp).toLocaleString()}
                  </td>
                  <td className="px-3 py-3 text-sm font-medium text-gray-900">
                    {row.action}
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-700">
                    <div>{row.resource_type}</div>
                    <div className="text-xs text-gray-400 font-mono">
                      {row.resource_id.length > 20
                        ? row.resource_id.slice(0, 8) + '…'
                        : row.resource_id}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-xs text-gray-500 font-mono">
                    {row.user_id ? row.user_id.slice(0, 8) + '…' : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs text-gray-500 font-mono">
                    {row.ip_address ?? '—'}
                  </td>
                  <td className="px-3 py-3 text-sm text-gray-500">
                    {renderHash(row.current_hash)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center text-sm text-gray-500">
            No audit entries match those filters.
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditPage;
