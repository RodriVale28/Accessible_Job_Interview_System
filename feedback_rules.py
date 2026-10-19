"""S1-5.2 Feedback-generation rules — owner: Aisha Aloma"""


def feedback_for_answer(answer_score) -> dict:
    """Turn one KeywordEvaluator result into feedback.

    TODO: matched keywords -> strength sentence
    TODO: missing keywords -> "Try mentioning ..." improvement
    TODO: blank answer -> missing-answer note
    """
    raise NotImplementedError


def session_feedback(answer_scores) -> dict:
    # TODO: overall summary payload consumed by the results page (S1-5.3)
    raise NotImplementedError
