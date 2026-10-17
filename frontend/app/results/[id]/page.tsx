// S1-5.3 Results & feedback page - owner: Shegofa Ahmadi
'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getResults, startSession } from '@/lib/api';
import type { AnswerResult, Results } from '@/lib/types';

const STATUS_TEXT: Record<AnswerResult['status'], string> = {
  answered: 'Answered',
  blank: 'Skipped',
  unanswered: 'Not answered',
};

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<Results | null>(null);
  const [error, setError] = useState('');
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    let alive = true;
    getResults(id)
      .then((r) => alive && setData(r))
      .catch((e: Error) => alive && setError(e.message));
    return () => { alive = false; };
  }, [id]);

  async function retry() {
    if (!data) return;
    setRetrying(true);
    try {
      const s = await startSession({ job_title: data.job_title, difficulty: data.difficulty, duration_min: data.duration_min });
      router.push(`/session/${s.session_id}`);
    } catch (e) {
      setError((e as Error).message);
      setRetrying(false);
    }
  }

  if (error && !data) {
    return (
      <div className="wrap hero">
        <div className="panel pad">
          <h1 className="card-title">Results aren&apos;t available</h1>
          <p role="alert">{error}</p>
          <Link className="btn amber" href="/setup">Start a new interview</Link>
        </div>
      </div>
    );
  }
  if (!data) return <div className="wrap hero"><p aria-live="polite">Loading your results…</p></div>;

  return (
    <div className="wrap report">
      <p className="section-label">Interview report</p>
      <div className="panel pad">
        <div className="report-hero">
          <div className="score-box" aria-hidden="true">{data.overall_score}<small>/100</small></div>
          <div>
            <h1 className="report-title">Overall score: {data.overall_score} out of 100</h1>
            <p className="muted" style={{ margin: 0 }}>
              <span className="badge">{data.label}</span>{' '}
              {data.job_title} · Technical · {data.difficulty} · {data.duration_min} min
            </p>
            <p className="muted small" style={{ margin: '8px 0 0' }}>
              {data.correct_count} of {data.total} answers met the keyword target · {data.answered_count} answered
              {data.missed_count > 0 && <> · {data.missed_count} skipped or not reached</>}
            </p>
          </div>
        </div>

        <div className="rband">
          <div className="rcard good"><h2 className="rcard-h">Strengths</h2><p>{data.strengths}</p></div>
          <div className="rcard grow"><h2 className="rcard-h">Where to improve</h2><p>{data.improvements}</p></div>
        </div>

        <div className="actions">
          <button className={`btn amber${retrying ? ' loading' : ''}`} type="button" onClick={() => void retry()} disabled={retrying}>
            {retrying ? 'Starting…' : 'Retry with same setup'}
          </button>
          <Link className="btn primary" href="/setup">Start a new session</Link>
        </div>
        {error && <p className="field-err" role="alert">{error}</p>}

        <h2 className="section-label" style={{ marginTop: 28 }}>Feedback for each answer</h2>
        <ol className="qlist">
          {data.answers.map((a) => (
            <li key={a.question_id} className="qcard">
              <div className="qcard-head">
                <span className="hs">{a.score}</span>
                <div className="grow">
                  <div className="hd">Question {a.q_index} · {a.category}</div>
                  <h3 className="ht">{a.prompt}</h3>
                </div>
                <span className={`pill ${a.correct ? 'good' : a.status === 'answered' ? 'mid' : 'bad'}`}>
                  {STATUS_TEXT[a.status]} · {a.score}/100
                </span>
              </div>
              {a.status === 'answered'
                ? <blockquote>{a.answer}</blockquote>
                : <p className="muted"><em>No answer was given for this question.</em></p>}
              {a.strengths && <p><b>Strength:</b> {a.strengths}</p>}
              <p><b>Improve:</b> {a.improvements}</p>
              <div className="kw">
                {a.matched.length > 0 && (
                  <p><span className="kw-l">Key terms you used</span>{a.matched.map((k) => <span key={k} className="chip good">{k}</span>)}</p>
                )}
                {a.missing.length > 0 && (
                  <p><span className="kw-l">Key terms to include</span>{a.missing.map((k) => <span key={k} className="chip">{k}</span>)}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
