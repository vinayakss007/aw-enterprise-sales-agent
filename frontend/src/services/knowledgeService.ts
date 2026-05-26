/**
 * Knowledge base CRUD + retrieval-debug endpoints.
 *
 * Lives under ``/customer/knowledge/`` because each tenant has its own
 * KB — system admins can't read another tenant's entries.
 */
import { api } from './api';

export interface KnowledgeEntry {
  id: string;
  tenant_id: string;
  created_by: string | null;
  title: string;
  content: string;
  category: string | null;
  tags: string[] | null;
  source: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeCreate {
  title: string;
  content: string;
  category?: string;
  tags?: string[];
  source?: string;
  active?: boolean;
}

export interface KnowledgeUpdate {
  title?: string;
  content?: string;
  category?: string;
  tags?: string[];
  source?: string;
  active?: boolean;
}

export interface KnowledgeMatch {
  id: string;
  title: string;
  content: string;
  category: string | null;
  tags: string[] | null;
  score: number;
}

export const knowledgeService = {
  async list(params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
    category?: string;
  }): Promise<KnowledgeEntry[]> {
    const response = await api.get<KnowledgeEntry[]>('/customer/knowledge/', {
      params,
    });
    return response.data;
  },

  async get(entryId: string): Promise<KnowledgeEntry> {
    const response = await api.get<KnowledgeEntry>(
      `/customer/knowledge/${entryId}`
    );
    return response.data;
  },

  async create(payload: KnowledgeCreate): Promise<KnowledgeEntry> {
    const response = await api.post<KnowledgeEntry>(
      '/customer/knowledge/',
      payload
    );
    return response.data;
  },

  async update(
    entryId: string,
    payload: KnowledgeUpdate
  ): Promise<KnowledgeEntry> {
    const response = await api.put<KnowledgeEntry>(
      `/customer/knowledge/${entryId}`,
      payload
    );
    return response.data;
  },

  async remove(entryId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(
      `/customer/knowledge/${entryId}`
    );
    return response.data;
  },

  async lookup(
    query: string,
    limit: number = 5
  ): Promise<KnowledgeMatch[]> {
    const response = await api.get<KnowledgeMatch[]>(
      '/customer/knowledge/lookup',
      { params: { q: query, limit } }
    );
    return response.data;
  },
};

export default knowledgeService;
