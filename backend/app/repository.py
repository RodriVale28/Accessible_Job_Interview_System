"""S1-4.2 Persistence Layer for PostgreSQL - Sublime Mpanda

The API routers get the store through get_repo(): this module's PostgreSQL functions
when DATABASE_URL is set, otherwise MemoryRepository (local demo and tests). Both
expose the same functions.
"""

from __future__ import annotations

import random
import sys
import threading
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from psycopg.types.json import Jsonb

from app.config import DATABASE_URL

class PersistenceError(Exception):
    """Raised when a database operation fails."""
    pass


class AlreadyAnswered(PersistenceError):
    """Raised when a question already has a response."""
    pass


QUESTION_COUNTS = {
    15: 5,
    30: 8,
    45: 10
}


_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()  # sync routes run on a thread pool


def _connection():
    """Borrow a pooled connection to the PostgreSQL database.

    Reusing open connections avoids a new TLS handshake to Supabase on every
    query. Leaving the `with` block commits (or rolls back) and returns it.
    A pool timeout is a psycopg.OperationalError, so callers' handlers still apply.
    """
    global _pool

    if not DATABASE_URL:
        raise PersistenceError("DATABASE_URL is not configured")

    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(
                DATABASE_URL,
                min_size=1,
                max_size=5,  # well under the Supabase session pooler's client limit
                kwargs={"row_factory": dict_row},
                check=ConnectionPool.check_connection,  # drop connections the pooler closed
                timeout=10,  # fail fast (503) instead of hanging when the DB is down
                open=True,
            )
    return _pool.connection()

def ping() -> bool:
    """Check whether the PostgreSQL database is reachable."""
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() is not None
    except (psycopg.Error, PersistenceError):
        return False

# S2-1.1: feedback fields added in Sprint 2; save_answer fills in any that are missing.
FEEDBACK_DEFAULTS = {
    "criteria_met": [], "criteria_missed": [], "evidence": [], "reasons": [], "grader": "keyword",
}


def create_session(user_id, job_title, difficulty, duration_min,
                   role_id=None, interview_type="Technical", timed=False) -> int:
    """Create an interview session and return its ID."""

    if duration_min not in QUESTION_COUNTS:
        raise ValueError("Duration must be 15, 30, or 45 minutes")

    total_questions = QUESTION_COUNTS[duration_min]

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sessions
                        (user_id, job_title, difficulty,
                         duration_min, total_questions,
                         role_id, interview_type, timed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        job_title,
                        difficulty,
                        duration_min,
                        total_questions,
                        role_id,
                        interview_type,
                        timed
                    )
                )

                return cur.fetchone()["id"]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not create interview session"
        ) from exc

def save_response(session_id, question_id, user_id, text) -> int:
    """Save a user's response to an interview question."""

    if not isinstance(text, str):
        raise ValueError("Answer must be a string")

    text = text.strip()

    try:
        with _connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT status FROM sessions
                    WHERE id = %s AND user_id = %s
                    FOR UPDATE
                    """,
                    (session_id, user_id)
                )

                session = cur.fetchone()

                if session is None:
                    raise PersistenceError("Session not found")

                if session["status"] != "in_progress":
                    raise PersistenceError("Session already completed")

                cur.execute(
                    """
                    SELECT 1 FROM session_questions
                    WHERE session_id = %s AND question_id = %s
                    """,
                    (session_id, question_id)
                )

                if cur.fetchone() is None:
                    raise PersistenceError(
                        "Question is not assigned to this session"
                    )

                cur.execute(
                    """
                    INSERT INTO responses
                        (session_id, question_id, answer_text, is_blank)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id, question_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        session_id,
                        question_id,
                        text,
                        not bool(text.strip())
                    )
                )

                result = cur.fetchone()

                if result is None:
                    raise AlreadyAnswered("Question already answered")

                return result["id"]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not save interview response"
        ) from exc

