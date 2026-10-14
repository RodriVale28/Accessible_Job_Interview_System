-- S1-4.1 Sprint 1 schema

CREATE TABLE question_library (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category           TEXT   NOT NULL,
    difficulty         TEXT   NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    prompt             TEXT   NOT NULL UNIQUE,
    expected_keywords  TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE sessions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         UUID        NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    job_title       TEXT        NOT NULL,
    interview_type  TEXT        NOT NULL DEFAULT 'Technical' CHECK (interview_type IN ('Technical')),
    difficulty      TEXT        NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    duration_min    INT         NOT NULL CHECK (duration_min IN (15, 30, 45)),
    total_questions INT         NOT NULL CHECK (total_questions > 0),
    status          TEXT        NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    overall_score   INT         CHECK (overall_score BETWEEN 0 AND 100),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);

CREATE TABLE session_questions (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id   BIGINT NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    question_id  BIGINT NOT NULL REFERENCES question_library (id),
    q_index      INT    NOT NULL CHECK (q_index > 0),
    asked_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, q_index),
    UNIQUE (session_id, question_id)
);

CREATE TABLE responses (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_question_id  BIGINT NOT NULL UNIQUE REFERENCES session_questions (id) ON DELETE CASCADE,
    answer_text          TEXT   NOT NULL CHECK (btrim(answer_text) <> ''),
    submitted_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE feedback (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_question_id  BIGINT  NOT NULL UNIQUE REFERENCES session_questions (id) ON DELETE CASCADE,
    score                INT     NOT NULL CHECK (score BETWEEN 0 AND 100),
    is_correct           BOOLEAN NOT NULL,
    matched_keywords     TEXT[]  NOT NULL DEFAULT '{}',
    missing_keywords     TEXT[]  NOT NULL DEFAULT '{}',
    strengths            TEXT,
    improvements         TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_user ON sessions (user_id, started_at DESC);
CREATE INDEX idx_question_library_difficulty ON question_library (difficulty);

ALTER TABLE question_library  ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses         ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback          ENABLE ROW LEVEL SECURITY;
