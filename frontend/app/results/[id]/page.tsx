// S1-5.3 Results & feedback page (Next.js) — owner: Shegofa Ahmadi
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ApiError, getResults, startSession } from '../../../lib/api';
import type { AnswerResult, Results } from '../../../lib/types';

function answerStatus(a: AnswerResult): { text: string; pill: 'good' | 'mid' | 'bad' } {
  if (a.status === 'unanswered') return { text: 'Not answered', pill: 'bad' };
  if (a.status === 'blank') return { text: 'Skipped', pill: 'bad' };
  if (a.correct) return { text: 'Correct', pill: 'good' };
  if (a.matched.length > 0) return { text: 'Partly correct', pill: 'mid' };
  return { text: 'Incorrect', pill: 'bad' };
}

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState('');

  // Only the latest request may update state (ignores late responses after
  // the id changes, the page unmounts, or "Try again" is pressed twice).
  const requestRef = useRef(0);

  // State is only set in the promise callbacks, after the request finishes.
  const loadResults = useCallback(() => {
    const request = ++requestRef.current;
    const isLatest = () => request === requestRef.current;
    return getResults(id).then(
      (data) => {
        if (!isLatest()) return;
        setResults(data);
        setLoading(false);
      },
      (err) => {
        if (!isLatest()) return;
        setError(
          err instanceof ApiError
            ? err.message
            : 'Could not load your results. Please try again.'
        );
        setLoading(false);
      }
    );
  }, [id]);

  useEffect(() => {
    const requests = requestRef;
    if (id) {
      void loadResults();
    }
    return () => {
      requests.current++;
    };
  }, [id, loadResults]);

  function retry() {
    setLoading(true);
    setError('');
    void loadResults();
  }

  // Start a new interview with the same job title, difficulty and length.
  async function retrySameSetup() {
    if (!results || retrying) return;
    setRetrying(true);
    setRetryError('');
    try {
      const session = await startSession({
        job_title: results.job_title,
        difficulty: results.difficulty,
        duration_min: results.duration_min,
      });
      router.push(`/session/${session.session_id}`);
    } catch (err) {
      setRetrying(false);
      setRetryError(err instanceof ApiError ? err.message : 'Could not start a new interview. Please try again.');
    }
  }

  if (loading) {
    return (
      <section className="wrap report" aria-live="polite">
        <h1 className="report-title">Interview results</h1>
        <p className="muted">Loading your results…</p>
      </section>
    );
  }

  if (error || !results) {
    return (
      <section className="wrap report" aria-labelledby="results-error-title">
        <div className="panel pad">
          <h1 id="results-error-title" className="card-title">Results unavailable</h1>
          <p role="alert" className="alert">
            {error || 'We could not find results for this interview.'}
          </p>
          <div className="actions">
            <button className="btn primary" onClick={retry}>Try again</button>
            <button className="btn amber" onClick={() => router.push('/setup')}>Start new session</button>
          </div>
        </div>
      </section>
    );
  }

  const score = Math.max(0, Math.min(100, Math.round(results.overall_score)));
  const notReached = results.total - results.answers.length;

  return (
    <section className="wrap report" aria-labelledby="results-title">
      <p className="section-label">Interview report</p>
      <div className="panel pad">
        <div className="report-hero">
          <div className="score-box" aria-hidden="true">
            {score}
            <small>/ 100</small>
          </div>
          <div>
            <h1 id="results-title" className="report-title">
              Overall score: {score} out of 100
            </h1>
            <p style={{ margin: '0 0 6px' }}>
              <span className="badge">{results.label}</span>
            </p>
            <p className="muted" style={{ margin: 0 }}>
              {results.job_title} · {results.interview_type} · {results.difficulty} · {results.duration_min} min
            </p>
            <p style={{ margin: '6px 0 0' }}>
              {results.correct_count} of {results.total} correct · {results.answered_count} answered ·{' '}
              {results.missed_count} skipped or not answered
            </p>
          </div>
        </div>

        {!results.completed_at && (
          <p className="alert" style={{ marginTop: 18 }}>
            This interview is still in progress, so the score may change.{' '}
            <Link href={`/session/${results.session_id}`}>Continue the interview</Link>
          </p>
        )}

        <div className="rband">
          <section className="rcard good" aria-labelledby="strengths-title">
            <h2 className="rcard-h" id="strengths-title">Strengths</h2>
            <p>{results.strengths}</p>
          </section>
          <section className="rcard grow" aria-labelledby="improvements-title">
            <h2 className="rcard-h" id="improvements-title">Where to improve</h2>
            <p>{results.improvements}</p>
          </section>
        </div>

        <h2 className="section-label" style={{ marginTop: 26 }}>Question-by-question</h2>
        {results.answers.length === 0 ? (
          <p className="muted">No questions were answered in this interview.</p>
        ) : (
          <ol className="qlist">
            {results.answers.map((a) => {
              const st = answerStatus(a);
              const answered = a.status === 'answered';
              return (
                <li className="qcard" key={a.question_id}>
                  <div className="qcard-head">
                    <span className="hs" aria-hidden="true">Q{a.q_index}</span>
                    <div className="grow">
                      <div className="hd">
                        {st.text} · {a.score}/100 · {a.category}
                      </div>
                      <h3 className="ht">
                        <span className="sr-only">Question {a.q_index}: </span>
                        {a.prompt}
                      </h3>
                    </div>
                    <span className={`pill ${st.pill}`}>{st.text}</span>
                  </div>

                  {answered ? (
                    <blockquote aria-label="Your answer">{a.answer}</blockquote>
                  ) : (
                    <p className="muted">
                      {a.status === 'blank' ? 'You skipped this question.' : 'Time ran out or the interview ended before you answered.'}
                    </p>
                  )}

                  {answered && a.strengths && (
                    <p><b>What went well:</b> {a.strengths}</p>
                  )}
                  <p><b>To improve:</b> {a.improvements}</p>

                  {(a.matched.length > 0 || a.missing.length > 0) && (
                    <div className="kw">
                      {a.matched.length > 0 && (
                        <p>
                          <span className="kw-l">Key terms you used:</span>
                          {a.matched.map((k) => <span className="chip good" key={k}>{k}</span>)}
                        </p>
                      )}
                      {a.missing.length > 0 && (
                        <p>
                          <span className="kw-l">Key terms to review:</span>
                          {a.missing.map((k) => <span className="chip" key={k}>{k}</span>)}
                        </p>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        )}

        {notReached > 0 && (
          <p className="muted" style={{ marginTop: 12 }}>
            {notReached} of {results.total} questions were not reached before the interview ended. They count as 0 in
            the overall score.
          </p>
        )}

        {retryError && <p role="alert" className="alert" style={{ marginTop: 18 }}>{retryError}</p>}
        <div className="actions">
          <button className="btn amber" onClick={() => void retrySameSetup()} disabled={retrying}>
            {retrying ? 'Starting…' : 'Retry with same setup'}
          </button>
          <button className="btn primary" onClick={() => router.push('/setup')}>
            Start new session
          </button>
        </div>
      </div>
    </section>
  );
}