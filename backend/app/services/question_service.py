"""S1-2.2 Question-selection service — owner: Moshood Abisoye"""


class NoQuestionAvailable(Exception):
    """No question can be returned.

    reason == "library_empty"    -> the endpoint should answer 404
    reason == "not_found"        -> the endpoint should answer 404
    reason == "session_complete" -> the endpoint should answer 409
    """

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


def _default_repo():
    # Imported lazily so tests can pass in a fake repo without a database.
    from app import repository
    return repository


def next_question(session_id: int, difficulty: str, repo=None) -> dict:
    """Return the next library question for this session.

    Returns id, prompt, category, q_index, total. expected_keywords never leaves
    the database layer.
    """
    repo = repo or _default_repo()

    total = repo.get_total_questions(session_id)          # sessions.total_questions
    if total is None:
        raise NoQuestionAvailable("Interview session not found.", "not_found")

    asked = repo.count_asked_questions(session_id)        # rows in session_questions
    if asked >= total:
        raise NoQuestionAvailable("All questions for this session have been asked.", "session_complete")

    question = repo.pick_unused_question(session_id, difficulty)
    if question is None:
        raise NoQuestionAvailable(f"No {difficulty} questions available.", "library_empty")

    q_index = asked + 1
    repo.record_asked_question(session_id, question["id"], q_index)

    return {
        "id": question["id"],
        "prompt": question["prompt"],
        "category": question["category"],
        "q_index": q_index,
        "total": total,
    }

def current_question(repo, session: dict):
    """Return (question, q_index) for the question the user is answering now.

    question is the full library row (with expected_keywords, for scoring only) or None
    when the last asked question is already answered or nothing has been asked yet.
    """
    asked = repo.asked_questions(session["id"])
    if not asked:
        return None, 0
    last = asked[-1]
    if last["question_id"] in repo.get_responses(session["id"]):
        return None, last["q_index"]
    return repo.get_question(last["question_id"]), last["q_index"]
