# ==========================================================================
# Interview Studio — S1-2.3: Tests for question retrieval
# Owner (Sprint 1): Arvin Barghi   |   Story: US-2 Receive Interview Questions
#
# This file collects the parts of the shared Interview Studio prototype that
# Arvin Barghi owns. The prototype was built by the team before tasks were
# assigned; from Sprint 1 on, Arvin maintains and extends this part.
# It is a reference copy — the running app still uses the original files.
#
# HOW IT WORKS
#  - Pytest runs Python test functions; FastAPI's TestClient calls the API like a browser would, without a real server.
#  - A test database (or Supabase test schema) gives every test a known starting point.
#
# YOUR SPRINT 1 WORK (see the starter file in this folder)
#  - Tests for: a valid question is returned, difficulty filter works, no repeats within a session, empty library returns the error state, and the DB read actually happens.
#  - Add a small fixture that seeds 3–5 known questions so results are predictable.
# ==========================================================================

# --------------------------------------------------------------------------
# FROM: database.py, lines 117-125
# WHAT IT DOES: The query your tests will exercise (through Moshood's endpoint).
# --------------------------------------------------------------------------
def library_questions(category=None, difficulty=None, limit=20):
    sql = "SELECT * FROM question_library WHERE 1=1"
    params = []
    if category:
        sql += " AND category = %s"; params.append(category)
    if difficulty:
        sql += " AND difficulty = %s"; params.append(difficulty)
    sql += " ORDER BY RAND() LIMIT %s"; params.append(limit)
    return query(sql, tuple(params))

