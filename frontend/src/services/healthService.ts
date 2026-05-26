/**
 * Health probe — used by the layout banner to surface backend outages.
 */
import { api } from './api';

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version?: string;
}

export const healthService = {
  async check(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },
};

export default healthService;
