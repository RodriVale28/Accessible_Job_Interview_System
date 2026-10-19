# ==========================================================================
# Interview Studio — S1-2.2: Question-selection service and endpoint
# Owner (Sprint 1): Moshood Abisoye   |   Story: US-2 Receive Interview Questions
#
# This file collects the parts of the shared Interview Studio prototype that
# Moshood Abisoye owns. The prototype was built by the team before tasks were
# assigned; from Sprint 1 on, Moshood maintains and extends this part.
# It is a reference copy — the running app still uses the original files.
#
# HOW IT WORKS
#  - The prototype generates questions with AI, and falls back to built-in questions when there is no API key.
#  - library_questions() already exists but no route calls it yet. That is the gap your task fills.
#
# YOUR SPRINT 1 WORK (see the starter file in this folder)
#  - Write a FastAPI service and endpoint (for example GET /sessions/{id}/next-question) that picks the next library question for the session's difficulty and never repeats one already asked.
#  - Return only what the UI needs (id, prompt, index, total). Keep expected_keywords on the server.
#  - Return a clear error (404/409) when no question is available.
# ==========================================================================

# --------------------------------------------------------------------------
# FROM: database.py, lines 117-125
# WHAT IT DOES: Picks random questions from the library, filtered by category/difficulty. Not yet called by any route.
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

# --------------------------------------------------------------------------
# FROM: llm.py, lines 78-110
# WHAT IT DOES: How the prototype gets questions today: AI first, built-in questions as a fallback.
# --------------------------------------------------------------------------
def generate_questions(track, difficulty, count=4, job_description=None):
    """Return a list of question strings. Uses the job description when given (F2)."""
    if job_description:
        user = (f"Generate {count} {difficulty} technical interview questions tailored to "
                f"THIS job description. Focus on skills it names.\n\nJob description:\n{job_description}")
    else:
        user = f"Generate {count} {difficulty} interview questions for a '{track}' interview."

    data = _chat_json(_QUESTION_SYS, user)
    if data and isinstance(data.get("questions"), list) and data["questions"]:
        return data["questions"][:count]

    # ---- offline mock ----
    opener = OPENERS.get(track, OPENERS["Behavioral"])
    if track == "Technical / Coding":
        extras = [
            "Given an array of integers, how would you find two numbers that add up to a target? What's the time complexity?",
            "How would you check whether a string of brackets is balanced? Which data structure would you use?",
            "Explain how a hash map works and what happens on a collision.",
            "How would you find the first non-repeating character in a string?",
            "Walk me through how you'd debug a function that works locally but fails in production.",
        ]
        random.shuffle(extras)
        return [opener] + extras[: max(0, count - 1)]
    extras = [
        "Describe a project you're proud of and the hardest problem you solved on it.",
        "Tell me about a time you received difficult feedback. What did you do with it?",
        "How do you approach a problem when you're unsure where to start?",
        "Walk me through a technical trade-off you made and why.",
        "Tell me about a time you had to learn something quickly under pressure.",
    ]
    random.shuffle(extras)
    return [opener] + extras[: max(0, count - 1)]

