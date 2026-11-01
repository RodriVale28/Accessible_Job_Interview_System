// Shared API helper. Everyone calls the FastAPI backend through this.
// Requests go to /api/* on this site and are forwarded to the backend (next.config.mjs).
import { authHeaders } from './user';
import { loginRequired } from './supabase';
import type {
  Difficulty, Duration, InterviewType, Results, Role, RoleMatch, SessionState, SessionSummary,
} from './types';

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(await authHeaders()), ...(init.headers ?? {}) },
      cache: 'no-store',
    });
  } catch {
    throw new ApiError('Could not reach the server. Check your connection and try again.', 0);
  }
  if (res.status === 401 && loginRequired) {
    // not signed in, or the login expired: come back here after logging in
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- api() is not a component
    window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname)}`);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (data as { detail?: unknown }).detail;
    const msg = typeof detail === 'string' ? detail
      : res.status >= 500 ? 'Cannot reach the interview server. Make sure the backend is running, then try again.'
      : 'Something went wrong. Please retry.';
    throw new ApiError(msg, res.status);
  }
  return data as T;
}

// S2-1.3: role_id, interview_type and timed are optional, so older callers keep working.
export const startSession = (body: {
  job_title: string;
  difficulty: Difficulty;
  duration_min: Duration;
  role_id?: number | null;
  interview_type?: InterviewType;
  timed?: boolean;
}) =>
  api<SessionState>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ interview_type: 'Technical', ...body }),
  });

// TODO S2-1.3: set to false once GET /api/roles and POST /api/roles/match are merged and live.
const USE_FAKE_ROLES = true;

const FAKE_ROLES: Role[] = [
  { id: 1, name: 'Software Engineer' },
  { id: 2, name: 'Data Analyst' },
  { id: 3, name: 'IT Support' },
  { id: 4, name: 'Customer Service' },
];

export const getRoles = (): Promise<Role[]> =>
  USE_FAKE_ROLES ? Promise.resolve(FAKE_ROLES) : api<Role[]>('/api/roles');

export const matchRole = (job_title: string): Promise<RoleMatch> => {
  if (USE_FAKE_ROLES) {
    // TODO S2-1.3: fake keyword match, removed together with USE_FAKE_ROLES
    const t = job_title.toLowerCase();
    const hit =
      /data|analyst/.test(t) ? FAKE_ROLES[1] :
      /help desk|technician|it support/.test(t) ? FAKE_ROLES[2] :
      /call center|customer|agent/.test(t) ? FAKE_ROLES[3] :
      /software|engineer|developer/.test(t) ? FAKE_ROLES[0] : null;
    return Promise.resolve({ role_id: hit?.id ?? null, role_name: hit?.name ?? null, matched_by: 'keyword' });
  }
  return api<RoleMatch>('/api/roles/match', { method: 'POST', body: JSON.stringify({ job_title }) });
};

export const getSession = (id: number | string) => api<SessionState>(`/api/sessions/${id}`);

export const completeSession = (id: number | string) =>
  api<Results>(`/api/sessions/${id}/complete`, { method: 'POST' });

export const getResults = (id: number | string) => api<Results>(`/api/sessions/${id}/results`);

export const listSessions = () => api<SessionSummary[]>('/api/sessions');
