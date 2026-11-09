// Shared API helper. Everyone calls the FastAPI backend through this.
// Requests go to /api/* on this site and are forwarded to the backend (next.config.mjs).
import { authHeaders } from './user';
import { loginRequired } from './supabase';
import type {
  Difficulty, Duration, InterviewType, PracticeResult, Question, Results, Role, RoleMatch, SessionState, SessionSummary,
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
    window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
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

export const getRoles = () => api<Role[]>('/api/roles');

export const matchRole = (job_title: string) =>
  api<RoleMatch>('/api/roles/match', { method: 'POST', body: JSON.stringify({ job_title }) });

export const getSession = (id: number | string) => api<SessionState>(`/api/sessions/${id}`);

export const completeSession = (id: number | string) =>
  api<Results>(`/api/sessions/${id}/complete`, { method: 'POST' });

export const getResults = (id: number | string) => api<Results>(`/api/sessions/${id}/results`);

export const listSessions = () => api<SessionSummary[]>('/api/sessions');

// S2-4.2: practice and discard (S2-4.1 endpoints).
export const getPracticeQuestion = (body: {
  question_id?: number; role_id?: number; skill?: string; interview_type?: InterviewType; difficulty?: Difficulty;
}) => api<Question>('/api/practice/question', { method: 'POST', body: JSON.stringify(body) });

export const submitPracticeAnswer = (body: { question_id: number; text: string }) =>
  api<PracticeResult>('/api/practice/answer', { method: 'POST', body: JSON.stringify(body) });

export const discardSession = (id: number | string) =>
  api<void>(`/api/sessions/${id}`, { method: 'DELETE' });

// TODO S2-2.2: Replace this development sample with live results once the
// Sprint 2 results API contract is available.
export const getSampleResults = (): Results => ({
  session_id: 1,
  job_title: 'Software Engineer',
  interview_type: 'Mixed',
  difficulty: 'Medium',
  duration_min: 15,
  overall_score: 75,
  label: 'Getting there',
  correct_count: 1,
  answered_count: 2,
  missed_count: 1,
  total: 3,
  strengths: 'You explained your approach clearly and included useful examples.',
  improvements: 'Try to explain the result of your actions more clearly.',
  completed_at: null,
  role_id: null,
  timed: false,
  answers: [
    {
      q_index: 0,
      question_id: 101,
      category: 'Behavioral',
      prompt: 'Tell me about a time you solved a difficult problem.',
      answer: 'I found the cause of an issue, planned a solution, and worked with my team to fix it.',
      status: 'answered',
      score: 80,
      correct: true,
      matched: ['problem', 'solution'],
      missing: ['result'],
      strengths: 'You explained the problem and the action you took.',
      improvements: 'Explain the final result of your actions.',
      question_type: 'Behavioral',
      criteria_met: [
        'Situation: Describe the situation.',
        'Task: Explain your responsibility.',
        'Action: Describe the steps you took.',
      ],
      criteria_missed: ['Result: Explain the outcome of your actions.'],
      evidence: [
        'I found the cause of an issue',
        'worked with my team',
        'planned a solution',
      ],
      grader: 'keyword',
    },
    {
      q_index: 1,
      question_id: 102,
      category: 'Technical',
      prompt: 'What is the purpose of a hash table?',
      answer: 'A hash table stores key-value pairs and helps find values quickly.',
      status: 'answered',
      score: 70,
      correct: true,
      matched: ['key-value pairs', 'quickly'],
      missing: ['hash function'],
      strengths: 'You explained the main purpose of a hash table.',
      improvements: 'Mention how a hash function helps locate values.',
      question_type: 'Technical',
      criteria_met: ['Explain that a hash table stores key-value pairs.'],
      criteria_missed: ['Explain how a hash function maps keys to locations.'],
      evidence: ['A hash table stores key-value pairs'],
      grader: 'ai',
    },
    {
      q_index: 2,
      question_id: 103,
      category: 'Technical',
      prompt: 'What is a binary search tree?',
      answer: '',
      status: 'blank',
      score: 0,
      correct: false,
      matched: [],
      missing: [],
      strengths: '',
      improvements: '',
      question_type: 'Technical',
      criteria_met: [],
      criteria_missed: [],
      evidence: [],
      grader: null,
    },
  ],
});
