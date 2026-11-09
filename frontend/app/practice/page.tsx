'use client';

import { Suspense, useEffect, useRef, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { PastInterviews } from '@/components/PastInterviews';
import ReadAloud from '@/components/ReadAloud';
import { useSearchParams } from 'next/navigation';
import { getPracticeQuestion, getRoles, submitPracticeAnswer } from '@/lib/api';
import { DIFFICULTY_LABEL, type Difficulty, type InterviewType, type PracticeResult, type Question, type Role } from '@/lib/types';

// Practice is one question, so Technical or Behavioral (Mixed is for full interviews).
const TYPES: InterviewType[] = ['Technical', 'Behavioral'];
const labelFor = (score: number) => score >= 80 ? 'Strong' : score >= 50 ? 'Getting there' : 'Room to grow';

export default function PracticePage() {
  return <Suspense fallback={<p className="muted" role="status">Loading practice…</p>}><PracticeContent /></Suspense>;
}

function PracticeContent() {
  const search = useSearchParams();
  const requestedId = Number(search.get('question_id')) || undefined;
  const [roles, setRoles] = useState<Role[]>([]);
  const [roleId, setRoleId] = useState('');
  const [interviewType, setInterviewType] = useState<InterviewType>('Technical');
  const [difficulty, setDifficulty] = useState<Difficulty>('Medium');
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<PracticeResult | null>(null);
  const [status, setStatus] = useState(''); // what is loading right now; '' = idle
  const busy = status !== '';
  const [error, setError] = useState('');
  const [answerInvalid, setAnswerInvalid] = useState(false);
  const feedbackRef = useRef<HTMLHeadingElement>(null);
  const questionRef = useRef<HTMLHeadingElement>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);
  const focusQuestion = useRef(false);

  useEffect(() => { if (result) feedbackRef.current?.focus(); }, [result]);

  // a new question was asked for: focus it so it is read out (the button that was clicked just changed)
  useEffect(() => {
    if (question && focusQuestion.current) { focusQuestion.current = false; questionRef.current?.focus(); }
  }, [question]);

  useEffect(() => { getRoles().then(setRoles).catch(() => setRoles([])); }, []);

  async function chooseQuestion(questionId?: number) {
    if (busy) return;
    setStatus('Loading a question…');
    setError('');
    setAnswerInvalid(false);
    setResult(null);
    setAnswer('');
    focusQuestion.current = true;
    try {
      const next = await getPracticeQuestion({ question_id: questionId, role_id: roleId ? Number(roleId) : undefined, interview_type: interviewType, difficulty });
      setQuestion(next);
    } catch (reason) {
      focusQuestion.current = false;
      setError(reason instanceof Error ? reason.message : 'Could not load a question. Please try again.');
    } finally { setStatus(''); }
  }

  useEffect(() => {
    let active = true;
    getPracticeQuestion({ question_id: requestedId })
      .then((next) => { if (active) setQuestion(next); })
      .catch((reason: Error) => {
        if (active) setError(reason instanceof Error ? reason.message : 'Could not load a question. Please try again.');
      });
    return () => { active = false; };
  }, [requestedId]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!question || !answer.trim()) {
      setError('Add an answer before checking it.');
      setAnswerInvalid(true);
      answerRef.current?.focus();
      return;
    }
    setStatus('Checking your answer…');
    setError('');
    setAnswerInvalid(false);
    try { setResult(await submitPracticeAnswer({ question_id: question.id, text: answer })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not check your answer. Please try again.'); }
    finally { setStatus(''); }
  }

  return (
    <div>
    <section className="wrap report" aria-labelledby="practice-title">
      <p className="section-label">Practice</p>
      <div className="panel pad">
        <h1 id="practice-title" className="card-title">Practice one question</h1>
        <div className="practice-settings">
          <div>
            <label className="glabel" htmlFor="practice-role">Role</label>
            <select id="practice-role" value={roleId} onChange={(e) => setRoleId(e.target.value)}>
              <option value="">Any role</option>
              {roles.map((role) => <option value={role.id} key={role.id}>{role.name}</option>)}
            </select>
          </div>
          <div>
            <label className="glabel" htmlFor="practice-type">Interview type</label>
            <select id="practice-type" value={interviewType} onChange={(e) => setInterviewType(e.target.value as InterviewType)}>
              {TYPES.map((type) => <option key={type}>{type}</option>)}
            </select>
          </div>
          <div>
            <label className="glabel" htmlFor="practice-difficulty">Difficulty</label>
            <select id="practice-difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value as Difficulty)}>
              {(['Easy', 'Medium', 'Hard'] as Difficulty[]).map((value) => <option key={value} value={value}>{DIFFICULTY_LABEL[value]}</option>)}
            </select>
          </div>
          <button className="guide-btn" type="button" onClick={() => void chooseQuestion()} aria-disabled={busy}>Choose question</button>
        </div>

        <p className="sr-only" role="status">{status}</p>
        {error && <p className="alert" id="practice-error" role="alert">{error}</p>}
        {question && <article className="practice-question" aria-labelledby="question-title">
          <div className="practice-qhead">
            <h2 id="question-title" ref={questionRef} tabIndex={-1}>{question.prompt}</h2>
            <ReadAloud text={question.prompt} label="Read question aloud" />
          </div>
          {!result ? (
            <form onSubmit={(e) => void submit(e)}>
              <label htmlFor="practice-answer" className="glabel">Your answer</label>
              <textarea id="practice-answer" ref={answerRef} rows={6} maxLength={5000} value={answer}
                aria-invalid={answerInvalid} aria-describedby={error ? 'practice-error' : undefined}
                onChange={(e) => { setAnswer(e.target.value); setAnswerInvalid(false); }} />
              <button type="submit" className="btn amber" aria-disabled={busy}>{busy ? 'Checking…' : 'See feedback'}</button>
            </form>
          ) : (
            <section className="practice-result" aria-labelledby="feedback-title">
              <h2 id="feedback-title" ref={feedbackRef} tabIndex={-1}>{labelFor(result.score)}</h2>
              {result.grader === 'keyword' && <p className="muted">Basic grading was used for this answer.</p>}
              <p><b>What went well:</b> {result.strengths}</p>
              <p><b>Next step:</b> {result.improvements}</p>
              {result.criteria_met.length > 0 && <div><h3>Key points covered</h3><ul>{result.criteria_met.map((item, i) => <li key={`${item}-${i}`}>{item}{result.evidence[i] ? <blockquote>{result.evidence[i]}</blockquote> : null}</li>)}</ul></div>}
              {result.criteria_missed.length > 0 && <div><h3>Ideas to add</h3><ul>{result.criteria_missed.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul></div>}
            </section>
          )}
        </article>}
        <div className="actions">
          {result && <button className="btn amber" type="button" onClick={() => void chooseQuestion(question?.id)} aria-disabled={busy}>Try again</button>}
          <button className="btn primary" type="button" onClick={() => void chooseQuestion()} aria-disabled={busy}>Another question</button>
          <Link className="btn primary" href="/">Back to Interview Studio</Link>
        </div>
      </div>
    </section>
    <section className="wrap report" aria-label="Interview history"><PastInterviews /></section>
    </div>
  );
}
