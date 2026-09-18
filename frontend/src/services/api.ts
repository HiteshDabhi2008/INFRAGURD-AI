import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ProjectSummary {
  project_code: string;
  project_name: string;
  agency?: string;
  state?: string;
  sector?: string;
  ministry?: string;
  original_cost?: number;
  revised_cost?: number;
  cumulative_expenditure?: number;
  physical_progress?: number;
  overall_risk?: string;
  risk_score?: number;
  warnings?: string[];
}

export interface ProjectDetail extends ProjectSummary {
  approval_date?: string;
  original_completion_date?: string;
  history: Array<{
    id: number;
    report_month: string;
    revised_cost?: number;
    revised_completion_date?: string;
    cumulative_expenditure?: number;
    physical_progress?: number;
  }>;
}

export const projectApi = {
  list: (params: Record<string, string | number | undefined> = {}) => api.get<{ projects: ProjectSummary[]; total: number }>('/api/projects', { params }),
  search: (q: string) => api.get<ProjectSummary[]>('/api/projects/search', { params: { q } }),
  detail: (id: string) => api.get<ProjectDetail>(`/api/projects/${encodeURIComponent(id)}`),
  history: (id: string) => api.get<ProjectDetail['history']>(`/api/projects/${encodeURIComponent(id)}/history`),
  costPrediction: (id: string) => api.post(`/api/ml/cost/predict`, { project_id: id }),
  timePrediction: (id: string) => api.post(`/api/ml/time/predict`, { project_id: id }),
  riskPrediction: (id: string) => api.post(`/api/risk/predict`, { project_id: id }),
};

export const analyticsApi = {
  overview: () => api.get('/api/analytics/overview'),
  ministry: () => api.get('/api/analytics/ministry'),
  sector: () => api.get('/api/analytics/sector'),
  state: () => api.get('/api/analytics/state'),
  agency: () => api.get('/api/analytics/agency'),
};

export const aiApi = {
  chat: (message: string, project_code?: string) => api.post('/api/ai/chat', { message, project_code }),
};

export default api;
