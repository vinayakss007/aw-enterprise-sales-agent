// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'owner' | 'admin' | 'user' | 'viewer';
  tenant_id: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

// Lead Types
export interface Lead {
  id: string;
  tenant_id: string;
  user_id: string;
  email?: string;
  name?: string;
  company?: string;
  domain?: string;
  title?: string;
  linkedin_url?: string;
  phone?: string;
  status: string;
  source: string;
  enriched_data?: Record<string, unknown>;
  crm_contact_id?: string;
  crm_account_id?: string;
  created_at: string;
  updated_at: string;
}

export interface LeadCreate {
  email?: string;
  name?: string;
  company?: string;
  domain?: string;
  title?: string;
  linkedin_url?: string;
  phone?: string;
  source?: string;
}

export interface LeadUpdate {
  email?: string;
  name?: string;
  company?: string;
  domain?: string;
  title?: string;
  linkedin_url?: string;
  phone?: string;
  status?: string;
}

// Agent Types — trajectory matches the backend's TrajectoryEntry shape
export interface TrajectoryEntry {
  step: string;
  status: 'started' | 'completed' | 'failed' | 'skipped';
  started_at?: number;
  completed_at?: number;
  duration_ms?: number;
  details?: Record<string, unknown>;
  tokens_input?: number;
  tokens_output?: number;
  cost_cents?: number;
  model?: string;
  error?: string;
}

export interface AgentExecution {
  id: string;
  tenant_id: string;
  user_id: string;
  lead_id: string;
  agent_type: string;
  trajectory: TrajectoryEntry[];
  success: boolean;
  tokens_input: number;
  tokens_output: number;
  cost_cents: number;
  draft_subject?: string | null;
  draft_email?: string | null;
  error?: string | null;
  started_at: string;
  completed_at: string;
  created_at: string;
  updated_at: string;
}

// Campaign Types
export type CampaignStatus = 'draft' | 'active' | 'paused' | 'completed' | 'deleted';

export interface CampaignStep {
  order: number;
  type: 'email' | 'call' | 'task';
  title: string;
  content: string;
  delay_days: number;
  subject?: string;
}

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: CampaignStatus;
  steps: CampaignStep[];
  created_at: string;
  updated_at: string;
  active_leads: number;
  completed_leads: number;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  steps: CampaignStep[];
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  status?: CampaignStatus;
}

// Tenant Types
export interface Tenant {
  id: string;
  name: string;
  subdomain?: string;
  plan: string;
  status: string;
  config?: Record<string, unknown>;
  limits?: Record<string, unknown>;
  billing_email?: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

// Usage Metrics Types
export interface UsageMetricsPoint {
  date: string;
  value: number;
  active_tenants: number;
  cost: number;
}

export interface UsageMetrics {
  date_range: [string, string];
  granularity: string;
  metrics: UsageMetricsPoint[];
  totals: {
    total_usage: number;
    total_cost: number;
    total_tenants: number;
    total_users: number;
    total_tasks: number;
  };
}

// Auth Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  name: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Worker tick result
export interface WorkerTickResult {
  processed: number;
  advanced: number;
  completed: number;
  failed: number;
  skipped: number;
  emails_sent: number;
  agent_runs: number;
  errors: string[];
}

// Common Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}
