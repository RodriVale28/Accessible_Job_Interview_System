"""S1-4.2 Persistence layer - owner: Sublime Mpanda

Two interchangeable stores with the same methods:
  PostgresRepository  Supabase/PostgreSQL (used whenever DATABASE_URL is set)
  MemoryRepository    in-process dicts (tests and quick local demos)
Every read of a session filters by user_id, so users only see their own data.
Database failures are raised as PersistenceError and returned to the app as HTTP 503.
"""
from __future__ import annotations

from typing import Optional

import threading
from datetime import datetime, timezone
from pathlib import Path

from app.config import DATABASE_URL
from app.data.questions_data import QUESTIONS

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


class PersistenceError(Exception):
    """A database read/write failed. Message is safe to show to users."""


class AlreadyAnswered(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- memory
class MemoryRepository:
    def __init__(self, questions=QUESTIONS):
        self._lock = threading.Lock()
        self.questions = {
            i + 1: {"id": i + 1, "category": c, "difficulty": d, "prompt": p, "expected_keywords": list(k)}
            for i, (c, d, p, k) in enumerate(questions)
        }
        self.sessions: dict = {}
        self.session_questions: dict = {}   # session_id -> list[{question_id, q_index}]
        self.responses: dict = {}           # (session_id, question_id) -> row
        self.feedback: dict = {}            # (session_id, question_id) -> row
        self._ids = {"session": 0, "response": 0}

    def init(self) -> None:
        pass

    def ping(self) -> bool:
        return True

    # questions
    def list_questions(self, difficulty: str) -> list:
        return [q for q in self.questions.values() if q["difficulty"] == difficulty]

    def get_question(self, question_id: int) -> Optional[dict]:
        return self.questions.get(question_id)

    # sessions
    def create_session(self, user_id, job_title, difficulty, duration_min, total_questions) -> dict:
        with self._lock:
            self._ids["session"] += 1
            sid = self._ids["session"]
            row = {"id": sid, "user_id": str(user_id), "job_title": job_title, "interview_type": "Technical",
                   "difficulty": difficulty, "duration_min": duration_min, "total_questions": total_questions,
                   "status": "in_progress", "overall_score": None, "correct_count": 0,
                   "started_at": _now(), "completed_at": None}
            self.sessions[sid] = row
            self.session_questions[sid] = []
            return dict(row)

    def get_session(self, session_id, user_id) -> Optional[dict]:
        row = self.sessions.get(session_id)
        if not row or row["user_id"] != str(user_id):
            return None
        return dict(row)

    def asked_questions(self, session_id) -> list:
        return [dict(r) for r in self.session_questions.get(session_id, [])]

    def add_session_question(self, session_id, question_id, q_index) -> None:
        with self._lock:
            self.session_questions[session_id].append({"question_id": question_id, "q_index": q_index})

    # responses + feedback
    def save_answer(self, session_id, question_id, text, is_blank, fb: dict, correct_count: int) -> int:
        with self._lock:
            if (session_id, question_id) in self.responses:
                raise AlreadyAnswered()
            self._ids["response"] += 1
            rid = self._ids["response"]
            self.responses[(session_id, question_id)] = {
                "id": rid, "session_id": session_id, "question_id": question_id,
                "answer_text": text, "is_blank": is_blank, "submitted_at": _now()}
            self.feedback[(session_id, question_id)] = {**fb, "response_id": rid}
            self.sessions[session_id]["correct_count"] = correct_count
            return rid

    def get_responses(self, session_id) -> dict:
        return {qid: dict(r) for (sid, qid), r in self.responses.items() if sid == session_id}

    def get_feedback(self, session_id) -> dict:
        return {qid: dict(r) for (sid, qid), r in self.feedback.items() if sid == session_id}

    def complete_session(self, session_id, overall_score, correct_count, missing_feedback: dict) -> None:
        with self._lock:
            for qid, fb in missing_feedback.items():
                self.feedback.setdefault((session_id, qid), {**fb, "response_id": None})
            s = self.sessions[session_id]
            s.update(status="completed", overall_score=overall_score,
                     correct_count=correct_count, completed_at=_now())


# --------------------------------------------------------------------------- postgres
class PostgresRepository:
    def __init__(self, url: str):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        # prepare_threshold=None keeps this compatible with Supabase's pooler.
        self.pool = ConnectionPool(url, min_size=1, max_size=5, open=False,
                                   kwargs={"row_factory": dict_row, "prepare_threshold": None,
                                           "connect_timeout": 10})

    def _conn(self):
        return self.pool.connection(timeout=15)

    def init(self) -> None:
        """Create tables (idempotent) and load the 50-question library."""
        self.pool.open(wait=True, timeout=30)
        sql = (MIGRATIONS / "001_init.sql").read_text()
        with self._conn() as conn:
            conn.execute(sql)
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO question_library (category, difficulty, prompt, expected_keywords)
                       VALUES (%s, %s, %s, %s) ON CONFLICT (prompt) DO NOTHING""",
                    [(c, d, p, list(k)) for c, d, p, k in QUESTIONS])

    def ping(self) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _run(self, fn):
        import psycopg
        try:
            with self._conn() as conn:
                return fn(conn)
        except (AlreadyAnswered, PersistenceError):
            raise
        except psycopg.errors.UniqueViolation as e:
            raise AlreadyAnswered() from e
        except Exception as e:  # pool timeout, network, constraint errors
            raise PersistenceError("We couldn't reach the database. Please try again.") from e

    def list_questions(self, difficulty: str) -> list:
        return self._run(lambda c: c.execute(
            "SELECT id, category, difficulty, prompt, expected_keywords FROM question_library "
            "WHERE difficulty = %s ORDER BY id", (difficulty,)).fetchall())

    def get_question(self, question_id: int) -> Optional[dict]:
        return self._run(lambda c: c.execute(
            "SELECT id, category, difficulty, prompt, expected_keywords FROM question_library WHERE id = %s",
            (question_id,)).fetchone())

    def create_session(self, user_id, job_title, difficulty, duration_min, total_questions) -> dict:
        return self._run(lambda c: c.execute(
            """INSERT INTO sessions (user_id, job_title, difficulty, duration_min, total_questions)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (str(user_id), job_title, difficulty, duration_min, total_questions)).fetchone())

    def get_session(self, session_id, user_id) -> Optional[dict]:
        row = self._run(lambda c: c.execute(
            "SELECT * FROM sessions WHERE id = %s AND user_id = %s", (session_id, str(user_id))).fetchone())
        if row:
            row["user_id"] = str(row["user_id"])
        return row

    def asked_questions(self, session_id) -> list:
        return self._run(lambda c: c.execute(
            "SELECT question_id, q_index FROM session_questions WHERE session_id = %s ORDER BY q_index",
            (session_id,)).fetchall())

    def add_session_question(self, session_id, question_id, q_index) -> None:
        self._run(lambda c: c.execute(
            "INSERT INTO session_questions (session_id, question_id, q_index) VALUES (%s, %s, %s)",
            (session_id, question_id, q_index)))

    def save_answer(self, session_id, question_id, text, is_blank, fb: dict, correct_count: int) -> int:
        def tx(c):
            with c.transaction():
                rid = c.execute(
                    """INSERT INTO responses (session_id, question_id, answer_text, is_blank)
                       VALUES (%s, %s, %s, %s) RETURNING id""",
                    (session_id, question_id, text, is_blank)).fetchone()["id"]
                c.execute(
                    """INSERT INTO feedback (session_id, question_id, response_id, score, correct,
                         matched_keywords, missing_keywords, strengths, improvements)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (session_id, question_id, rid, fb["score"], fb["correct"], fb["matched"],
                     fb["missing"], fb["strengths"], fb["improvements"]))
                c.execute("UPDATE sessions SET correct_count = %s WHERE id = %s", (correct_count, session_id))
                return rid
        return self._run(tx)

    def get_responses(self, session_id) -> dict:
        rows = self._run(lambda c: c.execute(
            "SELECT * FROM responses WHERE session_id = %s", (session_id,)).fetchall())
        return {r["question_id"]: r for r in rows}

    def get_feedback(self, session_id) -> dict:
        rows = self._run(lambda c: c.execute(
            """SELECT question_id, response_id, score, correct, matched_keywords AS matched,
                      missing_keywords AS missing, strengths, improvements
               FROM feedback WHERE session_id = %s""", (session_id,)).fetchall())
        return {r["question_id"]: r for r in rows}

    def complete_session(self, session_id, overall_score, correct_count, missing_feedback: dict) -> None:
        def tx(c):
            with c.transaction():
                for qid, fb in missing_feedback.items():
                    c.execute(
                        """INSERT INTO feedback (session_id, question_id, response_id, score, correct,
                             matched_keywords, missing_keywords, strengths, improvements)
                           VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (session_id, question_id) DO NOTHING""",
                        (session_id, qid, fb["score"], fb["correct"], fb["matched"], fb["missing"],
                         fb["strengths"], fb["improvements"]))
                c.execute(
                    """UPDATE sessions SET status = 'completed', overall_score = %s, correct_count = %s,
                              completed_at = now() WHERE id = %s""",
                    (overall_score, correct_count, session_id))
        self._run(tx)


# --------------------------------------------------------------------------- factory
_repo = None


def get_repo():
    """FastAPI dependency. Tests override it with a fresh MemoryRepository."""
    global _repo
    if _repo is None:
        _repo = PostgresRepository(DATABASE_URL) if DATABASE_URL else MemoryRepository()
    return _repo
