import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeftIcon,
  BoltIcon,
  ChartBarIcon,
  EnvelopeIcon,
  PhoneIcon,
  BuildingOfficeIcon,
  GlobeAltIcon,
  UserIcon,
  ClockIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';

import { useToast } from '../../contexts/ToastContext';
import leadService, { LeadActivity } from '../../services/leadService';
import type { Lead } from '../../types';

const ACTIVITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  email: EnvelopeIcon,
  enrichment: BoltIcon,
  score: ChartBarIcon,
  call: PhoneIcon,
  default: ClockIcon,
};

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
  archived: 'bg-red-100 text-red-800',
};

const ActivityCard: React.FC<{ activity: LeadActivity }> = ({ activity }) => {
  const [expanded, setExpanded] = useState(false);
  const Icon = ACTIVITY_ICONS[activity.type] || ACTIVITY_ICONS.default;

  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100">
          <Icon className="h-4 w-4 text-indigo-600" />
        </div>
        <div className="flex-1 w-px bg-gray-200" />
      </div>
      <div className="flex-1 pb-6">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-900">{activity.summary}</p>
          <time className="text-xs text-gray-500">
            {new Date(activity.timestamp).toLocaleString()}
          </time>
        </div>
        <p className="mt-0.5 text-xs text-gray-500 capitalize">{activity.type}</p>
        {activity.details && Object.keys(activity.details).length > 0 && (
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center text-xs text-indigo-600 hover:text-indigo-800"
            >
              {expanded ? (
                <>
                  Hide details <ChevronUpIcon className="ml-1 h-3 w-3" />
                </>
              ) : (
                <>
                  Show details <ChevronDownIcon className="ml-1 h-3 w-3" />
                </>
              )}
            </button>
            {expanded && (
              <pre className="mt-2 rounded bg-gray-50 p-3 text-xs text-gray-700 overflow-x-auto">
                {JSON.stringify(activity.details, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const LeadDetailPage: React.FC = () => {
  const { leadId } = useParams<{ leadId: string }>();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const leadQuery = useQuery<Lead>({
    queryKey: ['lead', leadId],
    queryFn: () => leadService.get(leadId!),
    enabled: !!leadId,
  });

  const activityQuery = useQuery<LeadActivity[]>({
    queryKey: ['lead', leadId, 'activity'],
    queryFn: () => leadService.getActivity(leadId!),
    enabled: !!leadId,
  });

  const enrichMutation = useMutation({
    mutationFn: () => leadService.enrich(leadId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
      queryClient.invalidateQueries({ queryKey: ['lead', leadId, 'activity'] });
      toast('Lead enriched successfully', 'success');
    },
    onError: () => toast('Enrichment failed', 'error'),
  });

  const scoreMutation = useMutation({
    mutationFn: () => leadService.score(leadId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
      queryClient.invalidateQueries({ queryKey: ['lead', leadId, 'activity'] });
      toast('Lead scored successfully', 'success');
    },
    onError: () => toast('Scoring failed', 'error'),
  });

  const lead = leadQuery.data;

  if (leadQuery.isLoading) {
    return <div className="p-12 text-center text-gray-500">Loading lead...</div>;
  }

  if (leadQuery.isError || !lead) {
    return (
      <div className="p-12 text-center text-red-600">
        Failed to load lead.{' '}
        <Link to="/leads" className="text-indigo-600 underline">
          Back to leads
        </Link>
      </div>
    );
  }

  const enrichedData = lead.enriched_data as Record<string, unknown> | undefined;
  const leadScore = enrichedData?.lead_score as number | undefined;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            to="/leads"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="mr-1 h-4 w-4" />
            Back
          </Link>
          <h1 className="text-xl font-semibold text-gray-900">
            {lead.name || lead.email || 'Lead Detail'}
          </h1>
          <span
            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
              STATUS_COLORS[lead.status] || 'bg-gray-100 text-gray-800'
            }`}
          >
            {lead.status}
          </span>
        </div>
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={() => enrichMutation.mutate()}
            disabled={enrichMutation.isPending}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <BoltIcon className="mr-2 h-4 w-4" />
            {enrichMutation.isPending ? 'Enriching...' : 'Enrich'}
          </button>
          <button
            type="button"
            onClick={() => scoreMutation.mutate()}
            disabled={scoreMutation.isPending}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <ChartBarIcon className="mr-2 h-4 w-4" />
            {scoreMutation.isPending ? 'Scoring...' : 'Score'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lead Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Lead Information</h2>
            <div className="space-y-3">
              {lead.name && (
                <div className="flex items-center text-sm">
                  <UserIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-900">{lead.name}</span>
                </div>
              )}
              {lead.email && (
                <div className="flex items-center text-sm">
                  <EnvelopeIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-900">{lead.email}</span>
                </div>
              )}
              {lead.company && (
                <div className="flex items-center text-sm">
                  <BuildingOfficeIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-900">{lead.company}</span>
                </div>
              )}
              {lead.domain && (
                <div className="flex items-center text-sm">
                  <GlobeAltIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-900">{lead.domain}</span>
                </div>
              )}
              {lead.title && (
                <div className="flex items-center text-sm">
                  <UserIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-500">Title:</span>
                  <span className="ml-1 text-gray-900">{lead.title}</span>
                </div>
              )}
              {lead.phone && (
                <div className="flex items-center text-sm">
                  <PhoneIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-900">{lead.phone}</span>
                </div>
              )}
            </div>

            {/* Lead Score */}
            {typeof leadScore === 'number' && (
              <div className="border-t pt-4">
                <p className="text-sm text-gray-500">Lead Score</p>
                <div className="mt-1 flex items-center">
                  <div className="text-2xl font-bold text-indigo-600">
                    {Math.round(leadScore)}
                  </div>
                  <span className="ml-1 text-sm text-gray-500">/ 100</span>
                </div>
              </div>
            )}

            {/* Enrichment Data */}
            {enrichedData && Object.keys(enrichedData).length > 0 && (
              <div className="border-t pt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Enrichment Data</p>
                <pre className="rounded bg-gray-50 p-3 text-xs text-gray-700 overflow-x-auto max-h-60">
                  {JSON.stringify(enrichedData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Activity Timeline</h2>
            {activityQuery.isLoading ? (
              <div className="text-sm text-gray-500">Loading activity...</div>
            ) : activityQuery.isError ? (
              <div className="text-sm text-red-600">Failed to load activity.</div>
            ) : !activityQuery.data || activityQuery.data.length === 0 ? (
              <div className="text-sm text-gray-500">No activity recorded yet.</div>
            ) : (
              <div className="space-y-0">
                {activityQuery.data.map((activity) => (
                  <ActivityCard key={activity.id} activity={activity} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LeadDetailPage;
