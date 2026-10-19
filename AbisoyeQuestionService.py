"""S1-2.2 Question-selection service — owner: Moshood Abisoye"""


class NoQuestionAvailable(Exception):
    pass


def next_question(session_id: int, difficulty: str) -> dict:
    """Return the next library question for this session.

    TODO: load ids already asked in this session
    TODO: pick one unused question matching the difficulty
    TODO: raise NoQuestionAvailable when none is left (endpoint maps it to 404/409)
    TODO: return only id, prompt, q_index, total (keep expected_keywords server-side)
    """
    raise NotImplementedError