// S1-0.1 / US-4: the signed-in user's saved interviews, so results can be reopened later.
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listSessions } from '../lib/api';
import { supabase } from '../lib/supabase';
import type { SessionSummary } from '../lib/types';

export function PastInterviews() {
  const [rows, setRows] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState('');

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
      <ul style={{ paddingLeft: 18, lineHeight: 1.9 }}>
        {rows.map((s) => {
          const done = s.status === 'completed';
          const when = new Date(s.started_at).toLocaleDateString();
          return (
            <li key={s.session_id}>
              <Link href={done ? `/results/${s.session_id}` : `/session/${s.session_id}`}>
                {s.job_title}
              </Link>
              <span className="muted">
                {' '}· {s.difficulty} · {s.duration_min} min · {when} ·{' '}
                {done ? `Score ${s.overall_score ?? 0}` : 'Not finished'}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
