# ==========================================================================
# Interview Studio — S1-1.2: Start-session API (FastAPI + Pydantic)
# Owner (Sprint 1): Owen Erickson   |   Story: US-1 Configure Technical Interview
#
# This file collects the parts of the shared Interview Studio prototype that
# Owen Erickson owns. The prototype was built by the team before tasks were
# assigned; from Sprint 1 on, Owen maintains and extends this part.
# It is a reference copy — the running app still uses the original files.
#
# HOW IT WORKS
#  - The route reads the JSON body (track, difficulty, mode, length, job title, job description) and rejects tracks that are not allowed (400 error).
#  - It saves a new row in the interviews table, decides how many questions to ask (15 min = 4, 30 = 6, 45 = 8, from config.py), and stores the first question.
#  - It returns interview_id, the first question, q_index and total so the front end can draw the progress indicator.
#
# YOUR SPRINT 1 WORK (see the starter file in this folder)
#  - Write Pydantic models: SessionCreate (job_title, difficulty, duration_min limited to 15/30/45, interview_type = "Technical") and SessionStartResponse.
#  - Write the FastAPI endpoint (for example POST /sessions) that validates input, creates the session through Sublime's repository (S1-4.2) and returns the start response.
#  - Agree the request/response shape with Kobra, Kieu, Moshood and Sublime first (Step 1 of the execution order).
# ==========================================================================

# --------------------------------------------------------------------------
# FROM: app.py, lines 115-115
# WHAT IT DOES: Which interview tracks the API accepts.
# --------------------------------------------------------------------------
ALLOWED_TRACKS = ("Behavioral", "Technical / Coding")

# --------------------------------------------------------------------------
# FROM: app.py, lines 118-147
# WHAT IT DOES: POST /api/interviews: validate input, create the session row, decide question count, store and return the first question.
# --------------------------------------------------------------------------
@app.post("/api/interviews")
@login_required
def start_interview():
    d = request.get_json(force=True)
    uid = current_user_id()
    track = d.get("track", "Behavioral")
    if track not in ALLOWED_TRACKS:             # scope: Behavioral + Technical only
        return jsonify(error=f"Unsupported track. Choose one of: {', '.join(ALLOWED_TRACKS)}"), 400
    difficulty = d.get("difficulty", "Standard")
    mode = d.get("mode", "mock")               # 'mock' | 'practice'
    length = int(d.get("length", 15))
    job_title = (d.get("job_title") or "").strip() or None
    job_desc = (d.get("job_description") or "").strip() or None

    iv_id = db.create_interview(uid, track, difficulty, mode, length, job_title, job_desc)

    # how many questions to ask
    count = 1 if mode == "practice" else Config.QUESTIONS_BY_LENGTH.get(length, 4)
    try:
        questions = llm.generate_questions(track, difficulty, count, job_desc)
    except Exception:
        return jsonify(error="Could not reach the AI service. Please retry."), 502  # NF12

    # store only the first question now; follow-ups come from analysis
    source = "job_desc" if job_desc else "ai"
    first = questions[0]
    db.add_question(iv_id, 1, first, source=source, tag="Opening question")

    return jsonify(interview_id=iv_id, mode=mode, question=first,
                   q_index=1, total=count, tag="Opening question")

# --------------------------------------------------------------------------
# FROM: database.py, lines 131-138
# WHAT IT DOES: INSERT that creates the session row.
# --------------------------------------------------------------------------
def create_interview(user_id, track, difficulty, mode, length_min,
                     job_title=None, job_description=None):
    return execute(
        """INSERT INTO interviews
           (user_id, track, difficulty, mode, length_min, job_title, job_description)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (user_id, track, difficulty, mode, int(length_min), job_title, job_description),
    )

# --------------------------------------------------------------------------
# FROM: config.py
# WHAT IT DOES: Session length -> number of questions.
# --------------------------------------------------------------------------
    # How many questions a mock interview asks, by session length
    QUESTIONS_BY_LENGTH = {15: 4, 30: 6, 45: 8}