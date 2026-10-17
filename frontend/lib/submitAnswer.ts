// S1-3.2 Submit answer -> save -> next question - owner: Jayme Nguyen
import { api } from './api';
import type { Question } from './types';

export type SubmitResult = {
  saved: boolean;
  blank: boolean;
  correct_count: number;
  answered: number;
  total: number;
  completed: boolean;
  q_index: number;
  question: Question | null;
};

/** Save the answer for the current question and get the next one.
 *  An empty `text` is a deliberate skip (saved as unanswered). Throws ApiError on failure. */
export function submitAnswer(sessionId: number, questionId: number, text: string): Promise<SubmitResult> {
  return api<SubmitResult>(`/api/sessions/${sessionId}/answers`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, text }),
  });
}
