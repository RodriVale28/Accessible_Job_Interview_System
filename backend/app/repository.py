"""S1-4.2 Persistence layer for PostgreSQL — owner: Sublime Mpanda"""


class PersistenceError(Exception):
    pass


def create_session(user_id, job_title, difficulty, duration_min) -> int:
    # TODO: INSERT session, return id; wrap DB errors in PersistenceError
    raise NotImplementedError


def save_response(session_id, question_id, user_id, text) -> int:
    # TODO
    raise NotImplementedError


def complete_session(session_id, user_id, overall_score) -> None:
    # TODO
    raise NotImplementedError


def get_session_with_responses(session_id, user_id) -> dict:
    # TODO: always filter by user_id (users only see their own data)
    raise NotImplementedError
