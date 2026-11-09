// S1-3.1 Interview session page - owner: Hongli Pan (submit flow: S1-3.2 Jayme Nguyen)
'use client';
import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ApiError, completeSession, getSession } from '@/lib/api';
import { submitAnswer } from '@/lib/submitAnswer';
import { ClockIcon, SendIcon } from '@/components/Icons';
import ReadAloud from '@/components/ReadAloud';
import { DIFFICULTY_LABEL, type Question, type SessionState } from '@/lib/types';

type Msg = { id: number; who: 'ai' | 'me'; text: string; label?: string; kind?: 'intro' | 'note' | 'question' };

function fmt(sec: number) {
  return `${Math.floor(sec / 60)}:${(sec % 60).toString().padStart(2, '0')}`;
}

// What the user typed but has not sent yet, kept per interview so "Leave and resume later" does not lose it.
const draftKey = (id: string) => `interview-studio-draft-${id}`;
function loadDraft(id: string, qid: number) {
  try {
    const d = JSON.parse(window.localStorage.getItem(draftKey(id)) ?? 'null') as { qid?: number; text?: unknown } | null;
    return d?.qid === qid && typeof d.text === 'string' ? d.text : '';
  } catch { return ''; }
}
function saveDraft(id: string, qid: number, text: string) {
  try {
    if (text) window.localStorage.setItem(draftKey(id), JSON.stringify({ qid, text }));
    else window.localStorage.removeItem(draftKey(id));
  } catch { /* storage blocked: the draft just is not kept */ }
}
const clearDraft = (id: string) => saveDraft(id, 0, '');

