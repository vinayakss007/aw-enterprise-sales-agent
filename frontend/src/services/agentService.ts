/**
 * Agent execute / history + CRM convenience endpoints.
 *
 * ``executeAgent`` posts ``agent_type`` as a query parameter to match the
 * backend signature (the route uses ``Query("research")`` not a body field).
 * ``listExecutions`` returns a flat array because the backend returns a
 * list, not an envelope.
 */
import { api } from './api';
import type { AgentExecution } from '../types';

export const agentService = {
  async executeAgent(leadId: string, agentType: string = 'research'): Promise<AgentExecution> {
    const response = await api.post<AgentExecution>(
      `/customer/agent/execute/${leadId}`,
      null,
      { params: { agent_type: agentType } }
    );
    return response.data;
  },

  async listExecutions(params?: { skip?: number; limit?: number }): Promise<AgentExecution[]> {
    const response = await api.get<AgentExecution[]>('/customer/agent/executions', { params });
    return response.data;
  },

  async getExecution(executionId: string): Promise<AgentExecution> {
    const response = await api.get<AgentExecution>(`/customer/agent/executions/${executionId}`);
    return response.data;
  },

  async syncLeadToCrm(leadId: string): Promise<{ contact_id: string | null }> {
    const response = await api.post(`/customer/crm/sync/${leadId}`);
    return response.data;
  },

  async createCrmNote(contactId: string, content: string): Promise<{ note_id: string | null }> {
    const response = await api.post(`/customer/crm/note/${contactId}`, { content });
    return response.data;
  },
};

export default agentService;
