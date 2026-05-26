import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  PauseIcon,
  PencilIcon,
  PlayIcon,
  PlusIcon,
  TrashIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

import { Modal } from '../../components/ui/Modal';
import campaignService from '../../services/campaignService';
import leadService from '../../services/leadService';
import type {
  Campaign,
  CampaignCreate,
  CampaignStep,
  Lead,
} from '../../types';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-blue-100 text-blue-800',
  deleted: 'bg-red-100 text-red-800',
};

const blankStep = (order: number): CampaignStep => ({
  order,
  type: 'email',
  title: 'Step ' + order,
  content: '',
  delay_days: order === 1 ? 0 : 3,
  subject: '',
});

const CampaignsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [addLeadsFor, setAddLeadsFor] = useState<Campaign | null>(null);
  const [selectedLeadIds, setSelectedLeadIds] = useState<string[]>([]);
  const [createForm, setCreateForm] = useState<CampaignCreate>({
    name: '',
    description: '',
    steps: [blankStep(1)],
  });

  const campaignsQuery = useQuery<Campaign[]>({
    queryKey: ['campaigns'],
    queryFn: () => campaignService.list({ limit: 100 }),
  });

  const leadsQuery = useQuery<Lead[]>({
    queryKey: ['leads', 'campaign-picker'],
    queryFn: () => leadService.list({ limit: 200 }),
    enabled: !!addLeadsFor,
  });

  const createMutation = useMutation({
    mutationFn: (payload: CampaignCreate) => campaignService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setCreateOpen(false);
      setCreateForm({ name: '', description: '', steps: [blankStep(1)] });
    },
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => campaignService.activate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaigns'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => campaignService.deactivate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaigns'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => campaignService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaigns'] }),
  });

  const addLeadsMutation = useMutation({
    mutationFn: ({ id, ids }: { id: string; ids: string[] }) =>
      campaignService.addLeads(id, ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setAddLeadsFor(null);
      setSelectedLeadIds([]);
    },
  });

  const handleToggle = (campaign: Campaign) => {
    if (campaign.status === 'active') {
      deactivateMutation.mutate(campaign.id);
    } else {
      activateMutation.mutate(campaign.id);
    }
  };

  const updateStep = (idx: number, patch: Partial<CampaignStep>) => {
    setCreateForm((form) => ({
      ...form,
      steps: form.steps.map((s, i) => (i === idx ? { ...s, ...patch } : s)),
    }));
  };

  const addStep = () =>
    setCreateForm((form) => ({
      ...form,
      steps: [...form.steps, blankStep(form.steps.length + 1)],
    }));

  const removeStep = (idx: number) =>
    setCreateForm((form) => ({
      ...form,
      steps: form.steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i + 1 })),
    }));

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">Campaigns</h1>
          <p className="mt-2 text-sm text-gray-700">
            Multi-step outreach campaigns. Drafts don't fire until activated.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" /> New campaign
          </button>
        </div>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {campaignsQuery.isLoading ? (
          <div className="p-12 text-center text-sm text-gray-500">Loading…</div>
        ) : campaignsQuery.data && campaignsQuery.data.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Steps
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Leads
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
              {campaignsQuery.data.map((campaign) => (
                <tr key={campaign.id} className="hover:bg-gray-50">
                  <td className="py-4 pl-4 pr-3 text-sm">
                    <div className="font-medium text-gray-900">{campaign.name}</div>
                    <div className="text-gray-500">{campaign.description}</div>
                  </td>
                  <td className="px-3 py-4 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        STATUS_COLORS[campaign.status] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {campaign.status}
                    </span>
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">
                    {campaign.steps?.length ?? 0}
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">
                    <span className="font-medium">{campaign.active_leads}</span>{' '}
                    active &nbsp;/&nbsp;
                    <span className="font-medium">{campaign.completed_leads}</span>{' '}
                    completed
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-500">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-4 pl-3 pr-4 text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        title="Add leads"
                        className="text-indigo-600 hover:text-indigo-900"
                        onClick={() => {
                          setAddLeadsFor(campaign);
                          setSelectedLeadIds([]);
                        }}
                      >
                        <UsersIcon className="h-5 w-5" />
                      </button>
                      <button
                        title={campaign.status === 'active' ? 'Pause' : 'Activate'}
                        className="text-green-600 hover:text-green-900"
                        onClick={() => handleToggle(campaign)}
                      >
                        {campaign.status === 'active' ? (
                          <PauseIcon className="h-5 w-5" />
                        ) : (
                          <PlayIcon className="h-5 w-5" />
                        )}
                      </button>
                      <button
                        title="Edit"
                        className="text-gray-600 hover:text-gray-900"
                        onClick={() =>
                          alert('Edit campaign UI is not implemented yet.')
                        }
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        title="Delete"
                        className="text-red-600 hover:text-red-900"
                        onClick={() => {
                          if (window.confirm(`Delete ${campaign.name}?`)) {
                            deleteMutation.mutate(campaign.id);
                          }
                        }}
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center">
            <p className="text-sm text-gray-500">
              No campaigns yet. Create one to get started.
            </p>
          </div>
        )}
      </div>

      <button
        type="button"
        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
        onClick={() => campaignsQuery.refetch()}
      >
        <ArrowPathIcon className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
      </button>

      {/* Create campaign modal */}
      <Modal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New campaign"
        size="2xl"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate(createForm);
          }}
          className="space-y-4"
        >
          <label className="block">
            <span className="block text-sm font-medium text-gray-700">Name</span>
            <input
              required
              type="text"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="block text-sm font-medium text-gray-700">Description</span>
            <textarea
              rows={2}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              value={createForm.description ?? ''}
              onChange={(e) =>
                setCreateForm({ ...createForm, description: e.target.value })
              }
            />
          </label>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Steps</span>
              <button
                type="button"
                onClick={addStep}
                className="text-xs text-indigo-600 hover:text-indigo-500"
              >
                + Add step
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Tip: leave content empty (or include <code>[[agent]]</code>) to have
              the AI agent draft the email per lead at send time.
            </p>
            <div className="mt-2 space-y-3">
              {createForm.steps.map((step, idx) => (
                <div key={idx} className="border rounded p-3 bg-gray-50">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <select
                      value={step.type}
                      onChange={(e) =>
                        updateStep(idx, { type: e.target.value as CampaignStep['type'] })
                      }
                      className="rounded-md border-gray-300 text-sm"
                    >
                      <option value="email">email</option>
                      <option value="call">call</option>
                      <option value="task">task</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Title"
                      value={step.title}
                      onChange={(e) => updateStep(idx, { title: e.target.value })}
                      className="rounded-md border-gray-300 text-sm"
                    />
                    <input
                      type="number"
                      min={0}
                      placeholder="Delay (days)"
                      value={step.delay_days}
                      onChange={(e) =>
                        updateStep(idx, { delay_days: Number(e.target.value) })
                      }
                      className="rounded-md border-gray-300 text-sm"
                    />
                  </div>
                  {step.type === 'email' && (
                    <input
                      type="text"
                      placeholder="Subject (supports {{first_name}})"
                      value={step.subject ?? ''}
                      onChange={(e) => updateStep(idx, { subject: e.target.value })}
                      className="mt-2 w-full rounded-md border-gray-300 text-sm"
                    />
                  )}
                  <textarea
                    rows={3}
                    placeholder="Content (or [[agent]] to use the agent)"
                    value={step.content}
                    onChange={(e) => updateStep(idx, { content: e.target.value })}
                    className="mt-2 w-full rounded-md border-gray-300 text-sm"
                  />
                  {createForm.steps.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeStep(idx)}
                      className="mt-2 text-xs text-red-600 hover:text-red-500"
                    >
                      Remove this step
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              className="px-4 py-2 text-sm border rounded-md"
              onClick={() => setCreateOpen(false)}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating…' : 'Create campaign'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Add leads modal */}
      <Modal
        isOpen={!!addLeadsFor}
        onClose={() => setAddLeadsFor(null)}
        title={`Add leads to ${addLeadsFor?.name ?? ''}`}
        size="lg"
      >
        {addLeadsFor && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              addLeadsMutation.mutate({
                id: addLeadsFor.id,
                ids: selectedLeadIds,
              });
            }}
            className="space-y-4"
          >
            {leadsQuery.isLoading ? (
              <p className="text-sm text-gray-500">Loading leads…</p>
            ) : leadsQuery.data && leadsQuery.data.length > 0 ? (
              <ul className="max-h-96 overflow-y-auto divide-y border rounded">
                {leadsQuery.data.map((lead) => (
                  <li
                    key={lead.id}
                    className="flex items-center justify-between px-3 py-2"
                  >
                    <label className="flex items-center cursor-pointer flex-1">
                      <input
                        type="checkbox"
                        className="mr-3"
                        checked={selectedLeadIds.includes(lead.id)}
                        onChange={(e) => {
                          setSelectedLeadIds((ids) =>
                            e.target.checked
                              ? [...ids, lead.id]
                              : ids.filter((i) => i !== lead.id)
                          );
                        }}
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {lead.name || lead.email}
                        </p>
                        <p className="text-xs text-gray-500">{lead.company}</p>
                      </div>
                    </label>
                    <span className="text-xs text-gray-400">{lead.status}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No leads to add yet.</p>
            )}
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded-md"
                onClick={() => setAddLeadsFor(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={selectedLeadIds.length === 0 || addLeadsMutation.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md disabled:opacity-50"
              >
                {addLeadsMutation.isPending
                  ? 'Adding…'
                  : `Add ${selectedLeadIds.length} lead${selectedLeadIds.length === 1 ? '' : 's'}`}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default CampaignsPage;