// The job title the user typed, plus the matched role when it is a different name (results show the typed title).
function jobLabel(s: SessionState) {
  const title = s.job_title || s.role_name || '';
  return s.role_name && s.role_name.toLowerCase() !== title.toLowerCase() ? `${title} (${s.role_name})` : title;
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
  const [live, setLive] = useState(''); // polite status for screen readers: saving, next question, ending
  const [timerNote, setTimerNote] = useState(''); // "5 minutes left", said once per threshold
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const questionRef = useRef<HTMLDivElement>(null);
  const focusedFirst = useRef(false);
  const finishing = useRef(false);
  const closingShown = useRef(false);
  const sending = useRef(false);
  const inflight = useRef<Promise<void>>(Promise.resolve());
  const draft = useRef<{ qid?: number; text: string }>({ text: '' });

  const finish = useCallback(async (timeUp = false) => {
    if (finishing.current) return;
    finishing.current = true;
    setBusy(true);
    const closing = timeUp ? 'Time is up. We’ll prepare your results…' : 'Thanks, that’s the end of the interview. We’ll prepare your results…';
    if (!closingShown.current) {
      closingShown.current = true; // a failed finish that is retried must not repeat the message
      setMessages((m) => [...m, msg({ who: 'ai', kind: 'note', text: closing })]);
    }
    setLive(closing);
    try {
      await completeSession(id);
      clearDraft(id);
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
        const saved = loadDraft(id, s.question.id);
        if (saved) setAnswer(saved);
        draft.current = { qid: s.question.id, text: saved };
        setState(s);
        setAnswered(s.q_index - 1);
        if (s.timed && s.seconds_left !== null) setDeadline(Date.now() + s.seconds_left * 1000);
        setMessages([
          msg({
            who: 'ai', kind: 'intro',
            text: (s.q_index === 1
              ? `Hi! This is a ${s.interview_type.toLowerCase()} interview (${DIFFICULTY_LABEL[s.difficulty]} level) for ${jobLabel(s)}. I’ll ask ${s.total} questions, one at a time. Take your time, and explain your thinking.`
              : `Welcome back. Picking up where you left off: ${s.q_index - 1} of ${s.total} answered.`)
              + (saved ? ' Your unsent draft is back in the answer box.' : ''),
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
    let prev = Math.round((deadline - Date.now()) / 1000);
    const t = window.setInterval(() => {
      const n = Date.now();
      setNow(n);
      // only a real crossing is announced, so resuming with 4 minutes left says nothing
      const left = Math.max(0, Math.round((deadline - n) / 1000));
      if (prev > 60 && left <= 60 && left > 0) setTimerNote('1 minute left.');
      else if (prev > 300 && left <= 300 && left > 60) setTimerNote('5 minutes left.');
      prev = left;
      if (n >= deadline) {
        window.clearInterval(t);
        void (async () => {
          await inflight.current; // an answer that is already being sent must be saved before the interview ends
          // Save what was typed so the last answer is not lost (the server allows a short grace period).
          const { qid, text } = draft.current;
          if (qid && text.trim()) await submitAnswer(id, qid, text.trim()).catch(() => undefined);
          await finish(true);
        })();
      }
    }, 1000);
    return () => window.clearInterval(t);
  }, [deadline, finish, id]);

  useEffect(() => { draft.current = { qid: state?.question?.id, text: answer }; }, [state, answer]);

  // On load, focus the current question: it is read out, which a log that mounts already filled is not.
  useEffect(() => {
    if (state && !focusedFirst.current) { focusedFirst.current = true; questionRef.current?.focus(); }
  }, [state]);

  // keep the newest message in view
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, busy]);

  const secondsLeft = deadline ? Math.max(0, Math.round((deadline - now) / 1000)) : 0;

  function send(text: string) {
    if (!state?.question || sending.current || finishing.current) return;
    sending.current = true;
    inflight.current = doSend(state, state.question, text, answer);
  }

  async function doSend(state: SessionState, question: Question, text: string, typed: string) {
    setBusy(true);
    setError('');
    setLive('Saving your answer…');
    setMessages((m) => [...m, msg({ who: 'me', text: text.trim() || '(skipped)' })]);
    setAnswer('');
    try {
      const r = await submitAnswer(state.session_id, question.id, text);
      clearDraft(id);
      setAnswered(r.answered);
      if (r.completed || !r.question) {
        setState({ ...state, correct_count: r.correct_count });
        await finish();
        return;
      }
      setState({ ...state, question: r.question, q_index: r.q_index, correct_count: r.correct_count });
      const note = r.blank ? 'No problem, let’s move on.' : 'Got it, answer saved.';
      const next = questionMsg(r.question!, r.q_index, state.total);
      setMessages((m) => [...m, msg({ who: 'ai', kind: 'note', text: note }), next]);
      setLive(`${note} ${next.label}. ${next.text}`);
      setError('');
      setBusy(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        if (/not the current question/.test(e.message)) {
          window.location.reload();
          return;
        }
        // Time ran out (server side) or the interview was ended in another tab: go to results.
        await finish();
        return;
      }
      const back = text || typed; // a failed Skip must not lose what was typed
      setMessages((m) => m.slice(0, -1));
      setAnswer(back);
      draft.current = { qid: question.id, text: back };
      setBusy(false);
      setLive('');
      setError(text
        ? `${(e as Error).message} Your answer is back in the box - press Send to try again.`
        : `${(e as Error).message} Your question was not skipped - choose "Skip question" to try again.`);
      if (text) requestAnimationFrame(() => inputRef.current?.focus());
    } finally {
      sending.current = false;
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (sending.current || finishing.current) return; // a second Enter while sending must do nothing
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
  const qid = state.question.id;
  let lastQuestionId = -1;
  for (const m of messages) if (m.kind === 'question') lastQuestionId = m.id;
  const clockCls = secondsLeft === 0 ? ' up' : secondsLeft <= 120 ? ' low' : '';

  return (
    <div className="wrap session">
      <h1 className="sr-only">{state.interview_type} interview: {jobLabel(state)}</h1>
      <div className="panel stage simple">
        <div className="chat-col">
          <div className="chat-head">
            <div>
              <div className="who">Interviewer</div>
              <div className="role">{jobLabel(state)} · {state.interview_type} · {DIFFICULTY_LABEL[state.difficulty]}</div>
            </div>
            {state.timed && <span className={`clock${clockCls}`} role="timer" aria-label={`Time left ${fmt(secondsLeft)}`}>
              <ClockIcon /><span>{secondsLeft === 0 ? 'Time is up' : fmt(secondsLeft)}</span>
            </span>}
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
            <span className="small muted">{answered} of {state.total} answered</span>
          </div>

          <div className="messages" ref={logRef} role="log" aria-live="off" tabIndex={0} aria-label="Interview conversation">
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.who}${m.kind ? ' ' + m.kind : ''}`}
                ref={m.id === lastQuestionId ? questionRef : undefined} tabIndex={m.id === lastQuestionId ? -1 : undefined}>
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

          <div className="question-tools">
            <ReadAloud text={state.question.prompt} label="Read question aloud" />
          </div>

          <form className="answer-area" onSubmit={onSubmit}>
            <div className="assist-row">
              <span className="spacer" />
              <Link className="guide-btn" href="/">Leave and resume later</Link>
              <button className="guide-btn" type="button" aria-disabled={busy} onClick={() => send('')}>Skip question</button>
              <button className="guide-btn end" type="button" aria-disabled={busy} onClick={() => { if (!sending.current && !finishing.current && window.confirm('End the interview now? Questions you have not answered will count as 0.')) void finish(); }}>End now</button>
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
                  onChange={(e) => { setAnswer(e.target.value); saveDraft(id, qid, e.target.value); }}
                  onKeyDown={onKeyDown}
                  aria-describedby={error ? 'answer-error kbd-hint' : 'kbd-hint'}
                  aria-invalid={!!error && !answer.trim()}
                  readOnly={busy}
                />
                <button className="send" type="submit" aria-disabled={busy} aria-label={state.q_index === state.total ? 'Send answer and finish' : 'Send answer'}>
                  <SendIcon />
                </button>
              </div>
            </div>
            {error && <p className="field-err pad-x" id="answer-error" role="alert">{error}</p>}
            <div className="hint" id="kbd-hint"><kbd>Enter</kbd> to send · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line</div>
          </form>
        </div>

      </div>
      <p className="sr-only" role="status">{live}</p>
      <p className="sr-only" aria-live="assertive">{timerNote}</p>
    </div>
  );
}