def complete_session(session_id, user_id, overall_score) -> None:
    """Mark an interview session as completed."""

    if overall_score is not None and not 0 <= overall_score <= 100:
        raise ValueError("Overall score must be between 0 and 100")

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sessions
                    SET status = 'completed',
                        overall_score = %s,
                        completed_at = NOW()
                    WHERE id = %s
                      AND user_id = %s
                      AND status = 'in_progress'
                    RETURNING id
                    """,
                    (overall_score, session_id, user_id)
                )

                if cur.fetchone() is None:
                    raise PersistenceError(
                        "Active interview session not found"
                    )

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not complete interview session"
        ) from exc


def get_session_with_responses(session_id, user_id) -> dict | None:
    """Retrieve a user's interview session and its responses.

    Returns None if the session doesn't exist or belongs to another user.
    """

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM sessions
                    WHERE id = %s AND user_id = %s
                    """,
                    (session_id, user_id)
                )

                session = cur.fetchone()

                if session is None:
                    return None

                cur.execute(
                    """
                    SELECT
                        sq.q_index,
                        q.id AS question_id,
                        q.prompt,
                        q.category,
                        q.question_type,
                        r.id AS response_id,
                        r.answer_text,
                        r.is_blank,
                        r.submitted_at,
                        f.score,
                        f.correct,
                        f.matched_keywords,
                        f.missing_keywords,
                        f.strengths,
                        f.improvements,
                        f.criteria_met,
                        f.criteria_missed,
                        f.evidence,
                        f.grader
                    FROM session_questions AS sq
                    JOIN question_library AS q
                        ON q.id = sq.question_id
                    LEFT JOIN responses AS r
                        ON r.session_id = sq.session_id
                        AND r.question_id = sq.question_id
                    LEFT JOIN feedback AS f
                        ON f.session_id = sq.session_id
                        AND f.question_id = sq.question_id
                    WHERE sq.session_id = %s
                    ORDER BY sq.q_index
                    """,
                    (session_id,)
                )

                return {
                    "session": session,
                    "questions": cur.fetchall()
                }

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve interview session"
        ) from exc


def get_total_questions(session_id):
    """Return the total number of questions for a session."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT total_questions
                    FROM sessions
                    WHERE id = %s
                    """,
                    (session_id,)
                )

                result = cur.fetchone()

                if result is None:
                    return None

                return result["total_questions"]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve total question count"
        ) from exc

def count_asked_questions(session_id) -> int:
    """Count the questions already assigned to a session."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM session_questions
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )

                result = cur.fetchone()
                return result["total"]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not count asked questions"
        ) from exc

def pick_unused_question(session_id, difficulty):
    """Select a random unused question for the session."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT q.id, q.prompt, q.category
                    FROM question_library AS q
                    WHERE q.difficulty = %s
                      AND q.question_type = 'Technical'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM session_questions AS sq
                          WHERE sq.session_id = %s
                            AND sq.question_id = q.id
                      )
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (difficulty, session_id)
                )

                return cur.fetchone()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not select an unused question"
        ) from exc

# ---- S2-1.2 interview builder ----

def skills_with_questions(question_type) -> set:
    """Names of skills that have at least one question of this type."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT sk.name
                    FROM question_skills AS qs
                    JOIN skills AS sk ON sk.id = qs.skill_id
                    JOIN question_library AS q ON q.id = qs.question_id
                    WHERE q.question_type = %s
                    """,
                    (question_type,)
                )
                return {r["name"] for r in cur.fetchall()}

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not list skills with questions"
        ) from exc


