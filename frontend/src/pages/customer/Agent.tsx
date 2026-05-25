import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';

import agentService from '../../services/agentService';
import leadService from '../../services/leadService';
import type { AgentExecution, Lead } from '../../types';

const AgentPage: React.FC = () => {
  const [selectedLeadId, setSelectedLeadId] = useState<string>('');
  const [agentType, setAgentType] = useState<'research' | 'outreach' | 'follow-up'>('research');
  const [lastRun, setLastRun] = useState<AgentExecution | null>(null);

  const queryClient = useQueryClient();

  const leadsQuery = useQuery<Lead[]>({
    queryKey: ['leads', 'agent-picker'],
    queryFn: () => leadService.list({ limit: 200 }),
  });

  const executionsQuery = useQuery<AgentExecution[]>({
    queryKey: ['agent-executions', 'history'],
    queryFn: () => agentService.listExecutions({ limit: 50 }),
  });

  const executeMutation = useMutation({
    mutationFn: () => agentService.executeAgent(selectedLeadId, agentType),
    onSuccess: (result) => {
      setLastRun(result);
      queryClient.invalidateQueries({ queryKey: ['agent-executions'] });
    },
  });

  const selectedLead = leadsQuery.data?.find((l) => l.id === selectedLeadId);

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">AI Agent</h1>
          <p className="mt-2 text-sm text-gray-700">
            Run the sales agent on a lead — research, enrich, draft, verify.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Configure</h2>
            <div className="space-y-4">
              <label className="block text-sm font-medium text-gray-700">
                Select lead
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <select
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm"
                    value={selectedLeadId}
                    onChange={(e) => setSelectedLeadId(e.target.value)}
                  >
                    <option value="">Choose…</option>
                    {leadsQuery.data?.map((lead) => (
                      <option key={lead.id} value={lead.id}>
                        {lead.name || lead.email} — {lead.company || 'no company'}
                      </option>
                    ))}
                  </select>
                </div>
              </label>

              <div>
                <span className="block text-sm font-medium text-gray-700 mb-2">
                  Agent type
                </span>
                <div className="grid grid-cols-3 gap-2">
                  {(['research', 'outreach', 'follow-up'] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setAgentType(type)}
                      className={`px-2 py-2 border rounded-md text-sm capitalize ${
                        agentType === type
                          ? 'bg-indigo-100 border-indigo-500 text-indigo-700'
                          : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                disabled={!selectedLeadId || executeMutation.isPending}
                onClick={() => executeMutation.mutate()}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
              >
                {executeMutation.isPending ? (
                  <>
                    <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                    Running…
                  </>
                ) : (
                  <>
                    <PlayIcon className="-ml-1 mr-2 h-5 w-5" /> Execute agent
                  </>
                )}
              </button>

              {executeMutation.error ? (
                <p className="text-sm text-red-600">
                  {executeMutation.error instanceof Error
                    ? executeMutation.error.message
                    : 'Agent run failed'}
                </p>
              ) : null}
            </div>
          </div>

          {selectedLead && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                Selected lead
              </h2>
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Name</dt>
                  <dd className="text-gray-900">{selectedLead.name || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Email</dt>
                  <dd className="text-gray-900">{selectedLead.email || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Company</dt>
                  <dd className="text-gray-900">{selectedLead.company || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Status</dt>
                  <dd className="text-gray-900">{selectedLead.status}</dd>
                </div>
              </dl>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Latest run</h2>
              <button
                type="button"
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
                onClick={() => executionsQuery.refetch()}
              >
                <ArrowPathIcon className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
              </button>
            </div>

            {lastRun ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-1">
                    {lastRun.draft_subject || 'Drafted email'}
                  </h3>
                  <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded border text-sm font-sans">
                    {lastRun.draft_email || '(no draft body)'}
                  </pre>
                </div>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-xs text-gray-500">Duration</p>
                    <p className="text-sm font-semibold">
                      {lastRun.completed_at && lastRun.started_at
                        ? `${(
                            (new Date(lastRun.completed_at).getTime() -
                              new Date(lastRun.started_at).getTime()) /
                            1000
                          ).toFixed(1)}s`
                        : '—'}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-xs text-gray-500">Tokens (in/out)</p>
                    <p className="text-sm font-semibold">
                      {lastRun.tokens_input} / {lastRun.tokens_output}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-xs text-gray-500">Cost</p>
                    <p className="text-sm font-semibold">
                      ${(lastRun.cost_cents / 100).toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded border">
                    <p className="text-xs text-gray-500">Status</p>
                    <p
                      className={`text-sm font-semibold ${
                        lastRun.success ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {lastRun.success ? 'Success' : 'Failed'}
                    </p>
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    Trajectory
                  </h4>
                  <ul className="text-xs space-y-1">
                    {lastRun.trajectory.map((entry, i) => (
                      <li
                        key={i}
                        className="flex justify-between bg-gray-50 px-2 py-1 rounded border"
                      >
                        <span>
                          <span className="font-mono">{entry.step}</span>
                          <span className="ml-2 text-gray-500">{entry.status}</span>
                        </span>
                        {entry.duration_ms != null && (
                          <span className="text-gray-500">
                            {entry.duration_ms}ms
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">
                  Pick a lead and run the agent to see a result here.
                </p>
              </div>
            )}
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Recent runs</h2>
            {executionsQuery.isLoading ? (
              <p className="text-sm text-gray-500">Loading…</p>
            ) : executionsQuery.data && executionsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-200">
                {executionsQuery.data.slice(0, 10).map((execution) => (
                  <li key={execution.id} className="py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-indigo-600">
                        {execution.agent_type}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                          execution.success
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {execution.success ? 'Success' : 'Failed'}
                      </span>
                    </div>
                    <div className="mt-1 flex justify-between text-xs text-gray-500">
                      <span>${(execution.cost_cents / 100).toFixed(2)}</span>
                      <span>{new Date(execution.started_at).toLocaleString()}</span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No runs yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentPage;
