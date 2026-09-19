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
  department?: string;
  district?: string;
  location?: string;
  status?: string;
  original_cost?: number;
  revised_cost?: number;
  cumulative_expenditure?: number;
  physical_progress?: number;
  overall_risk?: string;
  risk_score?: number;
  warnings?: string[];
  created_at?: string;
  created_by?: string;
  approval_date?: string;
  original_completion_date?: string;
}

export interface ProjectHistoryItem {
  id: number;
  report_month: string;
  revised_cost?: number;
  revised_completion_date?: string;
  cumulative_expenditure?: number;
  physical_progress?: number;
  cost_overrun_pct?: number;
  time_overrun_months?: number;
}

export interface RiskPredictionResult {
  project_code: string;
  risk_score: number;
  overall_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  warnings: string[];
  explanation: string;
  cost_model_output: {
    risk_level: string;
    expected_overrun_percent: number;
    is_cost_overrun: boolean;
    predicted_total_cost?: number;
  };
  time_model_output: {
    risk_level: string;
    overrun_probability: number;
    expected_overrun_months: number | null;
    is_time_overrun: boolean;
  };
}

export interface ProjectDetail extends ProjectSummary {
  approval_date?: string;
  original_completion_date?: string;
  history: ProjectHistoryItem[];
}

export const projectApi = {
  list: (params: Record<string, string | number | undefined> = {}) => api.get<{ projects: ProjectSummary[]; total: number }>('/api/projects', { params }),
  search: (q: string) => api.get<ProjectSummary[]>('/api/projects/search', { params: { q } }),
  detail: (id: string) => api.get<ProjectDetail>(`/api/projects/${encodeURIComponent(id)}`),
  history: (id: string) => api.get<ProjectHistoryItem[]>(`/api/projects/${encodeURIComponent(id)}/history`),
  costPrediction: (id: string) => api.post(`/api/ml/cost/predict`, { project_id: id }),
  timePrediction: (id: string) => api.post(`/api/ml/time/predict`, { project_id: id }),
  riskPrediction: (id: string) => api.post<RiskPredictionResult>(`/api/risk/predict`, { project_id: id }),
  monthlyUpdate: (code: string, payload: MonthlyUpdatePayload) =>
    api.post<MonthlyUpdateResponse>(`/api/projects/${encodeURIComponent(code)}/monthly-update`, payload),
  getSnapshot: (code: string, reportMonth: string) =>
    api.get<{ exists: boolean; snapshot: any }>(`/api/projects/${encodeURIComponent(code)}/snapshot/${encodeURIComponent(reportMonth)}`),
  checkDuplicate: (project_code: string, project_name?: string) =>
    api.get<DuplicateCheckResult>('/api/projects/check-duplicate', { params: { project_code, project_name } }),
  create: (payload: CreateProjectPayload) =>
    api.post<ProjectDetail>('/api/projects', payload),
  getNewlyAdded: (limit: number = 50) =>
    api.get<ProjectSummary[]>('/api/projects/newly-added', { params: { limit } }),
  getSectors: () =>
    api.get<string[]>('/api/sectors'),
};

export interface CreateProjectPayload {
  project_code: string;
  project_name: string;
  ministry: string;
  department?: string;
  agency?: string;
  sector: string;
  state: string;
  district?: string;
  location?: string;
  approval_date?: string;
  original_completion_date?: string;
  revised_completion_date?: string;
  original_cost: number;
  revised_cost?: number;
  cumulative_expenditure?: number;
  physical_progress?: number;
  reporting_month?: string;
  status?: string;
  remarks?: string;
  milestones?: string;
}

export interface DuplicateCheckResult {
  exists: boolean;
  possible_duplicate: boolean;
  message: string;
  existing_project?: {
    project_code: string;
    project_name: string;
    ministry?: string;
    agency?: string;
    state?: string;
    sector?: string;
  };
}

