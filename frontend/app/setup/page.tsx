
'use client';

import { useState, type FormEvent } from 'react';
import { startSession } from '../../lib/api';
import type { Difficulty, Duration } from '../../lib/types';

export default function SetupPage() {
  const [jobTitle, setJobTitle] = useState('');
  const [difficulty, setDifficulty] = useState<Difficulty>('Medium');
  const [durationMin, setDurationMin] = useState<Duration>(15);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState<number | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');

    if (!jobTitle.trim()) {
      setError('Please enter a job title.');
      return;
    }

    setLoading(true);

    try {
      const session = await startSession({
        job_title: jobTitle.trim(),
        difficulty,
        duration_min: durationMin,
      });

      setSessionId(session.session_id);

      // Navigation will use the team's confirmed interview route.
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to start the interview. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-2 text-3xl font-bold">
        Interview Setup
      </h1>

      <p className="mb-6">
        Choose your settings before starting your interview.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="jobTitle" className="block font-semibold">
            Job Title
          </label>

          <input
            id="jobTitle"
            type="text"
            required
            maxLength={120}
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="e.g. Software Engineer"
            className="mt-2 w-full rounded border p-3"
          />
        </div>

        <div className="rounded border p-4">
          <h2 className="font-semibold">Interview Type</h2>
          <p>Technical</p>
        </div>

        <fieldset>
          <legend className="mb-2 font-semibold">
            Difficulty
          </legend>

          <div className="flex flex-wrap gap-2">
            {(['Easy', 'Medium', 'Hard'] as const).map((level) => (
              <button
                key={level}
                type="button"
                aria-pressed={difficulty === level}
                onClick={() => setDifficulty(level)}
                className={`rounded border p-3 ${
                  difficulty === level
                    ? 'bg-blue-700 text-white'
                    : 'bg-white text-black'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 font-semibold">
            Interview Duration
          </legend>

          <div className="flex flex-wrap gap-2">
            {([15, 30, 45] as const).map((minutes) => (
              <button
                key={minutes}
                type="button"
                aria-pressed={durationMin === minutes}
                onClick={() => setDurationMin(minutes)}
                className={`rounded border p-3 ${
                  durationMin === minutes
                    ? 'bg-blue-700 text-white'
                    : 'bg-white text-black'
                }`}
              >
                {minutes} minutes
              </button>
            ))}
          </div>
        </fieldset>

        {error && (
          <p role="alert" className="text-red-700">
            {error}
          </p>
        )}

        {sessionId !== null && (
          <p role="status">
            Interview session {sessionId} created successfully.
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-blue-700 p-3 font-semibold text-white disabled:opacity-50"
        >
          {loading ? 'Starting Interview...' : 'Begin Interview'}
        </button>
      </form>
    </main>
  );
}
