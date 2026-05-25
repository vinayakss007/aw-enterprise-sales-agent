import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  PlusIcon,
  SparklesIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import knowledgeService, {
  KnowledgeCreate,
  KnowledgeEntry,
  KnowledgeMatch,
  KnowledgeUpdate,
} from '../../services/knowledgeService';

const emptyForm: KnowledgeCreate = {
  title: '',
  content: '',
  category: '',
  tags: [],
  source: '',
  active: true,
};

const KnowledgeFormFields: React.FC<{
  values: KnowledgeCreate;
  onChange: (next: KnowledgeCreate) => void;
}> = ({ values, onChange }) => (
  <div className="space-y-3">
    <label className="block">
      <span className="block text-sm font-medium text-gray-700">Title</span>
      <input
        required
        type="text"
        value={values.title}
        onChange={(e) => onChange({ ...values, title: e.target.value })}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
      />
    </label>
    <label className="block">
      <span className="block text-sm font-medium text-gray-700">Content</span>
      <textarea
        required
        rows={6}
        value={values.content}
        onChange={(e) => onChange({ ...values, content: e.target.value })}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
      />
    </label>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <label className="block">
        <span className="block text-sm font-medium text-gray-700">Category</span>
        <input
          type="text"
          value={values.category ?? ''}
          onChange={(e) => onChange({ ...values, category: e.target.value })}
          placeholder="e.g. pricing, objection, faq"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </label>
      <label className="block">
        <span className="block text-sm font-medium text-gray-700">Source</span>
        <input
          type="text"
          value={values.source ?? ''}
          onChange={(e) => onChange({ ...values, source: e.target.value })}
          placeholder="url or note about origin"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </label>
    </div>
    <label className="block">
      <span className="block text-sm font-medium text-gray-700">
        Tags (comma-separated)
      </span>
      <input
        type="text"
        value={(values.tags ?? []).join(', ')}
        onChange={(e) =>
          onChange({
            ...values,
            tags: e.target.value
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean),
          })
        }
        placeholder="pricing, enterprise"
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
      />
    </label>
  </div>
);

