// S1-1.1 Interview setup page - owner: Kobra Amiri (validation: S1-1.3 Blake Hawkins)
'use client';
import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { startSession } from '@/lib/api';
import { DIFFICULTIES, DURATIONS, FIELD_ORDER, validateSetup, type FieldErrors } from '@/lib/setupValidation';
import { CodeIcon, PlayIcon } from '@/components/Icons';
import type { Difficulty, Duration } from '@/lib/types';

const DIFFICULTY_HINT: Record<Difficulty, string> = {
  Easy: 'Core definitions',
  Medium: 'Compare and explain',
  Hard: 'Deeper trade-offs',
};
const FOCUS_ID = { jobTitle: 'jobTitle', difficulty: 'difficulty-Easy', durationMin: 'duration-15' } as const;
const DURATION_HINT: Record<Duration, string> = { 15: '5 questions', 30: '8 questions', 45: '10 questions' };

export default function SetupPage() {
  const router = useRouter();
  const [jobTitle, setJobTitle] = useState('');
  const [difficulty, setDifficulty] = useState<Difficulty | ''>('');
  const [durationMin, setDurationMin] = useState<Duration | 0>(0);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState('');
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setServerError('');
    const found = validateSetup({ jobTitle, difficulty: difficulty || undefined, durationMin: durationMin || undefined });
    setErrors(found);
    const first = FIELD_ORDER.find((f) => found[f]);
    if (first) {
      document.getElementById(FOCUS_ID[first])?.focus();
      return;
    }
    setBusy(true);
    try {
      const s = await startSession({
        job_title: jobTitle.trim(),
        difficulty: difficulty as Difficulty,
        duration_min: durationMin as Duration,
      });
      router.push(`/session/${s.session_id}`);
    } catch (err) {
      setServerError((err as Error).message);
      setBusy(false);
    }
  }

  const errorCount = Object.keys(errors).length;

  return (
    <div className="wrap hero">
      <h1 className="sr-only">Set up your technical interview</h1>
      <p className="section-label">Set up your session</p>

      {errorCount > 0 && (
        <div className="alert" role="alert">Please fix {errorCount} {errorCount === 1 ? 'field' : 'fields'} below.</div>
      )}
      {serverError && <div className="alert" role="alert">{serverError}</div>}

      <form className="panel pad" onSubmit={onSubmit} noValidate>
        <div className="setup-grid">
          <div>
            <div className="opt-group">
              <span className="glabel" id="track-label">Interview track</span>
              <div className="tracks" role="group" aria-labelledby="track-label">
                <div className="track" aria-current="true">
                  <span className="ico"><CodeIcon /></span>
                  <span><span className="tt">Technical</span><span className="td">Typed answers · Sprint 1</span></span>
                </div>
              </div>
            </div>

            <div className="opt-group">
              <label className="glabel" htmlFor="jobTitle">Job title</label>
              <input
                id="jobTitle"
                type="text"
                value={jobTitle}
                maxLength={120}
                autoComplete="organization-title"
                placeholder="e.g. Junior Software Engineer"
                onChange={(e) => setJobTitle(e.target.value)}
                aria-invalid={!!errors.jobTitle}
                aria-describedby={errors.jobTitle ? 'jobTitle-error' : undefined}
                required
              />
              {errors.jobTitle && <p id="jobTitle-error" className="field-err">{errors.jobTitle}</p>}
            </div>
          </div>

          <div>
            <div className="opt-group">
              <span className="glabel" id="difficulty-label">Difficulty</span>
              <div className="seg" role="group" aria-labelledby="difficulty-label"
                aria-describedby={errors.difficulty ? 'difficulty-error' : undefined} data-invalid={!!errors.difficulty}>
                {DIFFICULTIES.map((d) => (
                  <button key={d} id={`difficulty-${d}`} type="button" aria-pressed={difficulty === d}
                    onClick={() => setDifficulty(d)}>
                    {d}<small>{DIFFICULTY_HINT[d]}</small>
                  </button>
                ))}
              </div>
              {errors.difficulty && <p id="difficulty-error" className="field-err">{errors.difficulty}</p>}
            </div>

            <div className="opt-group">
              <span className="glabel" id="duration-label">Length</span>
              <div className="seg" role="group" aria-labelledby="duration-label"
                aria-describedby={errors.durationMin ? 'duration-error' : undefined} data-invalid={!!errors.durationMin}>
                {DURATIONS.map((m) => (
                  <button key={m} id={`duration-${m}`} type="button" aria-pressed={durationMin === m}
                    onClick={() => setDurationMin(m)}>
                    {m} min<small>{DURATION_HINT[m]}</small>
                  </button>
                ))}
              </div>
              {errors.durationMin && <p id="duration-error" className="field-err">{errors.durationMin}</p>}
            </div>
          </div>
        </div>

        <button className={`btn amber full${busy ? ' loading' : ''}`} type="submit" disabled={busy} aria-busy={busy}>
          {!busy && <PlayIcon />}{busy ? 'Starting…' : 'Begin Interview'}
        </button>
      </form>
    </div>
  );
}
