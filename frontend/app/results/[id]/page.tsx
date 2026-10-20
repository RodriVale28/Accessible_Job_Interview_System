// S1-5.3 Results & feedback page (Next.js) — owner: Shegofa Ahmadi


'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ApiError, getResults } from '../../../lib/api';
import type { Results } from '../../../lib/types';

export default function ResultsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadResults() {
      try {
        setLoading(true);
        setError('');
        const data = await getResults(id);

        if (active) {
          setResults(data);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof ApiError
              ? err.message
              : 'Could not load your results. Please try again.'
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (id) {
      void loadResults();
    }

    return () => {
      active = false;
    };
  }, [id]);

  if (loading) {
    return (
      <section className="report" aria-live="polite">
        <h1>Interview results</h1>
        <p>Loading your results...</p>
      </section>
    );
  }

  if (error || !results) {
    return (
      <section className="report" aria-labelledby="results-error-title">
        <h1 id="results-error-title">Results unavailable</h1>
        <p role="alert">
          {error || 'We could not find results for this interview.'}
        </p>
        <div className="actions">
          <button
            className="btn primary"
            onClick={() => router.refresh()}
          >
            Try again
          </button>
          <button
            className="btn amber"
            onClick={() => router.push('/setup')}
          >
            Start new session
          </button>
        </div>
      </section>
    );
  }

  const score = Math.max(0, Math.min(100, results.overall_score));
  const completedDate = results.completed_at
    ? new Date(results.completed_at).toLocaleString()
    : 'Not available';

  return (
    <section className="report" aria-labelledby="results-title">
      <header className="report-hero">
        <p>Interview complete</p>
        <h1 id="results-title">Your results and feedback</h1>
        <p>
          {results.job_title} · {results.difficulty} difficulty
        </p>

        <div className="rband">
          <div
            role="img"
            aria-label={`Overall score: ${score} out of 100`}
            style={{
              width: 140,
              height: 140,
              borderRadius: '50%',
              display: 'grid',
              placeItems: 'center',
              background: `conic-gradient(#267653 ${score * 3.6}deg, #e5e7eb 0deg)`,
              margin: '16px auto',
            }}
          >
            <div
              style={{
                width: 108,
                height: 108,
                borderRadius: '50%',
                background: 'var(--surface, white)',
                display: 'grid',
                placeContent: 'center',
                textAlign: 'center',
              }}
            >
              <strong style={{ fontSize: 28 }}>{score}%</strong>
              <span>Overall score</span>
            </div>
          </div>

          <p>
            <strong>{results.label}</strong>
          </p>
          <p>
            {results.correct_count} correct out of {results.total} questions
          </p>
          <p>
            {results.answered_count} answered · {results.missed_count} missed
          </p>
        </div>
      </header>

      <section className="rcard" aria-labelledby="strengths-title">
        <h2 className="rcard-h" id="strengths-title">Your strengths</h2>
        <p>{results.strengths}</p>
      </section>

      <section className="rcard" aria-labelledby="improvements-title">
        <h2 className="rcard-h" id="improvements-title">
          Areas to improve
        </h2>
        <p>{results.improvements}</p>
      </section>

      <section aria-labelledby="answer-feedback-title">
        <h2 id="answer-feedback-title">Question-by-question feedback</h2>

        {results.answers.length === 0 ? (
          <p>No answer feedback is available for this interview.</p>
        ) : (
          <div className="qlist">
            {results.answers.map((answer, index) => (
              <article
                className="qcard"
                key={`${answer.question_id}-${index}`}
              >
                <div className="qcard-head">
                  <h3>
                    Question {answer.q_index || index + 1}: {answer.prompt}
                  </h3>
                  <span
                    className={`pill ${
                      answer.correct
                        ? 'good'
                        : answer.status === 'blank' ||
                            answer.status === 'unanswered'
                          ? 'bad'
                          : 'mid'
                    }`}
                  >
                    {answer.status === 'blank' ||
                    answer.status === 'unanswered'
                      ? 'Unanswered'
                      : answer.correct
                        ? 'Correct'
                        : 'Needs practice'}
                  </span>
                </div>

                <p><strong>Your answer:</strong></p>
                <p>
                  {answer.answer?.trim()
                    ? answer.answer
                    : 'No answer was provided.'}
                </p>

                <p>
                  <strong>Score:</strong> {answer.score}%
                </p>

                <div className="hs">
                  <h4>What went well</h4>
                  <p>{answer.strengths || 'Keep practicing your answers.'}</p>
                </div>

                <div className="hd">
                  <h4>What to improve</h4>
                  <p>
                    {answer.improvements ||
                      'Try adding more relevant details to your answer.'}
                  </p>
                </div>

                {answer.matched.length > 0 && (
                  <p>
                    <strong>Keywords included:</strong>{' '}
                    {answer.matched.join(', ')}
                  </p>
                )}

                {answer.missing.length > 0 && (
                  <p>
                    <strong>Keywords to review:</strong>{' '}
                    {answer.missing.join(', ')}
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <p>
        <strong>Completed:</strong> {completedDate}
      </p>

      <div className="actions">
        <button
          className="btn amber"
          onClick={() => router.push('/setup')}
        >
          Retry interview
        </button>
        <button
          className="btn primary"
          onClick={() => router.push('/setup')}
        >
          Start new session
        </button>
      </div>
    </section>
  );
}
