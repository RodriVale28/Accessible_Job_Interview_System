'use client';

import { Suspense, useEffect, useState, type FormEvent } from 'react';
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
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { getRoles().then(setRoles).catch(() => setRoles([])); }, []);

  async function chooseQuestion(questionId?: number) {
    setBusy(true);
    setError('');
    setResult(null);
    setAnswer('');
    try {
      const next = await getPracticeQuestion({ question_id: questionId, role_id: roleId ? Number(roleId) : undefined, interview_type: interviewType, difficulty });
      setQuestion(next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load a question. Please try again.');
    } finally { setBusy(false); }
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
    if (!question || !answer.trim()) {
      setError('Add an answer before checking it.');
      return;
    }
    setBusy(true);
    setError('');
    try { setResult(await submitPracticeAnswer({ question_id: question.id, text: answer })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not check your answer. Please try again.'); }
    finally { setBusy(false); }
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
          <button className="guide-btn" type="button" onClick={() => void chooseQuestion()} disabled={busy}>Choose question</button>
        </div>

        {error && <p className="alert" role="alert">{error}</p>}
        {question && <article className="practice-question" aria-labelledby="question-title">
          <div className="practice-qhead">
            <h2 id="question-title">{question.prompt}</h2>
            <ReadAloud text={question.prompt} label="Read question aloud" />
          </div>
          {!result ? (
            <form onSubmit={(e) => void submit(e)}>
              <label htmlFor="practice-answer" className="glabel">Your answer</label>
              <textarea id="practice-answer" rows={6} maxLength={5000} value={answer} onChange={(e) => setAnswer(e.target.value)} />
              <button type="submit" className="btn amber" disabled={busy}>{busy ? 'Checking…' : 'See feedback'}</button>
            </form>
          ) : (
            <section className="practice-result" aria-labelledby="feedback-title">
              <h2 id="feedback-title">{labelFor(result.score)}</h2>
              {result.grader === 'keyword' && <p className="muted">Basic grading was used for this answer.</p>}
              <p><b>What went well:</b> {result.strengths}</p>
              <p><b>Next step:</b> {result.improvements}</p>
              {result.criteria_met.length > 0 && <div><h3>Key points covered</h3><ul>{result.criteria_met.map((item, i) => <li key={`${item}-${i}`}>{item}{result.evidence[i] ? <blockquote>{result.evidence[i]}</blockquote> : null}</li>)}</ul></div>}
              {result.criteria_missed.length > 0 && <div><h3>Ideas to add</h3><ul>{result.criteria_missed.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul></div>}
            </section>
          )}
        </article>}
        <div className="actions">
          {result && <button className="btn amber" type="button" onClick={() => void chooseQuestion(question?.id)} disabled={busy}>Try again</button>}
          <button className="btn primary" type="button" onClick={() => void chooseQuestion()} disabled={busy}>Another question</button>
          <Link className="btn primary" href="/">Back to Interview Studio</Link>
        </div>
      </div>
    </section>
    <section className="wrap report" aria-label="Interview history"><PastInterviews /></section>
    </div>
  );
}