export interface PortfolioData {
  total_projects: number;
  ongoing_projects: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  financial: {
    original_cost: number;
    revised_cost: number;
    cumulative_expenditure: number;
  };
  average_progress: number;
  state_wise: Array<{
    state: string;
    total: number;
    high_risk: number;
    critical: number;
    delayed: number;
    avg_progress: number;
  }>;
  ministry_wise: Array<{
    ministry: string;
    total: number;
    high_risk: number;
    critical: number;
    avg_progress: number;
  }>;
  high_risk_projects: Array<{
    project_code: string;
    project_name: string;
    ministry?: string;
    agency?: string;
    state?: string;
    sector?: string;
    risk_level: string;
    risk_score: number;
    revised_cost: number;
    physical_progress: number;
    warnings: string[];
  }>;
}

export interface GeneratedReport {
  report_type: string;
  markdown_report: string;
  metadata: {
    data_source: string;
    reporting_authority: string;
    projects_covered: number;
    generated_for: string;
    generated_at: string;
  };
  metrics: PortfolioData;
}

export const reportsApi = {
  getPortfolioData: () => api.get<PortfolioData>('/api/reports/portfolio-data'),
  generate: (payload: { report_type: string; project_code?: string }) =>
    api.post<GeneratedReport>('/api/reports/generate', payload),
};

export interface MonthlyUpdatePayload {
  report_month: string;
  physical_progress?: number;
  cumulative_expenditure?: number;
  project_status?: string;
  revised_cost?: number;
  revised_completion_date?: string;
  remarks?: string;
  allow_edit?: boolean;
}

export interface MonthlyUpdateResponse {
  success: boolean;
  message: string;
  snapshot: ProjectHistoryItem & {
    project_status?: string;
    remarks?: string;
    created_by?: string;
    created_at?: string;
  };
  risk_assessment: {
    risk_score: number;
    overall_risk: string;
    warnings: string[];
  };
  predictions: {
    cost_risk_level: string;
    predicted_cost_overrun: number;
    time_risk_level: string;
    predicted_time_months: number;
  };
}

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  authority_type: string;
  role: string;
  canonical_role: string;
  organization?: string;
  department?: string;
  designation?: string;
  state_region?: string;
  agency?: string;
  government_id?: string;
  masked_government_id: string;
  mobile_number?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at?: string;
}

export interface UpdateProfilePayload {
  full_name?: string;
  mobile_number?: string;
  designation?: string;
  organization?: string;
  department?: string;
  agency?: string;
  state_region?: string;
}

export interface AdminUserItem extends UserProfile {}

export interface AdminUpdateUserPayload {
  authority_type?: string;
  is_active?: boolean;
  is_verified?: boolean;
  government_id?: string;
  mobile_number?: string;
  full_name?: string;
  department?: string;
  designation?: string;
  organization?: string;
  agency?: string;
  state_region?: string;
}

export interface AuditLogItem {
  id: number;
  user_id?: number;
  user_email?: string;
  action: string;
  details?: string;
  ip_address?: string;
  timestamp?: string;
}

export const authApi = {
  getMe: () => api.get<UserProfile>('/api/auth/me'),
  updateProfile: (data: UpdateProfilePayload) => api.put<UserProfile>('/api/auth/profile', data),
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post<{ message: string }>('/api/auth/change-password', data),
};

export const adminApi = {
  listUsers: (params?: { q?: string; role?: string }) =>
    api.get<AdminUserItem[]>('/api/admin/users', { params }),
  updateUser: (userId: number, data: AdminUpdateUserPayload) =>
    api.put<AdminUserItem>(`/api/admin/users/${userId}`, data),
  listAuditLogs: (params?: { limit?: number; action?: string }) =>
    api.get<AuditLogItem[]>('/api/admin/audit-logs', { params }),
};

export interface StateStat {
  state_name: string;
  project_count: number;
  high_risk_count: number;
  critical_count: number;
  delayed_count: number;
  avg_delay_months: number;
  avg_progress: number;
  original_cost: number;
  revised_cost: number;
  cumulative_expenditure: number;
  cost_utilization_pct: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  total_projects: number;
}

