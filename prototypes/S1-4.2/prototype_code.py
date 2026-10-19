# ==========================================================================
# Interview Studio — S1-4.2: Persistence (repository) layer
# Owner (Sprint 1): Sublime Mpanda   |   Story: US-4 Save Session & Responses
#
# This file collects the parts of the shared Interview Studio prototype that
# Sublime Mpanda owns. The prototype was built by the team before tasks were
# assigned; from Sprint 1 on, Sublime maintains and extends this part.
# It is a reference copy — the running app still uses the original files.
#
# HOW IT WORKS
#  - Routes never write SQL themselves; they call database.py. This keeps every SQL statement in one place.
#  - Every read and write is scoped by user_id, so one user can never see another user's interview.
#  - All queries use %s placeholders (parameterised), which prevents SQL injection.
#
# YOUR SPRINT 1 WORK (see the starter file in this folder)
#  - Write the FastAPI repository module for PostgreSQL: create_session, save_response, complete_session, get_session_with_responses.
#  - Catch database errors and raise a clear application error so the API can show a safe message.
# ==========================================================================

# --------------------------------------------------------------------------
# FROM: database.py, lines 17-23
# WHAT IT DOES: Opens a MySQL connection from config.
# --------------------------------------------------------------------------
def get_conn(with_db=True):
    """Open a MySQL connection. with_db=False connects to the server only
    (used once to CREATE DATABASE during setup)."""
    params = dict(Config.DB)
    if not with_db:
        params.pop("database", None)
    return mysql.connector.connect(**params)

# --------------------------------------------------------------------------
# FROM: database.py, lines 26-35
# WHAT IT DOES: Runs a SELECT with parameters and returns dict rows.
# --------------------------------------------------------------------------
def query(sql, params=None, one=False):
    """Run a SELECT and return dict rows (or a single dict with one=True)."""
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()

# --------------------------------------------------------------------------
# FROM: database.py, lines 38-47
# WHAT IT DOES: Runs INSERT/UPDATE/DELETE, commits, returns the new row id.
# --------------------------------------------------------------------------
def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE. Returns lastrowid for inserts."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

# --------------------------------------------------------------------------
# FROM: database.py, lines 141-146
# WHAT IT DOES: Reads one session, always scoped to the logged-in user.
# --------------------------------------------------------------------------
def get_interview(interview_id, user_id):
    """Scoped to user_id -> enforces NF2 (no cross-user access)."""
    return query(
        "SELECT * FROM interviews WHERE id = %s AND user_id = %s",
        (interview_id, user_id), one=True,
    )

# --------------------------------------------------------------------------
# FROM: database.py, lines 177-181
# WHAT IT DOES: Saves a question asked in a session.
# --------------------------------------------------------------------------
def add_question(interview_id, q_index, prompt, source="ai", tag=None):
    return execute(
        "INSERT INTO questions (interview_id, q_index, prompt, source, tag) VALUES (%s,%s,%s,%s,%s)",
        (interview_id, q_index, prompt, source, tag),
    )

# --------------------------------------------------------------------------
# FROM: database.py, lines 188-192
# WHAT IT DOES: Saves an answer linked to its question, session and user.
# --------------------------------------------------------------------------
def add_answer(question_id, interview_id, user_id, content):
    return execute(
        "INSERT INTO answers (question_id, interview_id, user_id, content) VALUES (%s,%s,%s,%s)",
        (question_id, interview_id, user_id, content),
    )

# --------------------------------------------------------------------------
# FROM: database.py, lines 156-161
# WHAT IT DOES: Pause / resume / in_progress.
# --------------------------------------------------------------------------
def set_status(interview_id, user_id, status):
    """Pause / resume / in_progress (F9, R11)."""
    execute(
        "UPDATE interviews SET status = %s WHERE id = %s AND user_id = %s",
        (status, interview_id, user_id),
    )

# --------------------------------------------------------------------------
# FROM: database.py, lines 164-171
# WHAT IT DOES: Marks the session completed with score and summary.
# --------------------------------------------------------------------------
def complete_interview(interview_id, user_id, overall, strengths, improvements):
    execute(
        """UPDATE interviews
           SET status='completed', overall_score=%s, strengths=%s, improvements=%s,
               completed_at=NOW()
           WHERE id=%s AND user_id=%s""",
        (int(overall), strengths, improvements, interview_id, user_id),
    )

# --------------------------------------------------------------------------
# FROM: database.py, lines 208-223
# WHAT IT DOES: Questions + answers + feedback for one session, in order.
# --------------------------------------------------------------------------
def get_transcript(interview_id, user_id):
    """Full ordered transcript with each answer's feedback (F7, R9)."""
    if not get_interview(interview_id, user_id):
        return None
    return query(
        """SELECT q.q_index, q.prompt, q.tag, q.source,
                  a.content AS answer, a.id AS answer_id,
                  f.structure, f.clarity, f.relevance, f.completeness,
                  f.confidence, f.strengths, f.improvements, f.tip
           FROM questions q
           LEFT JOIN answers  a ON a.question_id = q.id
           LEFT JOIN feedback f ON f.answer_id   = a.id
           WHERE q.interview_id = %s
           ORDER BY q.q_index""",
        (interview_id,),
    )

