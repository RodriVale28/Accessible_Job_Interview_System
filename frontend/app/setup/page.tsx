// S1-1.1 Interview setup page — owner: Kobra Amiri
'use client';

import { useRef, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { CodeIcon, PlayIcon } from '@/components/Icons';
import { startSession } from '../../lib/api';
import { FIELD_ORDER, validateSetup, type FieldErrors } from '../../lib/setupValidation';
import type { Difficulty, Duration } from '../../lib/types';

const DIFFICULTY_OPTIONS: { value: Difficulty; hint: string }[] = [
  { value: 'Easy', hint: 'Fundamentals' },
  { value: 'Medium', hint: 'Applied' },
  { value: 'Hard', hint: 'In depth' },
];

const DURATION_OPTIONS: { value: Duration; questions: number }[] = [
  { value: 15, questions: 5 },
  { value: 30, questions: 8 },
  { value: 45, questions: 10 },
];

export default function SetupPage() {
  const router = useRouter();
  const [jobTitle, setJobTitle] = useState('');
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [durationMin, setDurationMin] = useState<Duration | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const jobTitleRef = useRef<HTMLInputElement>(null);
  const difficultyRef = useRef<HTMLButtonElement>(null);
  const durationRef = useRef<HTMLButtonElement>(null);
  const fieldRefs = { jobTitle: jobTitleRef, difficulty: difficultyRef, durationMin: durationRef };

  const errorCount = Object.keys(fieldErrors).length;

  function clearFieldError(field: keyof FieldErrors) {
    setFieldErrors(({ [field]: _removed, ...rest }) => rest);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    const errors = validateSetup({
      jobTitle,
      difficulty: difficulty ?? undefined,
      durationMin: durationMin ?? undefined,
    });
    setFieldErrors(errors);
    const firstInvalid = FIELD_ORDER.find((field) => errors[field]);
    if (firstInvalid || !difficulty || !durationMin) {
      if (firstInvalid) fieldRefs[firstInvalid].current?.focus();
      return;
    }

    setLoading(true);

    try {
      const session = await startSession({
        job_title: jobTitle.trim(),
        difficulty,
        duration_min: durationMin,
      });

      router.push(`/session/${session.session_id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to start the interview. Please try again.'
      );
      setLoading(false);
    }
  }

  return (
    <section className="wrap hero" aria-labelledby="setup-title">
      <p className="section-label">Set up your session</p>

      <form className="panel pad" onSubmit={handleSubmit} noValidate>
        <h1 id="setup-title" className="card-title">Interview setup</h1>
        <p className="muted" style={{ margin: '-6px 0 20px' }}>
          Answer technical questions one at a time, then get a score and feedback on every answer.
        </p>

        {errorCount > 0 && (
          <div role="alert" className="alert">
            Please fix {errorCount} {errorCount === 1 ? 'field' : 'fields'} before starting.
          </div>
        )}

        <div className="setup-grid">
          <div>
            <div className="opt-group">
              <label htmlFor="jobTitle" className="glabel">Job title</label>
              <input
                id="jobTitle"
                ref={jobTitleRef}
                type="text"
                required
                maxLength={120}
                autoComplete="organization-title"
                value={jobTitle}
                onChange={(e) => {
                  setJobTitle(e.target.value);
                  if (fieldErrors.jobTitle) clearFieldError('jobTitle');
                }}
                placeholder="e.g. Junior Software Engineer"
                aria-invalid={fieldErrors.jobTitle ? true : undefined}
                aria-describedby={fieldErrors.jobTitle ? 'jobTitle-error' : undefined}
              />
              {fieldErrors.jobTitle && (
                <p id="jobTitle-error" className="field-err">{fieldErrors.jobTitle}</p>
              )}
            </div>

            <div className="opt-group">
              <span className="glabel">Interview type</span>
              <div className="tracks">
                <div className="track">
                  <span className="ico"><CodeIcon /></span>
                  <span>
                    <span className="tt">Technical</span>
                    <span className="td">Problem-solving and core CS concepts</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="opt-group">
              <span className="glabel" id="difficulty-label">Difficulty</span>
              <div
                className="seg"
                role="group"
                aria-labelledby="difficulty-label"
                aria-describedby={fieldErrors.difficulty ? 'difficulty-error' : undefined}
                data-invalid={fieldErrors.difficulty ? 'true' : undefined}
              >
                {DIFFICULTY_OPTIONS.map((opt, i) => (
                  <button
                    key={opt.value}
                    ref={i === 0 ? difficultyRef : undefined}
                    type="button"
                    aria-pressed={difficulty === opt.value}
                    onClick={() => {
                      setDifficulty(opt.value);
                      if (fieldErrors.difficulty) clearFieldError('difficulty');
                    }}
                  >
                    {opt.value}
                    <small>{opt.hint}</small>
                  </button>
                ))}
              </div>
              {fieldErrors.difficulty && (
                <p id="difficulty-error" className="field-err">{fieldErrors.difficulty}</p>
              )}
            </div>

            <div className="opt-group">
              <span className="glabel" id="duration-label">Length</span>
              <div
                className="seg"
                role="group"
                aria-labelledby="duration-label"
                aria-describedby={fieldErrors.durationMin ? 'duration-error' : undefined}
                data-invalid={fieldErrors.durationMin ? 'true' : undefined}
              >
                {DURATION_OPTIONS.map((opt, i) => (
                  <button
                    key={opt.value}
                    ref={i === 0 ? durationRef : undefined}
                    type="button"
                    aria-pressed={durationMin === opt.value}
                    onClick={() => {
                      setDurationMin(opt.value);
                      if (fieldErrors.durationMin) clearFieldError('durationMin');
                    }}
                  >
                    {opt.value} min
                    <small>{opt.questions} questions</small>
                  </button>
                ))}
              </div>
              {fieldErrors.durationMin && (
                <p id="duration-error" className="field-err">{fieldErrors.durationMin}</p>
              )}
            </div>
          </div>
        </div>

        {error && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className={`btn amber full${loading ? ' loading' : ''}`}
          style={{ marginTop: 6 }}
        >
          {!loading && <PlayIcon />}
          {loading ? 'Starting interview…' : 'Begin Interview'}
        </button>
      </form>
    </section>
  );
}