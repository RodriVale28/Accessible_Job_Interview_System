-- S1-4.1 / task 1.1: extra constraints and Row Level Security on top of 001_init.sql
-- Run once in the Supabase SQL Editor after 001 and 002 (the API only runs 001 on startup).
-- Adds rules the app already follows, so no code changes are needed.

-- A session is completed exactly when it has a completed_at time.
ALTER TABLE sessions
    ADD CONSTRAINT sessions_completed_check CHECK ((status = 'completed') = (completed_at IS NOT NULL));

-- Question numbers start at 1.
ALTER TABLE session_questions
    ADD CONSTRAINT session_questions_q_index_check CHECK (q_index > 0);

-- History page: a user's sessions, newest first.
CREATE INDEX IF NOT EXISTS idx_sessions_user_started ON sessions (user_id, started_at DESC);

-- RLS policies. Logged-in Supabase users can read only their own sessions and everything
-- under them. All writes go through the FastAPI backend, which connects as the table owner
-- and is not limited by RLS, so it must still filter by user_id.
-- question_library has no policy: it stays server-only (expected_keywords).
-- Sprint 1 uses guest ids, so these match no one until login is added.

CREATE POLICY own_sessions ON sessions
    FOR SELECT TO authenticated
    USING (user_id = (SELECT auth.uid()));

CREATE POLICY own_session_questions ON session_questions
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM sessions s
        WHERE s.id = session_questions.session_id
          AND s.user_id = (SELECT auth.uid())
    ));

CREATE POLICY own_responses ON responses
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM sessions s
        WHERE s.id = responses.session_id
          AND s.user_id = (SELECT auth.uid())
    ));

CREATE POLICY own_feedback ON feedback
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM sessions s
        WHERE s.id = feedback.session_id
          AND s.user_id = (SELECT auth.uid())
    ));
