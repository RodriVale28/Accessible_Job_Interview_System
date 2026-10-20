"""S1-5.2 Feedback-generation rules — owner: Aisha Aloma"""

BLANK_STRENGTH = "No answer was provided."
BLANK_IMPROVEMENT = "Try answering the question and including relevant keywords."
BLANK_TIP = "Start by answering the question directly."


def _is_blank(answer):
    return answer is not None and not str(answer).strip()


def feedback_for_answer(answer_score, answer=None) -> dict:
    matched = list(getattr(answer_score, "matched", []) or [])
    missing = list(getattr(answer_score, "missing", []) or [])
    score = getattr(answer_score, "score", 0)
    correct = getattr(answer_score, "correct", False)
    blank = _is_blank(answer)

    if blank:
        status = "blank"
        strengths = BLANK_STRENGTH
        improvements = BLANK_IMPROVEMENT
        tip = BLANK_TIP
    else:
        if matched:
            strengths = (
                "You demonstrated understanding by mentioning: "
                + ", ".join(matched)
                + "."
            )
        else:
            strengths = "Keep practicing how to connect your answer to the question."

        if missing:
            improvements = "Try mentioning " + ", ".join(missing) + "."
            tip = "Review the missing concepts and explain how they relate to the question."
        else:
            improvements = "You included all the expected keywords."
            tip = "Continue supporting your answers with clear examples."

        if correct:
            status = "correct"
        elif matched:
            status = "partial"
        else:
            status = "incorrect"

    return {
        "score": score,
        "correct": correct,
        "answered": not blank,
        "status": status,
        "matched": matched,
        "missing": missing,
        "strengths": strengths,
        "improvements": improvements,
        "tip": tip,
    }


def session_feedback(answer_scores, answers=None) -> dict:
    answer_scores = list(answer_scores)

    if answers is None:
        answers = [None] * len(answer_scores)
    else:
        answers = list(answers)
        if len(answers) != len(answer_scores):
            raise ValueError("answers and answer_scores must have the same length.")

    results = [
        feedback_for_answer(score, answer)
        for score, answer in zip(answer_scores, answers)
    ]

    if not results:
        return {
            "overall": 0,
            "correct_count": 0,
            "total": 0,
            "unanswered_count": 0,
            "strengths": "No answers were evaluated.",
            "improvements": "Complete an answer to receive feedback.",
            "answers": [],
        }

    overall = round(sum(item["score"] for item in results) / len(results))
    correct_count = sum(1 for item in results if item["correct"])
    unanswered_count = sum(1 for item in results if item["status"] == "blank")

    strengths = [
        item["strengths"]
        for item in results
        if item["matched"] or item["status"] == "blank"
    ]
    improvements = [
        item["improvements"]
        for item in results
        if item["missing"] or item["status"] == "blank"
    ]

    return {
        "overall": overall,
        "correct_count": correct_count,
        "total": len(results),
        "unanswered_count": unanswered_count,
        "strengths": " ".join(strengths) if strengths else "Keep practicing your answers.",
        "improvements": (
            " ".join(improvements)
            if improvements
            else "You included the expected keywords across your answers."
        ),
        "answers": results,
    }
