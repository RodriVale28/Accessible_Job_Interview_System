export type Difficulty = 'Easy' | 'Medium' | 'Hard';
export type Duration = 15 | 30 | 45;

// S2-1.3
export type InterviewType = 'Technical' | 'Behavioral' | 'Mixed';
export type Role = { id: number; name: string };
export type RoleMatch = {
  role_id: number | null;
  role_name: string | null;
  matched_by: 'ai' | 'keyword';
};

export type Question = { id: number; prompt: string; category: string };

export type SessionState = {
  session_id: number;
  job_title: string;
  interview_type: InterviewType;
  difficulty: Difficulty;
  duration_min: Duration;
  status: 'in_progress' | 'completed';
  q_index: number;
  total: number;
  correct_count: number;
  question: Question | null;
  started_at: string;
  expires_at: string | null; // null when the interview is not timed (S2-1.3)
  seconds_left: number | null; // null when the interview is not timed (S2-1.3)
  role_name: string | null; // S2-1.3
  timed: boolean; // S2-1.3
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
  question_type: string | null; // S2-2.2
  criteria_met: string[]; // S2-2.2
  criteria_missed: string[]; // S2-2.2
  evidence: string[]; // S2-2.2, one quote per criteria_met item
  grader: 'ai' | 'keyword' | null; // S2-2.2
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
  role_id: number | null; // S2-2.2 (for Retry)
  timed: boolean; // S2-2.2 (for Retry)
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
  role_name: string | null; // S2-1.3
  interview_type: InterviewType; // S2-1.3
  timed: boolean;
};


export type PracticeResult = {
  question_id: number;
  prompt: string;
  answer: string;
  score: number;
  correct: boolean;
  criteria_met: string[];
  criteria_missed: string[];
  evidence: string[];
  grader: string;
  strengths: string;
  improvements: string;
};
