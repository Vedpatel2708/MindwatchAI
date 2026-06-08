/**
 * frontend/lib/api.ts — MINDWATCH
 * Type-safe API client for all backend endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface AnalysisStep {
  step_number: number;
  step_type: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_output?: Record<string, unknown>;
  content?: string;
  is_error: boolean;
  error_detail?: string;
}

export interface Assessment {
  id: string;
  input_text: string;
  input_type: string;
  session_id?: string;
  crisis_score?: number;
  depression_score?: number;
  anxiety_score?: number;
  crisis_signal?: number;
  sentiment_score?: number;
  dominant_emotion?: string;
  detected_symptoms?: string[];
  risk_level: string;
  agent_summary?: string;
  recommendations?: string[];
  resources?: Array<{ name: string; contact: string; type: string }>;
  status: string;
  submitted_at: string;
  analyzed_at?: string;
  analysis_steps?: AnalysisStep[];
}

export interface RiskAlert {
  id: string;
  assessment_id: string;
  crisis_score: number;
  risk_level: string;
  status: string;
  created_at: string;
}

export interface DailyDataPoint {
  date: string;
  assessments: number;
  high_risk: number;
}

export interface AnalyticsSummary {
  total_assessments_today: number;
  high_risk_today: number;
  open_alerts: number;
  crisis_rate_today: number;
  daily_series: DailyDataPoint[];
  emotion_distribution: Record<string, number>;
}

export interface APIEnvelope<T> {
  data: T | null;
  error: { code: string; message: string } | null;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  const envelope: APIEnvelope<T> = await res.json();
  if (envelope.error) throw new Error(`API Error [${envelope.error.code}]: ${envelope.error.message}`);
  return envelope.data as T;
}

export async function submitAssessment(body: {
  input_text: string; input_type?: string; session_id?: string;
}): Promise<{ assessment_id: string; risk_level: string; crisis_score: number; status: string }> {
  return apiFetch('/assessments', { method: 'POST', body: JSON.stringify(body) });
}

export async function fetchAssessments(params: { page?: number; page_size?: number; risk_level?: string } = {}): Promise<PaginatedList<Assessment>> {
  const qs = new URLSearchParams();
  if (params.page)       qs.set('page', String(params.page));
  if (params.page_size)  qs.set('page_size', String(params.page_size));
  if (params.risk_level) qs.set('risk_level', params.risk_level);
  return apiFetch<PaginatedList<Assessment>>(`/assessments${qs.toString() ? '?' + qs : ''}`);
}

export async function fetchAssessment(id: string): Promise<Assessment> {
  return apiFetch<Assessment>(`/assessments/${id}`);
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>('/analytics/summary');
}
