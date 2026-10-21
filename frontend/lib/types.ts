export type Difficulty = 'Easy' | 'Medium' | 'Hard';
export type Duration = 15 | 30 | 45;

export type Question = { id: number; prompt: string; category: string };

export type SessionState = {
  session_id: number;
  job_title: string;
  interview_type: string;
  difficulty: Difficulty;
  duration_min: Duration;
  status: 'in_progress' | 'completed';
  q_index: number;
  total: number;
  correct_count: number;
  question: Question | null;
  started_at: string;
  expires_at: string;
  seconds_left: number;
};

// Response of POST /api/sessions/{id}/answers
export type AnswerOut = {
  saved: boolean;
  blank: boolean;
  correct_count: number;
  answered: number;
  total: number;
  completed: boolean;
  q_index: number;
  question: Question | null;
};

export type AnswerResult = {
  q_index: number;
  question_id: number;
  category: string;
  prompt: string;
  answer: string;
  status: 'answered' | 'blank' | 'unanswered';
  score: number;
  correct: boolean;
  matched: string[];
  missing: string[];
  strengths: string;
  improvements: string;
};

export type Results = {
  session_id: number;
  job_title: string;
  interview_type: string;
  difficulty: Difficulty;
  duration_min: Duration;
  overall_score: number;
  label: string;
  correct_count: number;
  answered_count: number;
  missed_count: number;
  total: number;
  strengths: string;
  improvements: string;
  completed_at: string | null;
  answers: AnswerResult[];
};

// One row of GET /api/sessions (past interviews, newest first)
export type SessionSummary = {
  session_id: number;
  job_title: string;
  difficulty: Difficulty;
  duration_min: Duration;
  status: 'in_progress' | 'completed';
  overall_score: number | null;
  started_at: string;
  completed_at: string | null;
};
