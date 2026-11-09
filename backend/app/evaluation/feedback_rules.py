
"""S2-2.2 Feedback generation and scoring — owner: Aisha Aloma."""

BLANK_STRENGTH = ""  # skips never appear under strengths
MAX_IMPROVEMENTS = 2
BLANK_IMPROVEMENT = "You skipped this one, so it is one to work on."
BLANK_TIP = "Answer the question directly to receive feedback."
NOT_REACHED_IMPROVEMENT = "The interview ended before this one, so it is one to work on."
STAR_PARTS = ("Situation", "Task", "Action", "Result")


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


# Rubric lines are written for graders ("Explains that ..."). Turn them into advice.
_RUBRIC_VERBS = {
    "Explains", "States", "Notes", "Mentions", "Names", "Describes", "Gives", "Recommends",
    "Connects", "Provides", "Includes", "Identifies", "Defines", "Shows", "Says", "Uses", "Lists",
}


def _advice(point):
    """'Explains that X' -> 'Mention that X'; 'Names the Y' -> 'Name the Y'; anything else unchanged."""
    verb, _, rest = point.partition(" ")
    if verb not in _RUBRIC_VERBS or not rest:
        return point
    if rest.startswith("that "):
        return "Mention " + rest
    return (verb[:-3] + "y" if verb.endswith("ies") else verb[:-1]) + " " + rest


def _count(n, noun="question"):
    return f"{n} {noun}" + ("" if n == 1 else "s")


def next_step_line(skipped, not_reached):
    """One line for the questions that were skipped (user chose Skip) and/or not reached."""
    those = "that is the one" if skipped + not_reached == 1 else "those are the ones"
    tail = f"so {those} to work on next."
    if skipped and not_reached:
        return f"You skipped {_count(skipped)} and did not reach {not_reached} more, {tail}"
    if skipped:
        return f"You skipped {_count(skipped)}, {tail}"
    verb = "was" if not_reached == 1 else "were"
    return f"{_count(not_reached)} {verb} not reached before the interview ended, {tail}"


def _and(words):
    """'Task' / 'Task and Result' / 'Situation, Task and Result'."""
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _star_parts(points):
    return [t.split(":", 1)[0] for t in points if t.split(":", 1)[0] in STAR_PARTS]


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

    # A quote inside a longer quote would repeat words back to the user.
    evidence_points = [
        p for p in evidence_points
        if not any(p != other and p in other for other in evidence_points)
    ]
    # Behavioral rubric lines start with "Situation:", "Task:"...; name the
    # parts covered instead of quoting the user's own answer back at them.
    star = _star_parts(met_points)

    if star:
        strengths = f"Your answer covered the {_and(star)}."
    elif evidence_points:
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

    missed_star = _star_parts(missed_points)

    if missed_star:
        improvements = (
            f"Add the {_and(missed_star)} "
            + ("part" if len(missed_star) == 1 else "parts")
            + " of STAR to your answer."
        )
    elif missed_points:
        top = missed_points[:2]
        advice = [_advice(p) for p in top]
        if advice != top:
            improvements = " ".join(a + "." for a in advice)
        else:  # plain keywords, not sentences
            improvements = "Points to add: " + "; ".join(top) + "."
    else:
        improvements = "Keep supporting your answers with clear examples."

    return {
        "strengths": strengths,
        "improvements": improvements,
    }


def session_feedback(answer_scores, answers=None, not_started=0) -> dict:
    """Summarize feedback across an interview session.

    An answer of "" is a skip; None means the question was not reached (the interview
    ended first). not_started counts questions that were never even shown.
    """
    answer_scores = list(answer_scores)

    if answers is None:
        answers = [""] * len(answer_scores)
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
        reached = answer is not None

        matched = _grade_items(grade, "criteria_met", "matched")
        missing = _grade_items(grade, "criteria_missed", "missing")

        score = 0 if blank else getattr(grade, "score", 0)
        correct = False if blank else getattr(grade, "correct", False)

        if not reached:
            status = "not_reached"
        elif blank:
            status = "blank"
        elif correct:
            status = "correct"
        elif matched:
            status = "partial"
        else:
            status = "incorrect"

        if not reached:
            fb = {"strengths": BLANK_STRENGTH, "improvements": NOT_REACHED_IMPROVEMENT}

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
            "not_reached_count": not_started,
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
    not_reached_count = not_started + sum(
        1 for item in results if item["status"] == "not_reached"
    )

    # Skips and unreached questions have no feedback of their own.
    graded = [i for i in results if i["status"] not in ("blank", "not_reached")]
    improvements = [i["improvements"] for i in graded if i["missing"]]
    good = sum(1 for i in graded if i["matched"])

    if unanswered_count or not_reached_count:
        # The skip line always shows, so it takes one of the 2 improvement slots.
        improvements = improvements[:MAX_IMPROVEMENTS - 1]
        improvements.append(next_step_line(unanswered_count, not_reached_count))
    else:
        improvements = improvements[:MAX_IMPROVEMENTS]

    return {
        "overall": overall,
        "correct_count": correct_count,
        "total": len(results),
        "unanswered_count": unanswered_count,
        "not_reached_count": not_reached_count,
        # A short summary only: the specific detail lives under each question.
        "strengths": (
            f"You made good points in {_count(good, 'answer')}. "
            "See each question below for what went well."
            if good
            else "Keep practicing your answers."
        ),
        "improvements": (
            " ".join(improvements)
            if improvements
            else "You covered the expected points across your answers."
        ),
        "answers": results,
    }
