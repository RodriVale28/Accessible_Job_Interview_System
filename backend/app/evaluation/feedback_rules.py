"""S1-5.2 Feedback-generation rules — owner: Aisha Aloma"""


def feedback_for_answer(answer_score, answer=None) -> dict:
    """Generate rule-based feedback for one evaluated answer."""

    matched = list(getattr(answer_score, "matched", []) or [])
    missing = list(getattr(answer_score, "missing", []) or [])
    score = getattr(answer_score, "score", 0)
    correct = getattr(answer_score, "correct", False)

    if answer is not None and not answer.strip():
        strengths = "No answer was provided."
        improvements = (
            "Try answering the question and including relevant keywords."
        )
        tip = "Start by answering the question directly."
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

    return {
        "score": score,
        "correct": correct,
        "matched": matched,
        "missing": missing,
        "strengths": strengths,
        "improvements": improvements,
        "tip": tip,
    }


def session_feedback(answer_scores, answers=None) -> dict:
    """Generate an overall feedback summary for a session."""

    answer_scores = list(answer_scores)

    if answers is None:
        answers = [None] * len(answer_scores)
    else:
        answers = list(answers)
        if len(answers) != len(answer_scores):
            raise ValueError(
                "answers and answer_scores must have the same length."
            )

    results = [
        feedback_for_answer(score, answer)
        for score, answer in zip(answer_scores, answers)
    ]

    if not results:
        return {
            "overall": 0,
            "strengths": "No answers were evaluated.",
            "improvements": "Complete an answer to receive feedback.",
            "answers": [],
        }

    overall = round(
        sum(item["score"] for item in results) / len(results)
    )

    strengths = [
        item["strengths"]
        for item in results
        if item["matched"] or item["strengths"] == "No answer was provided."
    ]

    improvements = [
        item["improvements"]
        for item in results
        if item["missing"] or item["strengths"] == "No answer was provided."
    ]

    return {
        "overall": overall,
        "strengths": (
            " ".join(strengths)
            if strengths
            else "Keep practicing your answers."
        ),
        "improvements": (
            " ".join(improvements)
            if improvements
            else "You included the expected keywords across your answers."
        ),
        "answers": results,
    }
