// Shared API helper. Everyone calls the FastAPI backend through this.
// Requests go to /api/* on this site and are forwarded to the backend (next.config.mjs).
import { getUserId } from './user';
import type { Difficulty, Duration, Results, SessionState } from './types';

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
      headers: { 'Content-Type': 'application/json', 'X-User-Id': getUserId(), ...(init.headers ?? {}) },
      cache: 'no-store',
    });
  } catch {
    throw new ApiError('Could not reach the server. Check your connection and try again.', 0);
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

export const startSession = (body: { job_title: string; difficulty: Difficulty; duration_min: Duration }) =>
  api<SessionState>('/api/sessions', { method: 'POST', body: JSON.stringify({ ...body, interview_type: 'Technical' }) });

export const getSession = (id: number | string) => api<SessionState>(`/api/sessions/${id}`);

export const completeSession = (id: number | string) =>
  api<Results>(`/api/sessions/${id}/complete`, { method: 'POST' });

export const getResults = (id: number | string) => api<Results>(`/api/sessions/${id}/results`);
