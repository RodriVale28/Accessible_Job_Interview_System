-- S2-1.1: Sprint 2 schema (roles and skills, rubrics, interview types, practice, settings).
-- Run after 001. Safe to run more than once.

CREATE TABLE IF NOT EXISTS skills (
    id   INT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name = lower(trim(name)) AND name <> '')
);

-- technical_share: share of technical questions in a Mixed interview.
CREATE TABLE IF NOT EXISTS roles (
    id              INT     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    keywords        TEXT[]  NOT NULL DEFAULT '{}',
    technical_share NUMERIC NOT NULL CHECK (technical_share BETWEEN 0 AND 1)
);

-- A role's weights add up to 1 (checked by the seed data, not here).
CREATE TABLE IF NOT EXISTS role_skills (
    role_id  INT     NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    skill_id INT     NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    weight   NUMERIC NOT NULL CHECK (weight > 0 AND weight <= 1),
    PRIMARY KEY (role_id, skill_id)
);

ALTER TABLE question_library
    ADD COLUMN IF NOT EXISTS question_type TEXT NOT NULL DEFAULT 'Technical'
        CHECK (question_type IN ('Technical', 'Behavioral'));

CREATE TABLE IF NOT EXISTS question_skills (
    question_id INT NOT NULL REFERENCES question_library(id) ON DELETE CASCADE,
    skill_id    INT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (question_id, skill_id)
);

-- text is a full statement; keywords are for the fallback grader.
CREATE TABLE IF NOT EXISTS rubric_criteria (
    id          INT    GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question_id INT    NOT NULL REFERENCES question_library(id) ON DELETE CASCADE,
    position    INT    NOT NULL CHECK (position > 0),
    text        TEXT   NOT NULL CHECK (length(trim(text)) > 0),
    keywords    TEXT[] NOT NULL DEFAULT '{}',
    UNIQUE (question_id, position)
);

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS role_id INT REFERENCES roles(id);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS timed   BOOLEAN NOT NULL DEFAULT false;

-- evidence is in the same order as criteria_met.
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS criteria_met    TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS criteria_missed TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS evidence        TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS reasons         TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS grader          TEXT   NOT NULL DEFAULT 'keyword'
    CHECK (grader IN ('ai', 'keyword'));

-- user_id FK to auth.users is added by 004 (Supabase only).
CREATE TABLE IF NOT EXISTS practice_attempts (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     UUID   NOT NULL,
    question_id INT    NOT NULL REFERENCES question_library(id),
    answer_text TEXT   NOT NULL DEFAULT '',
    result      JSONB  NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id    UUID    PRIMARY KEY,
    text_size  TEXT    NOT NULL DEFAULT 'md'      CHECK (text_size IN ('sm', 'md', 'lg', 'xl')),
    theme      TEXT    NOT NULL DEFAULT 'light'   CHECK (theme IN ('light', 'dark', 'contrast')),
    font       TEXT    NOT NULL DEFAULT 'default' CHECK (font IN ('default', 'dyslexic')),
    read_aloud BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 001 allowed only 'Technical'. Dropped and re-added so a re-run is a no-op.
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_interview_type_check;
ALTER TABLE sessions ADD CONSTRAINT sessions_interview_type_check
    CHECK (interview_type IN ('Technical', 'Behavioral', 'Mixed'));

CREATE INDEX IF NOT EXISTS idx_question_skills_skill ON question_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_question_type         ON question_library(question_type);
CREATE INDEX IF NOT EXISTS idx_practice_user_created ON practice_attempts(user_id, created_at DESC);

-- RLS on with no policies, same as 001.
ALTER TABLE skills            ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_skills       ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_skills   ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubric_criteria   ENABLE ROW LEVEL SECURITY;
ALTER TABLE practice_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings     ENABLE ROW LEVEL SECURITY;