def pick_question_for(session_id, difficulty, skills=None, question_type=None):
    """Random unused question: {id, prompt, category} or None.

    session_id None = no exclusions (practice). Relaxes to any skill, then any
    difficulty, before giving up. Behavioral questions ignore difficulty.
    """
    use_difficulty = question_type != "Behavioral"
    attempts = [(skills, use_difficulty), (None, use_difficulty)]
    if use_difficulty:
        attempts.append((None, False))

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                for skill_names, with_difficulty in attempts:
                    sql = ["SELECT q.id, q.prompt, q.category FROM question_library AS q"]
                    params = []
                    if skill_names:
                        sql.append(
                            "JOIN question_skills AS qs ON qs.question_id = q.id "
                            "JOIN skills AS sk ON sk.id = qs.skill_id AND sk.name = ANY(%s)"
                        )
                        params.append(list(skill_names))
                    sql.append("WHERE (%s::text IS NULL OR q.question_type = %s)")
                    params += [question_type, question_type]
                    if with_difficulty:
                        sql.append("AND q.difficulty = %s")
                        params.append(difficulty)
                    if session_id is not None:
                        sql.append(
                            "AND NOT EXISTS (SELECT 1 FROM session_questions AS sq "
                            "WHERE sq.session_id = %s AND sq.question_id = q.id)"
                        )
                        params.append(session_id)
                    sql.append("ORDER BY RANDOM() LIMIT 1")
                    cur.execute(" ".join(sql), params)
                    row = cur.fetchone()
                    if row:
                        return row
                return None

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not select a question"
        ) from exc


def count_session_question_types(session_id) -> dict:
    """How many Technical / Behavioral questions a session has been given: {type: count}."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT q.question_type, COUNT(*) AS n
                    FROM session_questions AS sq
                    JOIN question_library AS q ON q.id = sq.question_id
                    WHERE sq.session_id = %s
                    GROUP BY q.question_type
                    """,
                    (session_id,)
                )
                return {r["question_type"]: r["n"] for r in cur.fetchall()}

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not count question types"
        ) from exc


def record_asked_question(session_id, question_id, q_index):
    """Record a question assigned to an interview session."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_questions
                        (session_id, question_id, q_index)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, question_id, q_index)
                )

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not record asked question"
        ) from exc


def get_session(session_id, user_id) -> dict | None:
    """Return the session row, or None if it doesn't exist or isn't this user's."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM sessions WHERE id = %s AND user_id = %s",
                    (session_id, user_id)
                )
                return cur.fetchone()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve interview session"
        ) from exc


def list_sessions(user_id, limit=20) -> list:
    """A user's most recent sessions, newest first (for the past interviews list)."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT s.id, s.job_title, s.difficulty, s.duration_min, s.status,
                           s.overall_score, s.started_at, s.completed_at,
                           s.role_id, r.name AS role_name, s.interview_type
                    FROM sessions AS s
                    LEFT JOIN roles AS r ON r.id = s.role_id
                    WHERE s.user_id = %s
                    ORDER BY s.started_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                return cur.fetchall()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not list interview sessions"
        ) from exc


def asked_questions(session_id) -> list:
    """Questions assigned to a session, in order: [{question_id, q_index}]."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question_id, q_index
                    FROM session_questions
                    WHERE session_id = %s
                    ORDER BY q_index
                    """,
                    (session_id,)
                )
                return cur.fetchall()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve asked questions"
        ) from exc


def get_question(question_id) -> dict | None:
    """Return a full question_library row, including expected_keywords (server-side only)."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM question_library WHERE id = %s",
                    (question_id,)
                )
                return cur.fetchone()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve question"
        ) from exc


def get_responses(session_id) -> dict:
    """Saved answers for a session, keyed by question_id."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT session_id, question_id, answer_text, is_blank
                    FROM responses
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                return {row["question_id"]: row for row in cur.fetchall()}

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve responses"
        ) from exc


def get_feedback(session_id) -> dict:
    """Saved per-answer feedback for a session, keyed by question_id."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question_id, score, correct,
                           matched_keywords AS matched,
                           missing_keywords AS missing,
                           strengths, improvements
                    FROM feedback
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                return {row["question_id"]: row for row in cur.fetchall()}

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve feedback"
        ) from exc


