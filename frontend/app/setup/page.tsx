
// S2-1.5 Interview setup page — owner: Kobra Amiri
'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { getRoles, matchRole, startSession } from '../../lib/api';
import {
  FIELD_ORDER,
  validateSetup,
  type FieldErrors,
} from '../../lib/setupValidation';
import type {
  Difficulty,
  Duration,
  InterviewType,
  Role,
} from '../../lib/types';

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: 'Easy', label: 'Warm-up' },
  { value: 'Medium', label: 'Standard' },
  { value: 'Hard', label: 'Challenge' },
];

const LENGTHS: {
  value: Duration;
  label: string;
  questions: number;
}[] = [
  { value: 15, label: 'Short', questions: 5 },
  { value: 30, label: 'Medium', questions: 8 },
  { value: 45, label: 'Long', questions: 10 },
];

const TYPES: InterviewType[] = [
  'Technical',
  'Behavioral',
  'Mixed',
];

export default function SetupPage() {
  const router = useRouter();

  const [jobTitle, setJobTitle] = useState('');
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] = useState(true);
  const rolesAvailable = roles.length > 0;
  const [roleId, setRoleId] = useState<number | null>(null);
  const [roleMessage, setRoleMessage] = useState('');
  const [matching, setMatching] = useState(false);

  const [interviewType, setInterviewType] =
    useState<InterviewType>('Mixed');
  const [typeChosenByUser, setTypeChosenByUser] = useState(false);
  const [difficulty, setDifficulty] =
    useState<Difficulty>('Medium');
  const [durationMin, setDurationMin] =
    useState<Duration>(15);
  const [timed, setTimed] = useState(false);

  const [fieldErrors, setFieldErrors] =
    useState<FieldErrors>({});
  const [stage, setStage] =
    useState<'setup' | 'expect'>('setup');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const titleRef = useRef<HTMLInputElement>(null);
  const roleRef = useRef<HTMLSelectElement>(null);
  const typeRef = useRef<HTMLFieldSetElement>(null);
  const difficultyRef = useRef<HTMLFieldSetElement>(null);
  const durationRef = useRef<HTMLFieldSetElement>(null);
  const expectHeadingRef = useRef<HTMLHeadingElement>(null);
  const setupHeadingRef = useRef<HTMLHeadingElement>(null);
  const backToSetup = useRef(false);
  const submitting = useRef(false);
  const requestId = useRef(0);

  useEffect(() => {
    let active = true;

    getRoles()
      .then((items) => {
        if (active) {
          setRoles(items);
          setRolesLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setRolesLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (stage === 'expect') {
      expectHeadingRef.current?.focus();
    } else if (backToSetup.current) {
      backToSetup.current = false; // the Back button is gone, so focus lands on the form heading
      setupHeadingRef.current?.focus();
    }
  }, [stage]);

  function clearError(field: keyof FieldErrors) {
    setFieldErrors((previous) => ({
      ...previous,
      [field]: undefined,
    }));
  }

  async function findRole(): Promise<number | null> {
    const title = jobTitle.trim();

    if (!rolesAvailable) {
      setRoleId(null);
      return null;
    }

    if (title.length < 2 || !/\p{L}/u.test(title)) {
      return null;
    }

    const current = ++requestId.current;
    setMatching(true);
    setRoleMessage('Finding a role for your job title…');

    try {
      const result = await matchRole(title);

      if (current !== requestId.current) {
        return null;
      }

      const found =
        result.role_id !== null &&
        roles.some((role) => role.id === result.role_id);

      const matchedId = found ? result.role_id : null;
      setRoleId(matchedId);

      if (found) {
        const name =
          roles.find((role) => role.id === result.role_id)?.name ??
          result.role_name;

        setRoleMessage(
          `We matched this to ${name}. You can change it below.`
        );

        if (!typeChosenByUser) {
          setInterviewType(
            name?.toLowerCase() === 'customer service'
              ? 'Behavioral'
              : 'Mixed'
          );
        }

        clearError('roleId');
      } else {
        setRoleMessage(
          'We could not find a close match. Please choose a role below.'
        );
      }
      return matchedId;
    } catch {
      if (current !== requestId.current) {
        return null;
      }

      setRoleMessage(
        'Automatic matching is unavailable. Please choose a role below.'
      );
      return null;
    } finally {
      if (current === requestId.current) {
        setMatching(false);
      }
    }
  }

  function focusInvalid(field: keyof FieldErrors) {
    const target = {
      jobTitle: titleRef,
      roleId: roleRef,
      interviewType: typeRef,
      difficulty: difficultyRef,
      durationMin: durationRef,
    }[field];

    target?.current?.focus();
  }

  async function handleContinue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // A second click while the role lookup runs would restart it and make the first one see "no role".
    if (submitting.current) return;
    submitting.current = true;
    try {
      await continueToExpect();
    } finally {
      submitting.current = false;
    }
  }

  async function continueToExpect() {
    setError('');

    // Wait for roles to load before deciding whether a role is required.
    if (rolesLoading) return;

    let selectedRoleId = roleId;
    if (rolesAvailable && selectedRoleId === null &&
        jobTitle.trim().length >= 2 && /\p{L}/u.test(jobTitle)) {
      selectedRoleId = await findRole();
    }

    const errors = validateSetup({
      jobTitle,
      roleId: selectedRoleId,
      rolesAvailable,
      interviewType,
      difficulty,
      durationMin,
    });

    setFieldErrors(errors);

    const invalid = FIELD_ORDER.find(
      (field) => errors[field]
    );

    if (invalid) {
      focusInvalid(invalid);
      return;
    }

    setStage('expect');
  }

  async function handleStart() {
    if (loading || (rolesAvailable && roleId === null)) {
      return;
    }

    setError('');
    setLoading(true);

    try {
      const session = await startSession({
        job_title: jobTitle.trim(),
        role_id: rolesAvailable ? roleId : null,
        interview_type: interviewType,
        difficulty,
        duration_min: durationMin,
        timed,
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

  const selectedRole = roles.find(
    (role) => role.id === roleId
  );

  const length = LENGTHS.find(
    (item) => item.value === durationMin
  )!;

  return (
    <section
      className="wrap hero"
      aria-labelledby="setup-title"
    >
      <p className="section-label">
        Set up your session
      </p>

      <div className="panel pad">
        {stage === 'setup' ? (
          <form onSubmit={handleContinue} noValidate>
            <h1
              id="setup-title"
              ref={setupHeadingRef}
              tabIndex={-1}
              className="card-title"
            >
              Interview setup
            </h1>

            <p className="muted">
              Choose how you would like to practice.
              You can take your time.
            </p>

            <div className="opt-group">
              <label
                className="glabel"
                htmlFor="jobTitle"
              >
                Job title
              </label>

              <input
                id="jobTitle"
                ref={titleRef}
                value={jobTitle}
                maxLength={120}
                placeholder="e.g. Junior Data Analyst"
                autoComplete="organization-title"
                aria-invalid={Boolean(
                  fieldErrors.jobTitle
                )}
                aria-describedby={
                  fieldErrors.jobTitle
                    ? 'job-title-error'
                    : undefined
                }
                onChange={(event) => {
                  requestId.current += 1;
                  setMatching(false);
                  setJobTitle(event.target.value);
                  setRoleId(null);
                  setRoleMessage('');
                  clearError('jobTitle');
                }}
onBlur={() => {
  if (rolesAvailable && jobTitle.trim().length >= 2) {
    void findRole();
  }
}}   
              />

              {fieldErrors.jobTitle && (
                <p
                  className="field-err"
                  id="job-title-error"
                >
                  {fieldErrors.jobTitle}
                </p>
              )}
            </div>

            <div className="opt-group">
              <label
                className="glabel"
                htmlFor="role"
              >
                Role to practice
              </label>

              <p
                className="muted"
                aria-live="polite"
              >
                {roleMessage ||
                  'Enter a job title to see a suggested role, or choose one yourself.'}
              </p>

              <select
                id="role"
                ref={roleRef}
                value={roleId ?? ''}
                aria-invalid={Boolean(
                  fieldErrors.roleId
                )}
                aria-describedby={
                  fieldErrors.roleId
                    ? 'role-error'
                    : undefined
                }
                onChange={(event) => {
                  requestId.current += 1;
                  setMatching(false);

                  const id = event.target.value
                    ? Number(event.target.value)
                    : null;

                  setRoleId(id);

                  const chosen = roles.find(
                    (role) => role.id === id
                  );

                  setRoleMessage(
                    chosen
                      ? `You chose ${chosen.name}.`
                      : 'Please choose a role.'
                  );

                  if (chosen && !typeChosenByUser) {
                    setInterviewType(
                      chosen.name.toLowerCase() ===
                        'customer service'
                        ? 'Behavioral'
                        : 'Mixed'
                    );
                  }

                  clearError('roleId');
                }}
              >
                <option value="">
                  Choose a role
                </option>

                {roles.map((role) => (
                  <option
                    key={role.id}
                    value={role.id}
                  >
                    {role.name}
                  </option>
                ))}
              </select>

              {!rolesLoading && !rolesAvailable && (
                <p className="muted" role="status">
                  Roles are not available yet, so you will get general questions.
                </p>
              )}

              {fieldErrors.roleId && (
                <p
                  className="field-err"
                  id="role-error"
                >
                  {fieldErrors.roleId}
                </p>
              )}
            </div>

            <fieldset
              className="opt-group"
              ref={typeRef}
              tabIndex={-1}
            >
              <legend className="glabel">
                Interview type
              </legend>

              <div
                className="seg"
                role="group"
                aria-label="Interview type"
              >
                {TYPES.map((type) => (
                  <button
                    type="button"
                    key={type}
                    aria-pressed={
                      interviewType === type
                    }
                    onClick={() => {
                      setInterviewType(type);
                      setTypeChosenByUser(true);
                      clearError('interviewType');
                    }}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset
              className="opt-group"
              ref={difficultyRef}
              tabIndex={-1}
            >
              <legend className="glabel">
                Difficulty
              </legend>

              <div
                className="seg"
                role="group"
                aria-label="Difficulty"
              >
                {DIFFICULTIES.map((option) => (
                  <button
                    type="button"
                    key={option.value}
                    aria-pressed={
                      difficulty === option.value
                    }
                    onClick={() => {
                      setDifficulty(option.value);
                      clearError('difficulty');
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset
              className="opt-group"
              ref={durationRef}
              tabIndex={-1}
            >
              <legend className="glabel">
                Interview length
              </legend>

              <div
                className="seg"
                role="group"
                aria-label="Interview length"
              >
                {LENGTHS.map((option) => (
                  <button
                    type="button"
                    key={option.value}
                    aria-pressed={
                      durationMin === option.value
                    }
                    onClick={() => {
                      setDurationMin(option.value);
                      clearError('durationMin');
                    }}
                  >
                    {option.label}
                    <small>
                      {option.questions} questions
                    </small>
                  </button>
                ))}
              </div>
            </fieldset>

            <div className="opt-group">
              <label
                className="glabel"
                htmlFor="timed"
              >
                <input
                  id="timed"
                  type="checkbox"
                  checked={timed}
                  onChange={(event) => {
                    setTimed(event.target.checked);
                  }}
                />
                {' '}Use a timer (optional)
              </label>

              <p className="muted">
                {timed
                  ? `You will have ${durationMin} minutes.`
                  : 'No countdown. Practice at your own pace.'}
              </p>
            </div>

            {error && (
              <p role="alert" className="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="btn amber full"
              aria-disabled={rolesLoading}
            >
              {rolesLoading ? 'Loading roles…' : matching ? 'Matching your role…' : 'Continue'}
            </button>
          </form>
        ) : (
          <div>
            <h1
              id="setup-title"
              ref={expectHeadingRef}
              tabIndex={-1}
              className="card-title"
            >
              What to expect
            </h1>

            <p>
              You&apos;re practicing for{' '}
              <strong>
                {selectedRole?.name ?? jobTitle}
              </strong>.
            </p>

            <ul>
              <li>
                {length.questions} questions in a{' '}
                {interviewType.toLowerCase()}{' '}
                interview.
              </li>

              <li>
                {timed
                  ? `The timer is on (${durationMin} minutes).`
                  : 'The timer is off. Take your time.'}
              </li>

              <li>
                You can skip any question.
              </li>

              <li>
                Your practice answers are not
                shared with employers.
              </li>

              <li>
                Afterward, you will see friendly
                feedback to help you improve.
              </li>
            </ul>

            {error && (
              <p role="alert" className="alert">
                {error}
              </p>
            )}
            <p role="status" className="sr-only">
              {loading ? 'Starting your interview…' : ''}
            </p>

            <div className="opt-group">
              <button
                type="button"
                className="btn"
                aria-disabled={loading}
                onClick={() => {
                  if (loading) return;
                  setError('');
                  backToSetup.current = true;
                  setStage('setup');
                }}
              >
                Back to setup
              </button>
            </div>

            <button
              type="button"
              className="btn amber full"
              aria-disabled={loading}
              onClick={() => {
                void handleStart();
              }}
            >
              {loading
                ? 'Starting interview…'
                : 'Start interview'}
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
