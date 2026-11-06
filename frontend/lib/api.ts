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
export const getRoles = () => api<Role[]>('/api/roles');

export const matchRole = (job_title: string) =>
  api<RoleMatch>('/api/roles/match', { method: 'POST', body: JSON.stringify({ job_title }) });

export const getSession = (id: number | string) => api<SessionState>(`/api/sessions/${id}`);

export const completeSession = (id: number | string) =>
  api<Results>(`/api/sessions/${id}/complete`, { method: 'POST' });

export const getResults = (id: number | string) => api<Results>(`/api/sessions/${id}/results`);

export const listSessions = () => api<SessionSummary[]>('/api/sessions');

// TODO S2-4.1: replace practice stand-ins when the practice endpoints are merged.
const PRACTICE_QUESTIONS: Question[] = [
  { id: 1, prompt: 'How would you explain a technical idea to someone who is new to it?', category: 'Communication' },
  { id: 2, prompt: 'Tell me about a time you solved a difficult problem.', category: 'Behavioral' },
  { id: 3, prompt: 'How do you prioritize tasks when several deadlines are close?', category: 'Planning' },
];

export async function getPracticeQuestion(input: { question_id?: number; role_id?: number; skill?: string; interview_type?: InterviewType; difficulty?: Difficulty }): Promise<Question> {
  const selected = PRACTICE_QUESTIONS.find((q) => q.id === input.question_id) ?? PRACTICE_QUESTIONS[0];
  return selected;
}

export async function submitPracticeAnswer(input: { question_id: number; text: string }): Promise<PracticeResult> {
  const question = PRACTICE_QUESTIONS.find((q) => q.id === input.question_id) ?? PRACTICE_QUESTIONS[0];
  const answered = input.text.trim().length > 0;
  const score = answered ? 70 : 0;
  return {
    question_id: question.id,
    prompt: question.prompt,
    answer: input.text,
    score,
    correct: score >= 50,
    criteria_met: answered ? ['Shares a clear and relevant response.'] : [],
    criteria_missed: answered ? ['Adds a specific example or next step.'] : ['Share an example or approach you would use.'],
    evidence: answered ? [input.text.trim()] : [],
    grader: 'keyword',
    strengths: answered ? 'You shared a clear starting point.' : 'You can take your time and try this question when you are ready.',
    improvements: answered ? 'Add one specific example to make your answer easier to follow.' : 'Try answering with one example or step.',
  };
}

// TODO S2-4.1: use the DELETE endpoint once the discard router is merged.
export async function discardSession(_id: number | string): Promise<void> {
  return;
}
