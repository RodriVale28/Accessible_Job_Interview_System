// S1-0.1 / US-4: the signed-in user's saved interviews, so results can be reopened later.
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { discardSession, listSessions } from '../lib/api';
import { supabase } from '../lib/supabase';
import type { SessionSummary } from '../lib/types';

export function PastInterviews() {
  const [rows, setRows] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState('');
  const [discardingId, setDiscardingId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function confirmDiscard(sessionId: number) {
    setBusyId(sessionId);
    setError('');
    try {
      await discardSession(sessionId);
      setRows((current) => current?.filter((row) => row.session_id !== sessionId) ?? null);
      setDiscardingId(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not discard this interview. Please try again.');
    } finally {
      setBusyId(null);
    }
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // signed out: nothing to show (and no redirect from the landing page)
      if (supabase && !(await supabase.auth.getSession()).data.session) return;
      try {
        const list = await listSessions();
        if (!cancelled) setRows(list);
      } catch {
        if (!cancelled) setError('Could not load your past interviews.');
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (error) return <p className="muted" role="status">{error}</p>;
  if (!rows?.length) return null;

  return (
    <section className="panel pad" aria-labelledby="past-title" style={{ marginTop: 28, textAlign: 'left' }}>
      <h2 id="past-title" className="card-title">Your past interviews</h2>
      {error && <p className="alert" role="alert">{error}</p>}
      <ul className="past-list">
        {rows.map((s) => {
          const done = s.status === 'completed';
          const when = new Date(s.started_at).toLocaleDateString();
          return (
            <li className="past-row" key={s.session_id}>
              <div>
                <h3>{done
                  ? <Link href={`/results/${s.session_id}`}>{s.job_title}</Link>
                  : (s.role_name || s.job_title)}</h3>
                <p className="muted">{s.role_name || s.job_title} · {s.interview_type} · {s.difficulty} · {s.duration_min} min · {when} · {done ? `Score ${s.overall_score ?? 0}` : 'In progress'}</p>
              </div>
              <div className="past-actions">
                {done ? <Link className="btn primary" href={`/results/${s.session_id}`}>View results</Link> : <>
                  <Link className="btn primary" href={`/session/${s.session_id}`}>Resume</Link>
                  {discardingId === s.session_id ? (
                    <div className="discard-confirm" role="group" aria-label={`Confirm discard of ${s.role_name || s.job_title} interview`}>
                      <span role="status">Discard this unfinished interview?</span>
                      <button className="btn amber" type="button" onClick={() => void confirmDiscard(s.session_id)} disabled={busyId === s.session_id}>{busyId === s.session_id ? 'Discarding…' : 'Yes, discard'}</button>
                      <button className="btn primary" type="button" onClick={() => setDiscardingId(null)} disabled={busyId === s.session_id}>Keep interview</button>
                    </div>
                  ) : <button className="btn primary" type="button" onClick={() => setDiscardingId(s.session_id)}>Discard</button>}
                </>}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
