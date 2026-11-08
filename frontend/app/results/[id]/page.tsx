// S2-2.3 Results page — Accessible Job Interview System
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ApiError, getResults, startSession } from '../../../lib/api';
import type { AnswerResult, InterviewType, Results } from '../../../lib/types';

type ResultLevel = 'Strong' | 'Getting there' | 'Room to grow';

function scoreLabel(score: number): ResultLevel {
  const safeScore = Number.isFinite(score)
    ? Math.max(0, Math.min(100, Math.round(score)))
    : 0;

  if (safeScore >= 80) return 'Strong';
  if (safeScore >= 50) return 'Getting there';
  return 'Room to grow';
}

function pillClass(level: ResultLevel): string {
  if (level === 'Strong') return 'pill good';
  if (level === 'Getting there') return 'pill mid';
  return 'pill';
}

function isInterviewType(value: string): value is InterviewType {
  return (
    value === 'Technical' ||
    value === 'Behavioral' ||
    value === 'Mixed'
  );
}

function isBehavioral(a: AnswerResult): boolean {
  return (a.question_type ?? '').toLowerCase() === 'behavioral';
}

const STAR_LABELS = ['Situation', 'Task', 'Action', 'Result'] as const;

function getStarRows(a: AnswerResult) {
  const met = a.criteria_met ?? [];
  const missed = a.criteria_missed ?? [];
  const evidence = a.evidence ?? [];

  return STAR_LABELS.map((label) => {
    const prefix = `${label.toLowerCase()}:`;

    const metIndex = met.findIndex((criterion) =>
      criterion.trim().toLowerCase().startsWith(prefix)
    );

    const missedCriterion = missed.find((criterion) =>
      criterion.trim().toLowerCase().startsWith(prefix)
    );

    return {
      label,
      criterion: metIndex >= 0 ? met[metIndex] : missedCriterion,
      covered: metIndex >= 0,
      evidence: metIndex >= 0 ? evidence[metIndex] : undefined,
    };
  });
}

function getKeyPointCounts(answers: AnswerResult[]) {
  return answers.reduce(
    (counts, answer) => {
      const met = answer.criteria_met ?? [];
      const missed = answer.criteria_missed ?? [];

      // Use the newer criteria fields when available.
      if (met.length > 0 || missed.length > 0) {
        return {
          covered: counts.covered + met.length,
          total: counts.total + met.length + missed.length,
        };
      }

      // Fall back to the Sprint 1 matched/missing fields.
      const oldMatched = answer.matched ?? [];
      const oldMissing = answer.missing ?? [];

      return {
        covered: counts.covered + oldMatched.length,
        total: counts.total + oldMatched.length + oldMissing.length,
      };
    },
    { covered: 0, total: 0 }
  );
}

