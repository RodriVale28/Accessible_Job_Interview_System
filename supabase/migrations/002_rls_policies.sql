-- S1 task 1.1: Row Level Security policies
-- Logged-in users can read only their own sessions and everything under them.
-- All writes go through the FastAPI backend, which connects with the database
-- password and is not limited by RLS, so it must still filter by user_id.
-- question_library has no policy: it stays server-only (expected_keywords).

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
        SELECT 1 FROM session_questions sq
        JOIN sessions s ON s.id = sq.session_id
        WHERE sq.id = responses.session_question_id
          AND s.user_id = (SELECT auth.uid())
    ));

CREATE POLICY own_feedback ON feedback
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM session_questions sq
        JOIN sessions s ON s.id = sq.session_id
        WHERE sq.id = feedback.session_question_id
          AND s.user_id = (SELECT auth.uid())
    ));
