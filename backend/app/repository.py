"""S1-4.2 Persistence Layer for PostgreSQL - Sublime Mpanda"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

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


def _connection():
    """Create a connection to the PostgreSQL database."""

    if not DATABASE_URL:
        raise PersistenceError("DATABASE_URL is not configured")

    try:
        return psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )
    except psycopg.Error as exc:
        raise PersistenceError(
            "Unable to connect to the database"
        ) from exc


def create_session(user_id, job_title, difficulty, duration_min) -> int:
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
                         duration_min, total_questions)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        job_title,
                        difficulty,
                        duration_min,
                        total_questions
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


def get_session_with_responses(session_id, user_id) -> dict:
    """Retrieve a user's interview session and its responses."""

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
                    raise PersistenceError("Session not found")

                cur.execute(
                    """
                    SELECT
                        sq.q_index,
                        q.id AS question_id,
                        q.prompt,
                        q.category,
                        r.id AS response_id,
                        r.answer_text,
                        r.is_blank,
                        r.submitted_at,
                        f.score,
                        f.correct,
                        f.matched_keywords,
                        f.missing_keywords,
                        f.strengths,
                        f.improvements
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