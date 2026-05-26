import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import adminService from '../../services/adminService';
import type { WorkerTickResult } from '../../types';

const SettingsPage: React.FC = () => {
  const [lastTick, setLastTick] = useState<WorkerTickResult | null>(null);

  const tickMutation = useMutation({
    mutationFn: () => adminService.tickCampaignWorker(100),
    onSuccess: (result) => setLastTick(result),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-700">
          Operations actions for your tenant.
        </p>
      </div>

      <section className="bg-white shadow rounded-lg p-6 space-y-4">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Campaign worker</h2>
          <p className="mt-1 text-sm text-gray-600">
            Trigger one tick of the campaign worker now (scoped to your tenant).
            The standalone worker process processes campaigns automatically;
            this is for testing and incident response.
          </p>
        </div>
        <button
          type="button"
          disabled={tickMutation.isPending}
          onClick={() => tickMutation.mutate()}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
        >
          {tickMutation.isPending ? 'Running…' : 'Tick worker now'}
        </button>

        {lastTick && (
          <div className="mt-4 rounded-md bg-gray-50 p-4 text-sm">
            <h3 className="font-semibold text-gray-900 mb-2">Last result</h3>
            <ul className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-gray-700">
              <li>processed: <strong>{lastTick.processed}</strong></li>
              <li>advanced: <strong>{lastTick.advanced}</strong></li>
              <li>completed: <strong>{lastTick.completed}</strong></li>
              <li>failed: <strong>{lastTick.failed}</strong></li>
              <li>skipped: <strong>{lastTick.skipped}</strong></li>
              <li>emails sent: <strong>{lastTick.emails_sent}</strong></li>
              <li>agent runs: <strong>{lastTick.agent_runs}</strong></li>
              <li>errors: <strong>{lastTick.errors.length}</strong></li>
            </ul>
            {lastTick.errors.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-gray-500">First few errors:</p>
                <ul className="list-disc list-inside text-xs text-red-700">
                  {lastTick.errors.slice(0, 5).map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {tickMutation.error ? (
          <p className="text-sm text-red-600">
            {tickMutation.error instanceof Error
              ? tickMutation.error.message
              : 'Tick failed'}
          </p>
        ) : null}
      </section>
    </div>
  );
};

export default SettingsPage;