const KnowledgePage: React.FC = () => {
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeEntry | null>(null);
  const [createForm, setCreateForm] = useState<KnowledgeCreate>(emptyForm);
  const [editForm, setEditForm] = useState<KnowledgeUpdate>({});
  const [lookupQuery, setLookupQuery] = useState('');
  const [lookupResults, setLookupResults] = useState<KnowledgeMatch[] | null>(
    null
  );

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const entriesQuery = useQuery<KnowledgeEntry[]>({
    queryKey: ['knowledge', 'all'],
    queryFn: () => knowledgeService.list({ limit: 200, active_only: false }),
  });

  const createMutation = useMutation({
    mutationFn: (payload: KnowledgeCreate) => knowledgeService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
      setCreateOpen(false);
      setCreateForm(emptyForm);
      toast('Knowledge entry created', 'success');
    },
    onError: (err: unknown) => {
      toast(err instanceof Error ? err.message : 'Create failed', 'error');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: KnowledgeUpdate }) =>
      knowledgeService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
      setEditing(null);
      setEditForm({});
      toast('Knowledge entry updated', 'success');
    },
    onError: (err: unknown) => {
      toast(err instanceof Error ? err.message : 'Update failed', 'error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => knowledgeService.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
      toast('Knowledge entry archived', 'success');
    },
    onError: (err: unknown) => {
      toast(err instanceof Error ? err.message : 'Delete failed', 'error');
    },
  });

  const lookupMutation = useMutation({
    mutationFn: (query: string) => knowledgeService.lookup(query, 5),
    onSuccess: (matches) => {
      setLookupResults(matches);
      if (matches.length === 0) {
        toast('No matches for that query', 'info');
      }
    },
    onError: (err: unknown) => {
      toast(err instanceof Error ? err.message : 'Lookup failed', 'error');
    },
  });

  const openEdit = (entry: KnowledgeEntry) => {
    setEditing(entry);
    setEditForm({
      title: entry.title,
      content: entry.content,
      category: entry.category ?? '',
      tags: entry.tags ?? [],
      source: entry.source ?? '',
      active: entry.active,
    });
  };

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">Knowledge base</h1>
          <p className="mt-2 text-sm text-gray-700">
            Talking points, pricing notes, objection handlers — anything the
            agent should pull from when drafting outreach. The agent
            keyword-searches this on every run.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" /> New entry
          </button>
        </div>
      </div>

      {/* Lookup playground */}
      <div className="bg-white shadow rounded-lg p-4 space-y-3">
        <div className="flex items-center space-x-2">
          <SparklesIcon className="h-5 w-5 text-indigo-500" />
          <h2 className="text-sm font-medium text-gray-900">
            Try the agent's retrieval
          </h2>
        </div>
        <p className="text-xs text-gray-500">
          Run the same keyword search the agent uses. Helpful for debugging
          why the agent picked a particular talking point.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const q = lookupQuery.trim();
            if (!q) return;
            lookupMutation.mutate(q);
          }}
          className="flex gap-2"
        >
          <div className="relative flex-grow">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={lookupQuery}
              onChange={(e) => setLookupQuery(e.target.value)}
              placeholder="e.g. enterprise pricing"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={lookupMutation.isPending || !lookupQuery.trim()}
            className="px-4 py-2 text-sm border rounded-md disabled:opacity-50"
          >
            {lookupMutation.isPending ? 'Searching…' : 'Search'}
          </button>
        </form>
        {lookupResults && lookupResults.length > 0 && (
          <ul className="text-sm divide-y border rounded">
            {lookupResults.map((m) => (
              <li key={m.id} className="px-3 py-2 flex justify-between">
                <div>
                  <div className="font-medium">{m.title}</div>
                  <div className="text-xs text-gray-500 truncate max-w-md">
                    {m.content.slice(0, 140)}
                  </div>
                </div>
                <span className="text-xs text-gray-400">
                  score {m.score.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {entriesQuery.isLoading ? (
          <div className="p-12 text-center text-sm text-gray-500">Loading…</div>
        ) : entriesQuery.data && entriesQuery.data.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Title
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Category
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Tags
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Active
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Updated
                </th>
                <th className="relative py-3.5 pl-3 pr-4">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {entriesQuery.data.map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="py-4 pl-4 pr-3 text-sm">
                    <div className="font-medium text-gray-900">{entry.title}</div>
                    <div className="text-xs text-gray-500 truncate max-w-md">
                      {entry.content.slice(0, 120)}
                    </div>
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-700">
                    {entry.category ?? '—'}
                  </td>
                  <td className="px-3 py-4 text-xs text-gray-600">
                    {(entry.tags || []).join(', ') || '—'}
                  </td>
                  <td className="px-3 py-4 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        entry.active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {entry.active ? 'active' : 'archived'}
                    </span>
                  </td>
                  <td className="px-3 py-4 text-xs text-gray-500">
                    {new Date(entry.updated_at).toLocaleString()}
                  </td>
                  <td className="py-4 pl-3 pr-4 text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        type="button"
                        title="Edit"
                        className="text-indigo-600 hover:text-indigo-900"
                        onClick={() => openEdit(entry)}
                      >
                        <PencilIcon className="h-5 w-5" />
                      </button>
                      <button
                        type="button"
                        title="Archive"
                        className="text-red-600 hover:text-red-900 disabled:opacity-30"
                        onClick={() => deleteMutation.mutate(entry.id)}
                        disabled={!entry.active}
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
          <div className="p-12 text-center text-sm text-gray-500">
            No knowledge entries yet — add one to give the agent context.
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => entriesQuery.refetch()}
        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
      >
        <ArrowPathIcon className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
      </button>

      {/* Create modal */}
      <Modal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New knowledge entry"
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate(createForm);
          }}
          className="space-y-4"
        >
          <KnowledgeFormFields values={createForm} onChange={setCreateForm} />
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
              {createMutation.isPending ? 'Creating…' : 'Create entry'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit modal */}
      <Modal
        isOpen={!!editing}
        onClose={() => setEditing(null)}
        title="Edit entry"
        size="lg"
      >
        {editing && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateMutation.mutate({ id: editing.id, payload: editForm });
            }}
            className="space-y-4"
          >
            <KnowledgeFormFields
              values={editForm as KnowledgeCreate}
              onChange={(v) => setEditForm(v)}
            />
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={editForm.active ?? true}
                onChange={(e) =>
                  setEditForm({ ...editForm, active: e.target.checked })
                }
              />
              <span>Active (uncheck to archive)</span>
            </label>
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded-md"
                onClick={() => setEditing(null)}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md disabled:opacity-50"
              >
                {updateMutation.isPending ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default KnowledgePage;
