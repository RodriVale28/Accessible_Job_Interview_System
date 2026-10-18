-- S1-4.1: Sprint 1 schema (PostgreSQL / Supabase). Safe to run more than once.

CREATE TABLE IF NOT EXISTS question_library (
    id                INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category          TEXT   NOT NULL,
    difficulty        TEXT   NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    prompt            TEXT   NOT NULL UNIQUE,
    expected_keywords TEXT[] NOT NULL CHECK (cardinality(expected_keywords) > 0)
);

-- user_id is the guest id for now; FK to auth.users once login is added.
CREATE TABLE IF NOT EXISTS sessions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         UUID   NOT NULL,
    job_title       TEXT   NOT NULL CHECK (length(trim(job_title)) BETWEEN 2 AND 120),
    interview_type  TEXT   NOT NULL DEFAULT 'Technical' CHECK (interview_type = 'Technical'),
    difficulty      TEXT   NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    duration_min    INT    NOT NULL CHECK (duration_min IN (15, 30, 45)),
    total_questions INT    NOT NULL CHECK (total_questions > 0),
    status          TEXT   NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    overall_score   INT    CHECK (overall_score BETWEEN 0 AND 100),
    correct_count   INT    NOT NULL DEFAULT 0,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS session_questions (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id  BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INT    NOT NULL REFERENCES question_library(id),
    q_index     INT    NOT NULL CHECK (q_index > 0),
    asked_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, q_index),
    UNIQUE (session_id, question_id)
);

-- Blank answers are stored with is_blank = true.
CREATE TABLE IF NOT EXISTS responses (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id   BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id  INT    NOT NULL REFERENCES question_library(id),
    answer_text  TEXT   NOT NULL DEFAULT '',
    is_blank     BOOLEAN NOT NULL DEFAULT false,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, question_id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id       BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id      INT    NOT NULL REFERENCES question_library(id),
    response_id      BIGINT REFERENCES responses(id) ON DELETE CASCADE,
    score            INT    NOT NULL CHECK (score BETWEEN 0 AND 100),
    correct          BOOLEAN NOT NULL,
    matched_keywords TEXT[] NOT NULL DEFAULT '{}',
    missing_keywords TEXT[] NOT NULL DEFAULT '{}',
    strengths        TEXT   NOT NULL DEFAULT '',
    improvements     TEXT   NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_started  ON sessions(user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_questions_sess ON session_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_responses_session      ON responses(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session       ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_question_difficulty    ON question_library(difficulty);

-- RLS on with no policies: blocks Supabase's public API. The backend connects as owner.
ALTER TABLE question_library  ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses         ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback          ENABLE ROW LEVEL SECURITY;
