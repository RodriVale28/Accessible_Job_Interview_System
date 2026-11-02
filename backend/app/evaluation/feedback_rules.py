
"""S2-2.2 Feedback generation and scoring — owner: Aisha Aloma."""

BLANK_STRENGTH = "You skipped this one, so it is one to work on."
BLANK_IMPROVEMENT = "You skipped this one, so it is one to work on."
BLANK_TIP = "Answer the question directly to receive feedback."


def _is_blank(answer_text):
    return answer_text is None or not str(answer_text).strip()


def _clean_text(value):
    """Remove extra whitespace and trailing punctuation."""
    return str(value).strip().rstrip(".!? ")


def _criterion_text(item):
    """Extract readable text from a grading criterion."""
    if isinstance(item, dict):
        value = (
            item.get("description")
            or item.get("criterion")
            or item.get("text")
            or ""
        )
        return _clean_text(value)
    return _clean_text(item)


def _evidence_text(item):
    """Extract readable evidence from a grading result."""
    if isinstance(item, dict):
        value = (
            item.get("evidence")
            or item.get("text")
            or item.get("quote")
            or ""
        )
        if isinstance(value, (list, tuple)):
            return "; ".join(
                text for entry in value
                if (text := _evidence_text(entry))
            )
        return _clean_text(value)
    return _clean_text(item)


def _grade_items(grade, new_field, legacy_field):
    """Support Sprint 2 criteria and older keyword results."""
    items = getattr(grade, new_field, None)
    if items is None:
        items = getattr(grade, legacy_field, [])
    return list(items or [])


def feedback_for_answer(grade, answer_text) -> dict:
    """Return strengths and improvements based on grading criteria."""
    if _is_blank(answer_text):
        return {
            "strengths": BLANK_STRENGTH,
            "improvements": BLANK_IMPROVEMENT,
        }

    matched = _grade_items(grade, "criteria_met", "matched")
    missing = _grade_items(grade, "criteria_missed", "missing")
    evidence = list(getattr(grade, "evidence", []) or [])

    evidence_points = []

    for item in matched:
        if isinstance(item, dict) and item.get("evidence"):
            point = _evidence_text(item["evidence"])
            if point:
                evidence_points.append(point)

    for item in evidence:
        point = _evidence_text(item)
        if point and point not in evidence_points:
            evidence_points.append(point)

    met_points = [
        text for item in matched
        if (text := _criterion_text(item))
    ]

    missed_points = [
        text for item in missing
        if (text := _criterion_text(item))
    ]

    if evidence_points:
        strengths = (
            "Your answer showed: "
            + "; ".join(evidence_points[:3])
            + "."
        )
    elif met_points:
        strengths = (
            "Your answer covered: "
            + "; ".join(met_points[:3])
            + "."
        )
    else:
        strengths = "Keep working on explaining your answer clearly."

    if missed_points:
        improvements = (
            "Work on these areas: "
            + "; ".join(missed_points[:2])
            + "."
        )
    else:
        improvements = "Keep supporting your answers with clear examples."

    return {
        "strengths": strengths,
        "improvements": improvements,
    }


def session_feedback(answer_scores, answers=None) -> dict:
    """Summarize feedback across an interview session."""
    answer_scores = list(answer_scores)

    if answers is None:
        answers = [None] * len(answer_scores)
    else:
        answers = list(answers)
        if len(answers) != len(answer_scores):
            raise ValueError(
                "answers and answer_scores must have the same length."
            )

    results = []

    for grade, answer in zip(answer_scores, answers):
        fb = feedback_for_answer(grade, answer)
        blank = _is_blank(answer)

        matched = _grade_items(grade, "criteria_met", "matched")
        missing = _grade_items(grade, "criteria_missed", "missing")

        score = 0 if blank else getattr(grade, "score", 0)
        correct = False if blank else getattr(grade, "correct", False)

        if blank:
            status = "blank"
        elif correct:
            status = "correct"
        elif matched:
            status = "partial"
        else:
            status = "incorrect"

        results.append({
            "score": score,
            "correct": correct,
            "answered": not blank,
            "status": status,
            "matched": matched,
            "missing": missing,
            "strengths": fb["strengths"],
            "improvements": fb["improvements"],
            "tip": (
                BLANK_TIP
                if blank
                else "Use specific examples to support your answer."
            ),
        })

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

    overall = round(
        sum(item["score"] for item in results) / len(results)
    )

    correct_count = sum(
        1 for item in results if item["correct"]
    )

    unanswered_count = sum(
        1 for item in results if item["status"] == "blank"
    )

    strengths = [
        item["strengths"]
        for item in results
        if item["status"] != "blank" and item["matched"]
    ]

    improvements = [
        item["improvements"]
        for item in results
        if item["status"] != "blank" and item["missing"]
    ]

    if unanswered_count:
        question_word = (
            "question" if unanswered_count == 1 else "questions"
        )
        improvements.append(
            f"You skipped {unanswered_count} {question_word}, "
            "so those are the ones to work on next."
        )

    return {
        "overall": overall,
        "correct_count": correct_count,
        "total": len(results),
        "unanswered_count": unanswered_count,
        "strengths": (
            " ".join(strengths)
            if strengths
            else "Keep practicing your answers."
        ),
        "improvements": (
            " ".join(improvements)
            if improvements
            else "You covered the expected points across your answers."
        ),
        "answers": results,
    }
