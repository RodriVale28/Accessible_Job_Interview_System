// S1-3.2 Submit answer -> save -> next question — owner: Jayme Nguyen
// An empty text is a skip: the backend saves it as a blank answer.
import { api } from './api';
import type { AnswerOut } from './types';

export const submitAnswer = (sessionId: number | string, questionId: number, text: string) =>
  api<AnswerOut>(`/api/sessions/${sessionId}/answers`, {
    method: 'POST',
    body: JSON.stringify({ question_id: questionId, text }),
  });