def save_answer(session_id, question_id, text, is_blank, feedback, correct_count) -> int:
    """Save an answer, its feedback and the session's running correct count in one transaction."""

    feedback = {**FEEDBACK_DEFAULTS, **feedback}

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO responses
                        (session_id, question_id, answer_text, is_blank)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id, question_id) DO NOTHING
                    RETURNING id
                    """,
                    (session_id, question_id, text, is_blank)
                )

                result = cur.fetchone()

                if result is None:
                    raise AlreadyAnswered("Question already answered")

                cur.execute(
                    """
                    INSERT INTO feedback
                        (session_id, question_id, response_id, score, correct,
                         matched_keywords, missing_keywords, strengths, improvements,
                         criteria_met, criteria_missed, evidence, reasons, grader)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_id,
                        question_id,
                        result["id"],
                        feedback["score"],
                        feedback["correct"],
                        feedback["matched"],
                        feedback["missing"],
                        feedback["strengths"],
                        feedback["improvements"],
                        feedback["criteria_met"],
                        feedback["criteria_missed"],
                        feedback["evidence"],
                        feedback["reasons"],
                        feedback["grader"]
                    )
                )

                cur.execute(
                    "UPDATE sessions SET correct_count = %s WHERE id = %s",
                    (correct_count, session_id)
                )

                return result["id"]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not save interview response"
        ) from exc


# ---- S2-1.1 Sprint 2 schema: roles and rubrics ----

def list_roles() -> list:
    """All roles: [{id, name, keywords, technical_share}]."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, keywords, technical_share FROM roles ORDER BY id"
                )
                return [{**r, "technical_share": float(r["technical_share"])}
                        for r in cur.fetchall()]

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not list roles"
        ) from exc


def get_role(role_id) -> dict | None:
    """A role with its skill weights: {id, name, keywords, technical_share, skills: {name: weight}}."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, keywords, technical_share FROM roles WHERE id = %s",
                    (role_id,)
                )
                role = cur.fetchone()

                if role is None:
                    return None

                cur.execute(
                    """
                    SELECT s.name, rs.weight
                    FROM role_skills AS rs
                    JOIN skills AS s ON s.id = rs.skill_id
                    WHERE rs.role_id = %s
                    """,
                    (role_id,)
                )
                skills = {r["name"]: float(r["weight"]) for r in cur.fetchall()}
                return {**role, "technical_share": float(role["technical_share"]), "skills": skills}

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve role"
        ) from exc


def get_rubric(question_id) -> list:
    """A question's rubric criteria in order: [{text, keywords}]. Empty if it has none yet."""

    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT text, keywords
                    FROM rubric_criteria
                    WHERE question_id = %s
                    ORDER BY position
                    """,
                    (question_id,)
                )
                return cur.fetchall()

    except psycopg.Error as exc:
        raise PersistenceError(
            "Could not retrieve rubric"
        ) from exc


# ---- S2-4.1: Practice, settings, and history (PostgreSQL) ----

def save_practice_attempt(user_id, question_id, answer_text, result: dict) -> int:
    """Save a practice attempt and grading result."""
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO practice_attempts
                        (user_id, question_id, answer_text, result)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, question_id, answer_text, Jsonb(result)),
                )
                return cur.fetchone()["id"]
    except psycopg.Error as exc:
        raise PersistenceError("Could not save practice attempt") from exc


def get_settings(user_id) -> dict | None:
    """Retrieve a user's accessibility settings."""
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT text_size, theme, font, read_aloud
                    FROM user_settings
                    WHERE user_id = %s
                    """,
                    (user_id,),
                )
                return cur.fetchone()
    except psycopg.Error as exc:
        raise PersistenceError("Could not retrieve settings") from exc


def save_settings(user_id, settings: dict):
    """Save or update a user's accessibility settings."""
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_settings
                        (user_id, text_size, theme, font, read_aloud)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        text_size = EXCLUDED.text_size,
                        theme = EXCLUDED.theme,
                        font = EXCLUDED.font,
                        read_aloud = EXCLUDED.read_aloud,
                        updated_at = NOW()
                    """,
                    (
                        user_id,
                        settings["text_size"],
                        settings["theme"],
                        settings["font"],
                        settings["read_aloud"],
                    ),
                )
    except psycopg.Error as exc:
        raise PersistenceError("Could not save settings") from exc


def discard_session(session_id, user_id) -> bool:
    """Discard an unfinished interview belonging to the user."""
    try:
        with _connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM sessions
                    WHERE id = %s
                      AND user_id = %s
                      AND status = 'in_progress'
                    FOR UPDATE
                    """,
                    (session_id, user_id),
                )

                if cur.fetchone() is None:
                    return False

                cur.execute(
                    "DELETE FROM feedback WHERE session_id = %s",
                    (session_id,),
                )
                cur.execute(
                    "DELETE FROM responses WHERE session_id = %s",
                    (session_id,),
                )
                cur.execute(
                    "DELETE FROM session_questions WHERE session_id = %s",
                    (session_id,),
                )
                cur.execute(
                    """
                    DELETE FROM sessions
                    WHERE id = %s
                      AND user_id = %s
                      AND status = 'in_progress'
                    RETURNING id
                    """,
                    (session_id, user_id),
                )

                return cur.fetchone() is not None
    except psycopg.Error as exc:
        raise PersistenceError("Could not discard interview") from exc