export interface StateMapAnalytics {
  summary: {
    total_states: number;
    total_projects: number;
    total_cost: number;
    original_cost: number;
    total_expenditure: number;
    avg_progress: number;
    high_risk_projects: number;
    critical_projects: number;
    delayed_projects: number;
  };
  state_stats: Record<string, StateStat>;
  top_states_by_projects: Array<{ state: string; projects: number; high_risk: number }>;
  risk_distribution_by_state: Array<{ state: string; LOW: number; MEDIUM: number; HIGH: number; CRITICAL: number; total: number }>;
  delay_analysis_by_state: Array<{ state: string; delayed_projects: number; avg_delay_months: number; total_projects: number }>;
  avg_progress_by_state: Array<{ state: string; avg_progress: number; project_count: number }>;
  financial_overview_by_state: Array<{ state: string; revised_cost: number; cumulative_expenditure: number; utilization_pct: number }>;
}

export interface StateProjectItem {
  project_code: string;
  project_name: string;
  agency?: string;
  sector?: string;
  ministry?: string;
  state?: string;
  original_cost?: number;
  revised_cost?: number;
  cumulative_expenditure?: number;
  physical_progress?: number;
  cost_overrun_pct?: number;
  time_overrun_months?: number;
  project_status?: string;
  report_month?: string;
  risk_score?: number;
  overall_risk?: string;
}

export interface RiskDashboardData {
  last_updated: string;
  kpis: {
    high_risk: number;
    high_risk_mom: string;
    medium_risk: number;
    medium_risk_mom: string;
    low_risk: number;
    low_risk_mom: string;
    total_projects: number;
    early_warnings_count: number;
    early_warnings_mom: string;
  };
  distribution: Array<{
    name: string;
    key: string;
    count: number;
    percent: number;
    color: string;
  }>;
  trend: Array<{
    month: string;
    full_month: string;
    High: number;
    Medium: number;
    Low: number;
  }>;
  performance: Array<{
    category: string;
    count: number;
    percent: number;
  }>;
  heatmap: Array<{
    ministry: string;
    full_name: string;
    high: number;
    medium: number;
    low: number;
    total: number;
  }>;
  heatmap_totals: {
    high: number;
    medium: number;
    low: number;
    total: number;
  };
  top_risk_factors: Array<{
    factor: string;
    count: number;
    percentage: number;
  }>;
  recent_early_warnings: Array<{
    project_code: string;
    project_name: string;
    risk_type: string;
    date: string;
    severity: string;
    status: string;
    explanation: string;
  }>;
  high_risk_projects: Array<{
    project_code: string;
    project_name: string;
    ministry: string;
    agency: string;
    state: string;
    risk_level: string;
    risk_score: number;
    cost_overrun_pct: number;
    cost_probability: number;
    time_overrun_months: number;
    time_probability: number;
    overall_risk_pct: number;
    physical_progress: number;
  }>;
  ministries: string[];
  sectors: string[];
}

export const analyticsApi = {
  overview: () => api.get('/api/analytics/overview'),
  ministry: () => api.get('/api/analytics/ministry'),
  sector: () => api.get('/api/analytics/sector'),
  state: () => api.get('/api/analytics/state'),
  agency: () => api.get('/api/analytics/agency'),
  riskDashboard: (params?: { ministry?: string; sector?: string }) => api.get<RiskDashboardData>('/api/analytics/risk-dashboard', { params }),
  getStateMap: () => api.get<StateMapAnalytics>('/api/analytics/state/map'),
  getStateProjects: (stateName: string) => api.get<{ state_name: string; total: number; projects: StateProjectItem[] }>(`/api/analytics/state/${encodeURIComponent(stateName)}/projects`),
};

export const aiApi = {
  chat: (message: string, project_code?: string) => api.post('/api/ai/chat', { message, project_code }),
};

export default api;