function AnswerFeedback({ answer }: { answer: AnswerResult }) {
  const answered = answer.status === 'answered';
  const level = scoreLabel(answer.score);
  const met = answer.criteria_met ?? [];
  const missed = answer.criteria_missed ?? [];
  const evidence = answer.evidence ?? [];
  const matched = answer.matched ?? [];
  const missing = answer.missing ?? [];
  const hasNewCriteria = met.length > 0 || missed.length > 0;
  const behavioral = isBehavioral(answer);

  return (
    <li className="qcard">
      <div className="qcard-head">
        <span className="hs" aria-hidden="true">
          Q{answer.q_index}
        </span>

        <div className="grow">
          <div className="hd">
            {answered ? `${level} · ${answer.score}/100` : 'Skipped'} ·{' '}
            {answer.category}
          </div>

          <h3 className="ht">
            <span className="sr-only">
              Question {answer.q_index}:{' '}
            </span>
            {answer.prompt}
          </h3>
        </div>

        <span className={answered ? pillClass(level) : 'pill'}>
          {answered ? level : 'Skipped: one to work on'}
        </span>
      </div>

      {answered ? (
        <blockquote aria-label="Your answer">
          {answer.answer}
        </blockquote>
      ) : (
        <p className="muted">
          {answer.status === 'blank'
            ? "You skipped this question. That's okay — you can try it again next time."
            : "This question wasn't reached. You can work on it in another practice session."}
        </p>
      )}

      {answered && answer.strengths && (
        <p>
          <b>What went well:</b> {answer.strengths}
        </p>
      )}

      {answered && behavioral && hasNewCriteria && (
        <section aria-label="STAR feedback">
          <h4>STAR method feedback</h4>
          <p className="muted">
            A strong behavioral answer explains the Situation, Task,
            Action, and Result.
          </p>

          <ul>
            {getStarRows(answer).map((row) => (
              <li key={row.label}>
                <p>
                  <b>{row.label}:</b>{' '}
                  {row.criterion ?? 'No specific feedback available.'}
                </p>

                {row.covered ? (
                  <>
                    <span className="chip good">Covered</span>
                    {row.evidence && (
                      <blockquote aria-label={`Evidence for ${row.label}`}>
                        {row.evidence}
                      </blockquote>
                    )}
                  </>
                ) : (
                  <span className="chip">
                    Try mentioning this next time
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {answered && !behavioral && hasNewCriteria && (
        <section className="kw" aria-label="Answer feedback">
          {met.length > 0 && (
            <div>
              <p>
                <b>Key points you covered:</b>
              </p>
              <ul>
                {met.map((criterion, index) => (
                  <li key={`${criterion}-${index}`}>
                    <p>{criterion}</p>
                    {evidence[index] && (
                      <blockquote aria-label="Evidence from your answer">
                        {evidence[index]}
                      </blockquote>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {missed.length > 0 && (
            <div>
              <p>
                <b>Next time, try mentioning:</b>
              </p>
              <ul>
                {missed.map((criterion, index) => (
                  <li key={`${criterion}-${index}`}>
                    {criterion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {answered && !hasNewCriteria && (
        <div className="kw">
          {matched.length > 0 && (
            <p>
              <span className="kw-l">Key terms you used:</span>
              {matched.map((term, index) => (
                <span className="chip good" key={`${term}-${index}`}>
                  {term}
                </span>
              ))}
            </p>
          )}

          {missing.length > 0 && (
            <p>
              <b>Next time, try mentioning:</b>
              {missing.map((term, index) => (
                <span className="chip" key={`${term}-${index}`}>
                  {term}
                </span>
              ))}
            </p>
          )}
        </div>
      )}

      {answered && answer.improvements && (
        <p>
          <b>Next step:</b> {answer.improvements}
        </p>
      )}

      {answer.grader === 'keyword' && (
        <p className="muted">
          Basic grading was used for this answer.
        </p>
      )}

      <p>
        <Link href={`/practice?question_id=${answer.question_id}`}>
          Try this one again
        </Link>
      </p>
    </li>
  );
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

  // Only the latest request may update state.
  const requestRef = useRef(0);

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

  // Start another interview using all the same setup options.
  async function retrySameSetup() {
    if (!results || retrying) return;

    setRetrying(true);
    setRetryError('');

    try {
      const session = await startSession({
        job_title: results.job_title,
        role_id: results.role_id,
        interview_type: isInterviewType(results.interview_type)
          ? results.interview_type
          : 'Technical',
        difficulty: results.difficulty,
        duration_min: results.duration_min,
        timed: results.timed,
      });

      router.push(`/session/${session.session_id}`);
    } catch (err) {
      setRetrying(false);
      setRetryError(
        err instanceof ApiError
          ? err.message
          : 'Could not start a new interview. Please try again.'
      );
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
      <section
        className="wrap report"
        aria-labelledby="results-error-title"
      >
        <div className="panel pad">
          <h1 id="results-error-title" className="card-title">
            Results unavailable
          </h1>

          <p role="alert" className="alert">
            {error || 'We could not find results for this interview.'}
          </p>

          <div className="actions">
            <button className="btn primary" onClick={retry}>
              Try again
            </button>

            <button
              className="btn amber"
              onClick={() => router.push('/setup')}
            >
              Start new session
            </button>
          </div>
        </div>
      </section>
    );
  }

  const score = Number.isFinite(results.overall_score)
    ? Math.max(0, Math.min(100, Math.round(results.overall_score)))
    : 0;

  const overallLabel = scoreLabel(score);
  const answers = results.answers ?? [];
  const notReached = Math.max(0, results.total - answers.length);
  const keyPoints = getKeyPointCounts(answers);

  return (
    <section
      className="wrap report"
      aria-labelledby="results-title"
    >
      <p className="section-label">Interview report</p>

      <div className="panel pad">
        <div className="report-hero">
          <div>
            <h1 id="results-title" className="report-title">
              {overallLabel}
            </h1>

            <p>
              {results.strengths ||
                'You completed a practice session. Keep building on what you learned.'}
            </p>

            <p>
              <b>
                Key points covered: {keyPoints.covered} of {keyPoints.total}
              </b>
            </p>

            <p className="muted">
              Overall score: {score}/100
            </p>

            <p className="muted">
              {results.job_title} · {results.interview_type} ·{' '}
              {results.difficulty} · {results.duration_min} min
            </p>

            <p className="muted">
              {results.answered_count} answered · {results.missed_count}{' '}
              skipped or not answered
            </p>
          </div>
        </div>

        {!results.completed_at && (
          <p className="alert" style={{ marginTop: 18 }}>
            This interview is still in progress, so the score may change.{' '}
            <Link href={`/session/${results.session_id}`}>
              Continue the interview
            </Link>
          </p>
        )}

        <div className="rband">
          <section
            className="rcard good"
            aria-labelledby="strengths-title"
          >
            <h2 className="rcard-h" id="strengths-title">
              Strengths
            </h2>
            <p>
              {results.strengths ||
                'Keep practicing to discover more of your strengths.'}
            </p>
          </section>

          <section
            className="rcard grow"
            aria-labelledby="improvements-title"
          >
            <h2 className="rcard-h" id="improvements-title">
              Next steps
            </h2>
            <p>
              {results.improvements ||
                'Continue practicing to build confidence and improve your answers.'}
            </p>
          </section>
        </div>

        <h2 className="section-label" style={{ marginTop: 26 }}>
          Question-by-question feedback
        </h2>

        {answers.length === 0 ? (
          <p className="muted">
            No question responses are available for this interview.
          </p>
        ) : (
          <ol className="qlist">
            {answers.map((answer) => (
              <AnswerFeedback
                key={`${answer.question_id}-${answer.q_index}`}
                answer={answer}
              />
            ))}
          </ol>
        )}

        {notReached > 0 && (
          <p className="muted" style={{ marginTop: 12 }}>
            {notReached} questions were not reached before the interview
            ended. They count as 0 in the overall score.
          </p>
        )}

        {retryError && (
          <p
            role="alert"
            className="alert"
            style={{ marginTop: 18 }}
          >
            {retryError}
          </p>
        )}

        <div className="actions">
          <button
            className="btn amber"
            onClick={() => void retrySameSetup()}
            disabled={retrying}
          >
            {retrying ? 'Starting…' : 'Retry with same setup'}
          </button>

          <button
            className="btn primary"
            onClick={() => router.push('/setup')}
          >
            Start new session
          </button>
        </div>
      </div>
    </section>
  );
}