# ---- S2-4.1: Practice, settings, and history (PostgreSQL) ----

def _question_dict(q) -> dict:
    """A question in the S2 dict shape; Sprint 1 tuples (category, difficulty, prompt, keywords) still load."""
    if not isinstance(q, dict):
        c, d, p, k = q
        q = {"category": c, "difficulty": d, "prompt": p, "expected_keywords": k}
    return {"question_type": "Technical", "skills": [], "rubric": [], **q}


def _load_library():
    """Questions and roles from question_library/, or empty lists for files not merged yet."""
    from question_library.questions_data import QUESTIONS
    try:
        from question_library.behavioral_data import BEHAVIORAL_QUESTIONS
    except ImportError:
        BEHAVIORAL_QUESTIONS = []
    try:
        from question_library.roles_data import ROLES
    except ImportError:
        ROLES = []
    return list(QUESTIONS) + list(BEHAVIORAL_QUESTIONS), ROLES


class MemoryRepository:
    """In-memory store with the same functions as the PostgreSQL ones above.

    Used when DATABASE_URL is empty (local demo, tests). Data is lost on restart.
    """

    def __init__(self, questions=None, roles=None):
        if questions is None or roles is None:
            lib_questions, lib_roles = _load_library()
            questions = lib_questions if questions is None else questions
            roles = lib_roles if roles is None else roles
        self.questions = {i: {**_question_dict(q), "id": i} for i, q in enumerate(questions, start=1)}
        self.roles = {i: {**r, "id": i} for i, r in enumerate(roles, start=1)}
        self.sessions = {}
        self.session_questions = {}  # session_id -> [{question_id, q_index}]
        self.responses = {}          # session_id -> {question_id: row}
        self.feedback = {}           # session_id -> {question_id: row}
        self._next_session_id = 1
        self._next_response_id = 1
        # S2-4.1: Practice attempts and accessibility settings
        self.practice_attempts = {}
        self.user_settings = {}
        self._next_practice_attempt_id = 1

        # S2-X.4: Check whether the in-memory repository is available.
    def ping(self) -> bool:
        return True

    def create_session(self, user_id, job_title, difficulty, duration_min,
                       role_id=None, interview_type="Technical", timed=False) -> int:
        if duration_min not in QUESTION_COUNTS:
            raise ValueError("Duration must be 15, 30, or 45 minutes")
        if role_id is not None and role_id not in self.roles:
            raise PersistenceError("Could not create interview session")  # FK violation in Postgres
        session_id = self._next_session_id
        self._next_session_id += 1
        self.sessions[session_id] = {
            "id": session_id, "user_id": str(user_id), "job_title": job_title,
            "role_id": role_id, "interview_type": interview_type, "timed": timed,
            "difficulty": difficulty, "duration_min": duration_min,
            "total_questions": QUESTION_COUNTS[duration_min], "status": "in_progress",
            "overall_score": None, "correct_count": 0,
            "started_at": datetime.now(timezone.utc), "completed_at": None,
        }
        self.session_questions[session_id] = []
        self.responses[session_id] = {}
        self.feedback[session_id] = {}
        return session_id

    def get_session(self, session_id, user_id):
        s = self.sessions.get(session_id)
        return dict(s) if s and s["user_id"] == str(user_id) else None

    def list_sessions(self, user_id, limit=20) -> list:
        mine = [s for s in self.sessions.values() if s["user_id"] == str(user_id)]
        mine.sort(key=lambda s: (s["started_at"], s["id"]), reverse=True)
        keys = ("id", "job_title", "difficulty", "duration_min", "status",
                "overall_score", "started_at", "completed_at", "role_id", "interview_type")
        return [{**{k: s[k] for k in keys},
                 "role_name": self.roles[s["role_id"]]["name"] if s["role_id"] else None}
                for s in mine[:limit]]

    def get_total_questions(self, session_id):
        s = self.sessions.get(session_id)
        return s["total_questions"] if s else None

    def count_asked_questions(self, session_id) -> int:
        return len(self.session_questions.get(session_id, []))

    def pick_unused_question(self, session_id, difficulty):
        used = {q["question_id"] for q in self.session_questions.get(session_id, [])}
        options = [q for q in self.questions.values()
                   if q["difficulty"] == difficulty and q["question_type"] == "Technical"
                   and q["id"] not in used]
        if not options:
            return None
        q = random.choice(options)
        return {"id": q["id"], "prompt": q["prompt"], "category": q["category"]}

    def record_asked_question(self, session_id, question_id, q_index):
        asked = self.session_questions[session_id]
        if any(q["question_id"] == question_id or q["q_index"] == q_index for q in asked):
            raise PersistenceError("Could not record asked question")
        asked.append({"question_id": question_id, "q_index": q_index})

    # S2-1.2 interview builder
    def skills_with_questions(self, question_type) -> set:
        """Names of skills that have at least one question of this type."""
        return {s for q in self.questions.values()
                if q["question_type"] == question_type
                for s in q["skills"]}

    def pick_question_for(self, session_id, difficulty, skills=None, question_type=None):
        used = set()
        if session_id is not None:
            used = {q["question_id"] for q in self.session_questions.get(session_id, [])}
        use_difficulty = question_type != "Behavioral"
        attempts = [(skills, use_difficulty), (None, use_difficulty)]
        if use_difficulty:
            attempts.append((None, False))
        for skill_names, with_difficulty in attempts:
            options = [
                q for q in self.questions.values()
                if q["id"] not in used
                and (question_type is None or q["question_type"] == question_type)
                and (not with_difficulty or q["difficulty"] == difficulty)
                and (not skill_names or set(skill_names) & set(q["skills"]))
            ]
            if options:
                q = random.choice(options)
                return {"id": q["id"], "prompt": q["prompt"], "category": q["category"]}
        return None

    def count_session_question_types(self, session_id) -> dict:
        counts = {}
        for a in self.session_questions.get(session_id, []):
            t = self.questions[a["question_id"]]["question_type"]
            counts[t] = counts.get(t, 0) + 1
        return counts

    def asked_questions(self, session_id) -> list:
        return sorted((dict(q) for q in self.session_questions.get(session_id, [])), key=lambda q: q["q_index"])

    def get_question(self, question_id):
        q = self.questions.get(question_id)
        return dict(q) if q else None

    def get_responses(self, session_id) -> dict:
        return {qid: dict(r) for qid, r in self.responses.get(session_id, {}).items()}

    def get_feedback(self, session_id) -> dict:
        return {qid: dict(f) for qid, f in self.feedback.get(session_id, {}).items()}

    def save_answer(self, session_id, question_id, text, is_blank, feedback, correct_count) -> int:
        if question_id in self.responses[session_id]:
            raise AlreadyAnswered("Question already answered")
        response_id = self._next_response_id
        self._next_response_id += 1
        self.responses[session_id][question_id] = {
            "id": response_id, "session_id": session_id, "question_id": question_id,
            "answer_text": text, "is_blank": is_blank, "submitted_at": datetime.now(timezone.utc),
        }
        self.feedback[session_id][question_id] = {"question_id": question_id, **FEEDBACK_DEFAULTS, **feedback}
        self.sessions[session_id]["correct_count"] = correct_count
        return response_id

    def complete_session(self, session_id, user_id, overall_score) -> None:
        if overall_score is not None and not 0 <= overall_score <= 100:
            raise ValueError("Overall score must be between 0 and 100")
        s = self.sessions.get(session_id)
        if not s or s["user_id"] != str(user_id) or s["status"] != "in_progress":
            raise PersistenceError("Active interview session not found")
        s.update(status="completed", overall_score=overall_score, completed_at=datetime.now(timezone.utc))

    def get_session_with_responses(self, session_id, user_id):
        session = self.get_session(session_id, user_id)
        if session is None:
            return None
        responses, feedback = self.responses[session_id], self.feedback[session_id]
        rows = []
        for asked in self.asked_questions(session_id):
            qid = asked["question_id"]
            q, r, f = self.questions.get(qid, {}), responses.get(qid, {}), feedback.get(qid, {})
            rows.append({
                "q_index": asked["q_index"], "question_id": qid,
                "prompt": q.get("prompt"), "category": q.get("category"),
                "question_type": q.get("question_type"),
                "response_id": r.get("id"), "answer_text": r.get("answer_text"),
                "is_blank": r.get("is_blank"), "submitted_at": r.get("submitted_at"),
                "score": f.get("score"), "correct": f.get("correct"),
                "matched_keywords": f.get("matched"), "missing_keywords": f.get("missing"),
                "strengths": f.get("strengths"), "improvements": f.get("improvements"),
                "criteria_met": f.get("criteria_met"), "criteria_missed": f.get("criteria_missed"),
                "evidence": f.get("evidence"), "grader": f.get("grader"),
            })
        return {"session": session, "questions": rows}

    # S2-1.1 roles and rubrics
    def list_roles(self) -> list:
        keys = ("id", "name", "keywords", "technical_share")
        return [{k: r[k] for k in keys} for r in self.roles.values()]

    def get_role(self, role_id):
        r = self.roles.get(role_id)
        return {**r, "skills": dict(r["skills"])} if r else None

    def get_rubric(self, question_id) -> list:
        q = self.questions.get(question_id)
        return [{"text": c["text"], "keywords": list(c["keywords"])} for c in q["rubric"]] if q else []
    # ---- S2-4.1: Practice, settings, and history ----

    def save_practice_attempt(self, user_id, question_id, answer_text, result: dict) -> int:
        """Store a user's practice attempt in memory."""
        if question_id not in self.questions:
            raise PersistenceError("Practice question not found")

        attempt_id = self._next_practice_attempt_id
        self._next_practice_attempt_id += 1

        self.practice_attempts[attempt_id] = {
            "id": attempt_id,
            "user_id": str(user_id),
            "question_id": question_id,
            "answer_text": answer_text,
            "result": dict(result),
            "created_at": datetime.now(timezone.utc),
        }
        return attempt_id

    def get_settings(self, user_id) -> dict | None:
        """Retrieve a user's saved accessibility settings."""
        settings = self.user_settings.get(str(user_id))
        return dict(settings) if settings is not None else None

    def save_settings(self, user_id, settings: dict):
        """Save or update a user's accessibility settings."""
        self.user_settings[str(user_id)] = dict(settings)

    def discard_session(self, session_id, user_id) -> bool:
        """Remove an unfinished interview owned by the user."""
        session = self.sessions.get(session_id)

        if session is None or session["user_id"] != str(user_id):
            return False

        if session["status"] != "in_progress":
            return False

        del self.sessions[session_id]
        self.session_questions.pop(session_id, None)
        self.responses.pop(session_id, None)
        self.feedback.pop(session_id, None)

        return True


_memory_repo = None


def get_repo():
    """FastAPI dependency for the API routers; tests override it with a MemoryRepository."""
    global _memory_repo
    if DATABASE_URL:
        return sys.modules[__name__]
    if _memory_repo is None:
        _memory_repo = MemoryRepository()
    return _memory_repo