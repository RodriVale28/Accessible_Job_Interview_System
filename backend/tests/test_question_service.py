import pytest

# Adjust this import to the real file location in the repo.
from app.services import question_service as qs


class FakeRepo:
    def __init__(self, total=3, library=None):
        self.total = total
        self.library = library if library is not None else [
            {"id": i, "prompt": f"Question {i}", "category": "Coding", "difficulty": "Easy"} for i in range(1, 6)
        ]
        self.asked = []  # list of (question_id, q_index)

    def get_total_questions(self, session_id):
        return self.total

    def count_asked_questions(self, session_id):
        return len(self.asked)

    def pick_unused_question(self, session_id, difficulty):
        used = {qid for qid, _ in self.asked}
        for q in self.library:
            if q["difficulty"] == difficulty and q["id"] not in used:
                return {"id": q["id"], "prompt": q["prompt"], "category": q["category"]}
        return None

    def record_asked_question(self, session_id, question_id, q_index):
        self.asked.append((question_id, q_index))


def test_returns_only_ui_fields():
    result = qs.next_question(1, "Easy", repo=FakeRepo())
    assert set(result) == {"id", "prompt", "category", "q_index", "total"}
    assert "expected_keywords" not in result
    assert result["q_index"] == 1 and result["total"] == 3


def test_never_repeats_and_index_increments():
    repo = FakeRepo(total=3)
    results = [qs.next_question(1, "Easy", repo=repo) for _ in range(3)]
    assert [r["q_index"] for r in results] == [1, 2, 3]
    assert len({r["id"] for r in results}) == 3


def test_raises_when_session_is_finished():
    repo = FakeRepo(total=2)
    qs.next_question(1, "Easy", repo=repo)
    qs.next_question(1, "Easy", repo=repo)
    with pytest.raises(qs.NoQuestionAvailable) as exc:
        qs.next_question(1, "Easy", repo=repo)
    assert exc.value.reason == "session_complete"


def test_raises_when_library_has_none_for_difficulty():
    with pytest.raises(qs.NoQuestionAvailable) as exc:
        qs.next_question(1, "Hard", repo=FakeRepo())
    assert exc.value.reason == "library_empty"
    assert "No Hard questions" in str(exc.value)


def test_raises_when_library_runs_out_before_total():
    repo = FakeRepo(total=5, library=[{"id": 1, "prompt": "Only one", "category": "Coding", "difficulty": "Easy"}])
    qs.next_question(1, "Easy", repo=repo)
    with pytest.raises(qs.NoQuestionAvailable):
        qs.next_question(1, "Easy", repo=repo)


def test_unknown_session_raises():
    repo = FakeRepo()
    repo.total = None
    with pytest.raises(qs.NoQuestionAvailable):
        qs.next_question(99, "Easy", repo=repo)