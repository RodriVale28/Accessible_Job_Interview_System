'use client';

import { FormEvent, KeyboardEvent, useEffect, useState } from 'react';

const QUESTIONS = [
  'Tell me about a time you had to solve a difficult problem at work.',
  'Describe a situation where you had to work with someone whose approach differed from yours.',
  'Tell me about a project you are proud of. What was your contribution?',
  'What is a skill you are currently working to improve, and how are you developing it?',
];
const DURATIONS = [15, 30, 45] as const;

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  return reduced;
}

export default function SessionPage() {
  const reducedMotion = usePrefersReducedMotion();
  const [duration, setDuration] = useState<(typeof DURATIONS)[number]>(30);
  const [secondsLeft, setSecondsLeft] = useState(30 * 60);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [answers, setAnswers] = useState<string[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const finished = questionIndex >= QUESTIONS.length;

  useEffect(() => {
    if (secondsLeft <= 0 || finished) return;
    const timer = window.setInterval(() => setSecondsLeft((time) => Math.max(0, time - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [secondsLeft, finished]);

  useEffect(() => {
    if (!analyzing) return;
    const timer = window.setTimeout(() => setAnalyzing(false), reducedMotion ? 0 : 900);
    return () => window.clearTimeout(timer);
  }, [analyzing, reducedMotion]);

  function changeDuration(value: string) {
    const minutes = Number(value) as (typeof DURATIONS)[number];
    setDuration(minutes);
    setSecondsLeft(minutes * 60);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = answer.trim();
    if (!value || finished || analyzing) return;
    setAnswers((previous) => [...previous, value]);
    setAnswer('');
    setQuestionIndex((index) => index + 1);
    if (questionIndex + 1 < QUESTIONS.length) setAnalyzing(true);
  }

  function onAnswerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const time = `${Math.floor(secondsLeft / 60).toString().padStart(2, '0')}:${(secondsLeft % 60).toString().padStart(2, '0')}`;
  const progress = Math.min(questionIndex, QUESTIONS.length);

  return (
    <main className="session-page">
      <style>{`
        * { box-sizing: border-box; }
        .session-page { min-height:100vh; padding:32px 20px; background:#f5f7fb; color:#182230; font:16px/1.5 system-ui,sans-serif; }
        .session-shell { max-width:850px; margin:0 auto; }
        .session-top { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:20px; }
        .session-top h1 { font-size:1.25rem; margin:0; }
        .session-tools { display:flex; align-items:center; gap:16px; }
        .session-tools label { display:flex; align-items:center; gap:8px; }
        .session-card { background:white; border:1px solid #dce2ec; border-radius:16px; padding:clamp(20px,5vw,40px); box-shadow:0 8px 28px #1822300a; }
        .progress-line { height:8px; background:#e8edf4; border-radius:8px; overflow:hidden; margin:10px 0 8px; }
        .progress-line span { display:block; height:100%; background:#3659c9; transition:width .25s ease; }
        .progress-label { display:flex; justify-content:space-between; color:#526174; font-size:.9rem; }
        .question { font-size:clamp(1.3rem,3vw,1.8rem); line-height:1.35; margin:38px 0 28px; }
        .answer-label { display:block; font-weight:600; margin-bottom:8px; }
        .answer-box { width:100%; min-height:170px; resize:vertical; border:1px solid #aeb9c9; border-radius:10px; padding:14px; font:inherit; }
        .answer-box:focus, select:focus { outline:3px solid #a8bafa; outline-offset:2px; }
        .form-footer { display:flex; justify-content:space-between; align-items:center; gap:16px; margin-top:14px; color:#526174; font-size:.9rem; }
        .submit-button { border:0; border-radius:9px; background:#294dbd; color:white; font:inherit; font-weight:650; padding:11px 20px; cursor:pointer; }
        .submit-button:disabled { opacity:.5; cursor:not-allowed; }
        .status { margin-top:22px; min-height:28px; color:#526174; }
        .typing-dots span { display:inline-block; width:7px; height:7px; margin:0 3px; border-radius:50%; background:#526174; animation:bounce .8s infinite alternate; }
        .typing-dots span:nth-child(2) { animation-delay:.2s; } .typing-dots span:nth-child(3) { animation-delay:.4s; }
        @keyframes bounce { to { transform:translateY(-5px); opacity:.45; } }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
        @media (max-width:560px) { .session-top { align-items:flex-start; flex-direction:column; } .session-tools { width:100%; justify-content:space-between; } .form-footer { align-items:flex-start; flex-direction:column; } }
      `}</style>
      <div className="session-shell">
        <header className="session-top">
          <h1>Interview session</h1>
          <div className="session-tools">
            <label htmlFor="duration">Duration
              <select id="duration" value={duration} onChange={(event) => changeDuration(event.target.value)}>
                {DURATIONS.map((minutes) => <option key={minutes} value={minutes}>{minutes} minutes</option>)}
              </select>
            </label>
            <span role="timer" aria-label={`${Math.floor(secondsLeft / 60)} minutes ${secondsLeft % 60} seconds remaining`}>Time {time}</span>
          </div>
        </header>
        <section className="session-card" aria-labelledby="question-heading">
          <div className="progress-label"><span>Interview progress</span><span>Question {Math.min(progress + (finished ? 0 : 1), QUESTIONS.length)} of {QUESTIONS.length}</span></div>
          <div className="progress-line" role="progressbar" aria-label="Interview progress" aria-valuemin={0} aria-valuemax={QUESTIONS.length} aria-valuenow={progress}><span style={{ width: `${(progress / QUESTIONS.length) * 100}%` }} /></div>
          {finished ? <div role="status"><h2 id="question-heading">Interview complete</h2><p>You answered {answers.length} questions. Your responses are saved for this session.</p></div> : <>
            <h2 className="question" id="question-heading">{QUESTIONS[questionIndex]}</h2>
            <form onSubmit={submit}>
              <label className="answer-label" htmlFor="answer">Your answer</label>
              <textarea id="answer" className="answer-box" value={answer} onChange={(event) => setAnswer(event.target.value)} onKeyDown={onAnswerKeyDown} placeholder="Type your answer here…" disabled={analyzing || secondsLeft === 0} aria-describedby="answer-hint" />
              <div className="form-footer"><span id="answer-hint">Press Enter to submit. Use Shift+Enter for a new line.</span><button className="submit-button" type="submit" disabled={!answer.trim() || analyzing || secondsLeft === 0}>Submit answer</button></div>
            </form>
            <div className="status" role="status" aria-live="polite">{secondsLeft === 0 ? 'Time is up.' : analyzing ? <><span>Ava is analyzing your answer…</span>{!reducedMotion && <span className="typing-dots" aria-hidden="true"><i /><i /><i /></span>}</> : null}</div>
          </>}
        </section>
      </div>
    </main>
  );
}
