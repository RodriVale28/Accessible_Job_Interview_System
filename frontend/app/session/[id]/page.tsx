// S1-3.1 Interview session page - owner: Hongli Pan (submit flow: S1-3.2 Jayme Nguyen)
'use client';
import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ApiError, completeSession, getSession } from '@/lib/api';
import { submitAnswer } from '@/lib/submitAnswer';
import { ClockIcon, SendIcon } from '@/components/Icons';
import type { Question, SessionState } from '@/lib/types';

type Msg = { id: number; who: 'ai' | 'me'; text: string; label?: string; kind?: 'intro' | 'note' | 'question' };

function fmt(sec: number) {
  return `${Math.floor(sec / 60)}:${(sec % 60).toString().padStart(2, '0')}`;
}

let msgId = 0;
const msg = (m: Omit<Msg, 'id'>): Msg => ({ ...m, id: ++msgId });
const questionMsg = (q: Question, idx: number, total: number) =>
  msg({ who: 'ai', kind: 'question', text: q.prompt, label: `Question ${idx} of ${total} · ${q.category}` });

export default function SessionPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [state, setState] = useState<SessionState | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [answered, setAnswered] = useState(0);
  const [loadError, setLoadError] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [deadline, setDeadline] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const finishing = useRef(false);

  const finish = useCallback(async () => {
    if (finishing.current) return;
    finishing.current = true;
    setBusy(true);
    setMessages((m) => [...m, msg({ who: 'ai', kind: 'note', text: 'Thanks, that’s the end of the interview. Scoring your answers…' })]);
    try {
      await completeSession(id);
      router.push(`/results/${id}`);
    } catch (e) {
      finishing.current = false;
      setBusy(false);
      setError((e as Error).message);
    }
  }, [id, router]);

  useEffect(() => {
    let alive = true;
    getSession(id)
      .then((s) => {
        if (!alive) return;
        if (s.status === 'completed') {
          router.replace(`/results/${id}`);
          return;
        }
        if (!s.question) {
          // Every question is answered but the interview was never finished
          // (tab closed, or completing failed): finish it now.
          completeSession(id)
            .then(() => alive && router.replace(`/results/${id}`))
            .catch((e: Error) => alive && setLoadError(e.message));
          return;
        }
        setState(s);
        setAnswered(s.q_index - 1);
        setDeadline(Date.now() + s.seconds_left * 1000);
        setMessages([
          msg({
            who: 'ai', kind: 'intro',
            text: s.q_index === 1
              ? `Hi! This is ${s.difficulty === 'Easy' ? 'an' : 'a'} ${s.difficulty.toLowerCase()} technical interview for ${s.job_title}. I’ll ask ${s.total} questions, one at a time. Take your time, and name the key terms you know.`
              : `Welcome back. Picking up where you left off: ${s.q_index - 1} of ${s.total} answered.`,
          }),
          questionMsg(s.question, s.q_index, s.total),
        ]);
      })
      .catch((e: Error) => alive && setLoadError(e.message));
    return () => { alive = false; };
  }, [id, router]);

  // countdown; when time runs out the interview is scored automatically
  useEffect(() => {
    if (!deadline) return;
    const t = window.setInterval(() => {
      const n = Date.now();
      setNow(n);
      if (n >= deadline) { window.clearInterval(t); void finish(); }
    }, 1000);
    return () => window.clearInterval(t);
  }, [deadline, finish]);

  // keep the newest message in view
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

  const secondsLeft = deadline ? Math.max(0, Math.round((deadline - now) / 1000)) : 0;
  const announce = !deadline ? '' : secondsLeft === 0 ? 'Time is up. Scoring your interview.'
    : secondsLeft <= 60 ? '1 minute left.' : secondsLeft <= 300 ? '5 minutes left.' : '';

  async function send(text: string) {
    if (!state?.question || busy) return;
    setBusy(true);
    setError('');
    setMessages((m) => [...m, msg({ who: 'me', text: text.trim() || '(skipped)' })]);
    setAnswer('');
    try {
      const r = await submitAnswer(state.session_id, state.question.id, text);
      setAnswered(r.answered);
      if (r.completed || !r.question) {
        setState({ ...state, correct_count: r.correct_count });
        await finish();
        return;
      }
      setState({ ...state, question: r.question, q_index: r.q_index, correct_count: r.correct_count });
      setMessages((m) => [
        ...m,
        msg({ who: 'ai', kind: 'note', text: r.blank ? 'No problem, let’s move on.' : 'Got it, answer saved.' }),
        questionMsg(r.question!, r.q_index, state.total),
      ]);
      setBusy(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    } catch (e) {
      // Time ran out (server side) or the interview was ended in another tab: go to results.
      if (e instanceof ApiError && e.status === 409 && /Time is up|already finished/.test(e.message)) {
        await finish();
        return;
      }
      setMessages((m) => m.slice(0, -1));
      setAnswer(text);
      setBusy(false);
      setError(`${(e as Error).message} Your answer is back in the box - press Send to try again.`);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!answer.trim()) {
      setError('Type an answer first, or choose "Skip question" to leave it unanswered.');
      inputRef.current?.focus();
      return;
    }
    void send(answer);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      e.currentTarget.form?.requestSubmit();
    }
  }

  if (loadError) {
    return (
      <div className="wrap hero">
        <div className="panel pad">
          <h1 className="card-title">We couldn&apos;t open this interview</h1>
          <p role="alert">{loadError}</p>
          <Link className="btn amber" href="/setup">Start a new interview</Link>
        </div>
      </div>
    );
  }
  if (!state || !state.question) return <div className="wrap hero"><p aria-live="polite">Loading your interview…</p></div>;

  const pct = Math.round((answered / state.total) * 100);
  const clockCls = secondsLeft === 0 ? ' up' : secondsLeft <= 120 ? ' low' : '';

  return (
    <div className="wrap session">
      <h1 className="sr-only">Technical interview: {state.job_title}</h1>
      <div className="panel stage simple">
        <div className="chat-col">
          <div className="chat-head">
            <div>
              <div className="who">Interviewer</div>
              <div className="role">{state.job_title} · Technical · {state.difficulty}</div>
            </div>
            <span className={`clock${clockCls}`} role="timer" aria-label={`Time left ${fmt(secondsLeft)}`}>
              <ClockIcon /><span>{secondsLeft === 0 ? "Time's up" : fmt(secondsLeft)}</span>
            </span>
            <span className="qcount">Q <b>{state.q_index}</b>/{state.total}</span>
          </div>
          <div className="progress-row">
            <div
              className="bar"
              role="progressbar"
              aria-label="Interview progress"
              aria-valuemin={0}
              aria-valuemax={state.total}
              aria-valuenow={answered}
              aria-valuetext={`Question ${state.q_index} of ${state.total}`}
            ><i style={{ width: `${pct}%` }} /></div>
            <span className="small muted">Correct so far: <b>{state.correct_count}</b></span>
          </div>

          <div className="messages" ref={logRef} role="log" aria-live="polite" aria-label="Interview conversation">
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.who}${m.kind ? ' ' + m.kind : ''}`}>
                <div>
                  <div className="name">
                    {m.who === 'ai' ? 'Interviewer' : 'You'}
                    {m.label && <span className="qlabel">· {m.label}</span>}
                  </div>
                  <div className="b">{m.text}</div>
                </div>
              </div>
            ))}
            {busy && (
              <div className="msg ai" aria-hidden="true"><div className="b muted">Saving…</div></div>
            )}
          </div>

          <form className="answer-area" onSubmit={onSubmit}>
            <div className="assist-row">
              <span className="spacer" />
              <button className="guide-btn" type="button" disabled={busy} onClick={() => void send('')}>Skip question</button>
              <button className="guide-btn end" type="button" disabled={busy} onClick={() => void finish()}>End now</button>
            </div>
            <div className="composer">
              <div className="inpwrap">
                <label className="sr-only" htmlFor="answer">Your answer</label>
                <textarea
                  id="answer"
                  ref={inputRef}
                  rows={2}
                  value={answer}
                  maxLength={5000}
                  placeholder="Type your answer…"
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={onKeyDown}
                  aria-describedby="kbd-hint"
                  aria-invalid={!!error && !answer.trim()}
                  disabled={busy}
                />
                <button className="send" type="submit" disabled={busy} aria-label={state.q_index === state.total ? 'Send answer and finish' : 'Send answer'}>
                  <SendIcon />
                </button>
              </div>
            </div>
            {error && <p className="field-err pad-x" role="alert">{error}</p>}
            <div className="hint" id="kbd-hint"><kbd>Enter</kbd> to send · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line</div>
          </form>
        </div>

      </div>
      <p className="sr-only" aria-live="assertive">{announce}</p>
    </div>
  );
}
