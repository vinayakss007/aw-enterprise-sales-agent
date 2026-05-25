import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  CurrencyDollarIcon,
  PlayIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline';

import agentService from '../../services/agentService';
import campaignService from '../../services/campaignService';
import leadService from '../../services/leadService';
import type { AgentExecution, Lead } from '../../types';

const formatRelative = (iso: string) => new Date(iso).toLocaleString();

const StatCard: React.FC<{
  label: string;
  value: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  bg: string;
  loading?: boolean;
}> = ({ label, value, icon: Icon, bg, loading }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="px-4 py-5 sm:p-6">
      <div className="flex items-center">
        <div className={`flex-shrink-0 ${bg} rounded-md p-3`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dt className="text-sm font-medium text-gray-500 truncate">{label}</dt>
          <dd className="text-2xl font-semibold text-gray-900">
            {loading ? '…' : value}
          </dd>
        </div>
      </div>
    </div>
  </div>
);

const CustomerDashboard: React.FC = () => {
  const leadsQuery = useQuery<Lead[]>({
    queryKey: ['leads', 'dashboard'],
    queryFn: () => leadService.list({ limit: 100 }),
  });

  const executionsQuery = useQuery<AgentExecution[]>({
    queryKey: ['agent-executions', 'dashboard'],
    queryFn: () => agentService.listExecutions({ limit: 50 }),
  });

  const campaignsQuery = useQuery({
    queryKey: ['campaigns', 'dashboard'],
    queryFn: () => campaignService.list({ limit: 100 }),
  });

  const activeLeads =
    leadsQuery.data?.filter((l) => l.status !== 'archived').length ?? 0;
  const successfulRuns =
    executionsQuery.data?.filter((e) => e.success).length ?? 0;
  const totalRuns = executionsQuery.data?.length ?? 0;
  const responseRate =
    totalRuns > 0 ? Math.round((successfulRuns / totalRuns) * 100) : 0;
  const totalCostCents =
    executionsQuery.data?.reduce((acc, e) => acc + (e.cost_cents || 0), 0) ?? 0;
  const activeCampaigns =
    campaignsQuery.data?.filter((c) => c.status === 'active').length ?? 0;

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Live view of your leads, agent runs and campaigns.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Active leads"
          value={activeLeads}
          icon={UserGroupIcon}
          bg="bg-indigo-500"
          loading={leadsQuery.isLoading}
        />
        <StatCard
          label="Agent runs (success rate)"
          value={`${totalRuns} (${responseRate}%)`}
          icon={ChatBubbleLeftRightIcon}
          bg="bg-blue-500"
          loading={executionsQuery.isLoading}
        />
        <StatCard
          label="Active campaigns"
          value={activeCampaigns}
          icon={ChartBarIcon}
          bg="bg-green-500"
          loading={campaignsQuery.isLoading}
        />
        <StatCard
          label="Spend"
          value={`$${(totalCostCents / 100).toFixed(2)}`}
          icon={CurrencyDollarIcon}
          bg="bg-purple-500"
          loading={executionsQuery.isLoading}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 border-b border-gray-200 sm:px-6 flex justify-between items-center">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent leads</h3>
            <Link to="/leads" className="text-sm text-indigo-600 hover:text-indigo-500">
              View all
            </Link>
          </div>
          {leadsQuery.isLoading ? (
            <p className="p-6 text-sm text-gray-500">Loading…</p>
          ) : leadsQuery.data && leadsQuery.data.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {leadsQuery.data.slice(0, 5).map((lead) => (
                <li key={lead.id} className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-indigo-600">
                        {lead.name || lead.email || '(unnamed lead)'}
                      </p>
                      <p className="text-sm text-gray-500">{lead.company}</p>
                    </div>
                    <div className="text-right">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {lead.status}
                      </span>
                      <p className="mt-1 text-xs text-gray-400">
                        {formatRelative(lead.created_at)}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="p-6 text-sm text-gray-500">No leads yet.</p>
          )}
        </div>

        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 border-b border-gray-200 sm:px-6 flex justify-between items-center">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent agent runs</h3>
            <Link to="/agent" className="text-sm text-indigo-600 hover:text-indigo-500">
              Open agent
            </Link>
          </div>
          {executionsQuery.isLoading ? (
            <p className="p-6 text-sm text-gray-500">Loading…</p>
          ) : executionsQuery.data && executionsQuery.data.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {executionsQuery.data.slice(0, 5).map((execution) => (
                <li key={execution.id} className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600">
                      {execution.agent_type}
                    </p>
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        execution.success
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {execution.success ? 'Success' : 'Failed'}
                    </span>
                  </div>
                  <div className="mt-2 flex justify-between text-sm text-gray-500">
                    <p>${(execution.cost_cents / 100).toFixed(2)}</p>
                    <p>{formatRelative(execution.started_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="p-6 text-sm text-gray-500">No agent runs yet.</p>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Quick actions
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            to="/leads"
            className="bg-white shadow rounded-lg p-6 text-center hover:shadow-md transition-shadow"
          >
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white">
              <UserGroupIcon className="h-6 w-6" />
            </div>
            <h4 className="mt-4 text-sm font-medium text-gray-900">Add lead</h4>
            <p className="mt-1 text-sm text-gray-500">Add a new lead to your database</p>
          </Link>
          <Link
            to="/agent"
            className="bg-white shadow rounded-lg p-6 text-center hover:shadow-md transition-shadow"
          >
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-md bg-green-500 text-white">
              <PlayIcon className="h-6 w-6" />
            </div>
            <h4 className="mt-4 text-sm font-medium text-gray-900">Run agent</h4>
            <p className="mt-1 text-sm text-gray-500">Execute an AI agent on a lead</p>
          </Link>
          <Link
            to="/campaigns"
            className="bg-white shadow rounded-lg p-6 text-center hover:shadow-md transition-shadow"
          >
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
              <ChartBarIcon className="h-6 w-6" />
            </div>
            <h4 className="mt-4 text-sm font-medium text-gray-900">Create campaign</h4>
            <p className="mt-1 text-sm text-gray-500">Start a new outreach campaign</p>
          </Link>
          <Link
            to="/admin/settings"
            className="bg-white shadow rounded-lg p-6 text-center hover:shadow-md transition-shadow"
          >
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-md bg-purple-500 text-white">
              <Cog6ToothIcon className="h-6 w-6" />
            </div>
            <h4 className="mt-4 text-sm font-medium text-gray-900">Configure CRM</h4>
            <p className="mt-1 text-sm text-gray-500">Connect HubSpot or another CRM</p>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CustomerDashboard;
