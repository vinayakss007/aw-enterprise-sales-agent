import React, { useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ArrowUpTrayIcon,
  BoltIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../contexts/ToastContext';
import leadService, { ImportReport } from '../../services/leadService';
import type { Lead, LeadCreate, LeadUpdate } from '../../types';

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
  archived: 'bg-red-100 text-red-800',
};

const emptyForm: LeadCreate = {
  email: '',
  name: '',
  company: '',
  domain: '',
  title: '',
  linkedin_url: '',
  phone: '',
};

const LeadFormFields: React.FC<{
  values: LeadCreate;
  onChange: (next: LeadCreate) => void;
}> = ({ values, onChange }) => (
  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
    {(
      [
        ['name', 'Name'],
        ['email', 'Email'],
        ['company', 'Company'],
        ['domain', 'Domain'],
        ['title', 'Title'],
        ['phone', 'Phone'],
      ] as const
    ).map(([field, label]) => (
      <label key={field} className="block">
        <span className="block text-sm font-medium text-gray-700">{label}</span>
        <input
          type="text"
          value={values[field] ?? ''}
          onChange={(e) => onChange({ ...values, [field]: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </label>
    ))}
    <label className="block sm:col-span-2">
      <span className="block text-sm font-medium text-gray-700">LinkedIn URL</span>
      <input
        type="text"
        value={values.linkedin_url ?? ''}
        onChange={(e) => onChange({ ...values, linkedin_url: e.target.value })}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
      />
    </label>
  </div>
);

const LeadsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Lead | null>(null);
  const [archiveCandidate, setArchiveCandidate] = useState<Lead | null>(null);
  const [importReport, setImportReport] = useState<ImportReport | null>(null);
  const [createForm, setCreateForm] = useState<LeadCreate>(emptyForm);
  const [editForm, setEditForm] = useState<LeadUpdate>({});

  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const leadsQuery = useQuery<Lead[]>({
    queryKey: ['leads', 'all'],
    queryFn: () => leadService.list({ limit: 200 }),
  });

  const filteredLeads = useMemo(() => {
    if (!leadsQuery.data) return [];
    const term = searchTerm.trim().toLowerCase();
    return leadsQuery.data.filter((lead) => {
      if (statusFilter !== 'all' && lead.status !== statusFilter) return false;
      if (!term) return true;
      return (
        (lead.name || '').toLowerCase().includes(term) ||
        (lead.email || '').toLowerCase().includes(term) ||
        (lead.company || '').toLowerCase().includes(term)
      );
    });
  }, [leadsQuery.data, searchTerm, statusFilter]);

  const createMutation = useMutation({
    mutationFn: (payload: LeadCreate) => leadService.create(payload),
    onSuccess: (lead) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setCreateOpen(false);
      setCreateForm(emptyForm);
      toast(`Created ${lead.name || lead.email || 'lead'}`, 'success');
    },
    onError: (err: unknown) => {
      toast(
        err instanceof Error ? err.message : 'Failed to create lead',
        'error'
      );
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: LeadUpdate }) =>
      leadService.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setEditing(null);
      setEditForm({});
      toast('Lead updated', 'success');
    },
    onError: (err: unknown) => {
      toast(
        err instanceof Error ? err.message : 'Failed to update lead',
        'error'
      );
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => leadService.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setArchiveCandidate(null);
      toast('Lead archived', 'success');
    },
    onError: (err: unknown) => {
      toast(
        err instanceof Error ? err.message : 'Failed to archive lead',
        'error'
      );
    },
  });

  const enrichMutation = useMutation({
    mutationFn: (id: string) => leadService.enrich(id),
    onSuccess: (lead) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      const provider = (lead.enriched_data as Record<string, unknown> | undefined)
        ?.provider;
      toast(
        `Enriched ${lead.name || lead.email || 'lead'}${
          provider ? ` via ${provider}` : ''
        }`,
        'success'
      );
    },
    onError: (err: unknown) => {
      toast(
        err instanceof Error ? err.message : 'Enrichment failed',
        'error'
      );
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => leadService.importCsv(file),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setImportReport(report);
      const errorSummary = report.errors.length
        ? `, ${report.errors.length} error${report.errors.length === 1 ? '' : 's'}`
        : '';
      toast(
        `CSV import: +${report.created} created, ${report.updated} updated, ${report.skipped} skipped${errorSummary}`,
        report.errors.length ? 'warning' : 'success'
      );
    },
    onError: (err: unknown) => {
      toast(
        err instanceof Error ? err.message : 'CSV import failed',
        'error'
      );
    },
  });

  const handleExport = async () => {
    try {
      const blob = await leadService.exportCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast('Lead CSV downloaded', 'success');
    } catch (err) {
      toast(
        err instanceof Error ? err.message : 'CSV export failed',
        'error'
      );
    }
  };

  const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // allow re-picking the same file later
    if (!file) return;
    importMutation.mutate(file);
  };

  const openEdit = (lead: Lead) => {
    setEditing(lead);
    setEditForm({
      name: lead.name,
      email: lead.email,
      company: lead.company,
      domain: lead.domain,
      title: lead.title,
      phone: lead.phone,
      linkedin_url: lead.linkedin_url,
      status: lead.status,
    });
  };

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-xl font-semibold text-gray-900">Leads</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage and track sales leads for your tenant. Import / export CSV,
            and run the configured enrichment provider per lead.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowDownTrayIcon className="-ml-1 mr-2 h-5 w-5" />
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={importMutation.isPending}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <ArrowUpTrayIcon className="-ml-1 mr-2 h-5 w-5" />
            {importMutation.isPending ? 'Importing…' : 'Import CSV'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFilePick}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" /> Add lead
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-grow">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm"
            placeholder="Search leads…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block sm:w-48 pl-3 pr-10 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="all">All statuses</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="qualified">Qualified</option>
          <option value="closed">Closed</option>
          <option value="archived">Archived</option>
        </select>
        <button
          type="button"
          onClick={() => leadsQuery.refetch()}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowPathIcon className="-ml-0.5 mr-2 h-4 w-4" /> Refresh
        </button>
      </div>

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        {leadsQuery.isLoading ? (
          <div className="p-12 text-center text-sm text-gray-500">Loading…</div>
        ) : leadsQuery.isError ? (
          <div className="p-12 text-center text-red-600">
            Failed to load leads. Try refreshing.
          </div>
        ) : filteredLeads.length === 0 ? (
          <div className="p-12 text-center text-sm text-gray-500">
            No leads match those filters.
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Company
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Title
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Email
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-3 py-3.5 text-left text-xs font-medium text-gray-500 uppercase">
                  Enrichment
                </th>
                <th className="relative py-3.5 pl-3 pr-4">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredLeads.map((lead) => {
                const provider = (
                  lead.enriched_data as Record<string, unknown> | undefined
                )?.provider as string | undefined;
                const confidence = (
                  lead.enriched_data as Record<string, unknown> | undefined
                )?.confidence as number | undefined;
                const enriching =
                  enrichMutation.isPending &&
                  enrichMutation.variables === lead.id;
                return (
                  <tr key={lead.id} className="hover:bg-gray-50">
                    <td className="py-4 pl-4 pr-3 text-sm">
                      <div className="font-medium text-gray-900">
                        {lead.name || '(no name)'}
                      </div>
                      <div className="text-gray-500">{lead.domain}</div>
                    </td>
                    <td className="px-3 py-4 text-sm text-gray-700">{lead.company}</td>
                    <td className="px-3 py-4 text-sm text-gray-700">{lead.title}</td>
                    <td className="px-3 py-4 text-sm text-gray-700">{lead.email}</td>
                    <td className="px-3 py-4 text-sm">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          STATUS_COLORS[lead.status] || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {lead.status}
                      </span>
                    </td>
                    <td className="px-3 py-4 text-xs text-gray-500">
                      {provider ? (
                        <>
                          <span className="font-mono">{provider}</span>
                          {typeof confidence === 'number' && (
                            <span className="ml-2">
                              ({Math.round(confidence * 100)}%)
                            </span>
                          )}
                        </>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-4 pl-3 pr-4 text-right text-sm font-medium">
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          title="Enrich"
                          className="text-amber-600 hover:text-amber-900 disabled:opacity-50"
                          onClick={() => enrichMutation.mutate(lead.id)}
                          disabled={enriching}
                        >
                          <BoltIcon
                            className={`h-5 w-5 ${enriching ? 'animate-pulse' : ''}`}
                          />
                        </button>
                        <button
                          type="button"
                          title="Edit"
                          className="text-indigo-600 hover:text-indigo-900"
                          onClick={() => openEdit(lead)}
                        >
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button
                          type="button"
                          title="Archive"
                          className="text-red-600 hover:text-red-900"
                          onClick={() => setArchiveCandidate(lead)}
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Create modal */}
      <Modal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Add lead"
        size="lg"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate(createForm);
          }}
          className="space-y-4"
        >
          <LeadFormFields values={createForm} onChange={setCreateForm} />
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
              {createMutation.isPending ? 'Creating…' : 'Create lead'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit modal */}
      <Modal
        isOpen={!!editing}
        onClose={() => setEditing(null)}
        title={`Edit ${editing?.name || editing?.email || ''}`}
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
            <LeadFormFields values={editForm as LeadCreate} onChange={(v) => setEditForm(v)} />
            <label className="block">
              <span className="block text-sm font-medium text-gray-700">Status</span>
              <select
                value={editForm.status || ''}
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="closed">Closed</option>
              </select>
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

      {/* Archive confirm modal — replaces window.confirm */}
      <Modal
        isOpen={!!archiveCandidate}
        onClose={() => setArchiveCandidate(null)}
        title="Archive lead"
      >
        {archiveCandidate && (
          <div className="space-y-4">
            <p className="text-sm text-gray-700">
              Archive{' '}
              <strong>{archiveCandidate.name || archiveCandidate.email}</strong>?
              This sets the status to ``archived``; the row stays in the
              database but is hidden from the default view.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded-md"
                onClick={() => setArchiveCandidate(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => archiveMutation.mutate(archiveCandidate.id)}
                disabled={archiveMutation.isPending}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-md disabled:opacity-50"
              >
                {archiveMutation.isPending ? 'Archiving…' : 'Archive lead'}
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Import report modal — surfaces row-level errors when present */}
      <Modal
        isOpen={!!importReport}
        onClose={() => setImportReport(null)}
        title="CSV import results"
      >
        {importReport && (
          <div className="space-y-3 text-sm">
            <ul className="grid grid-cols-2 gap-2">
              <li>
                Created: <strong>{importReport.created}</strong>
              </li>
              <li>
                Updated: <strong>{importReport.updated}</strong>
              </li>
              <li>
                Skipped: <strong>{importReport.skipped}</strong>
              </li>
              <li>
                Errors: <strong>{importReport.errors.length}</strong>
              </li>
            </ul>
            {importReport.errors.length > 0 && (
              <div>
                <p className="font-medium">Row errors:</p>
                <ul className="list-disc list-inside text-xs text-red-700 max-h-48 overflow-y-auto">
                  {importReport.errors.map((e, i) => (
                    <li key={i}>
                      Row {e.row}: {e.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded-md"
                onClick={() => setImportReport(null)}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default LeadsPage;
