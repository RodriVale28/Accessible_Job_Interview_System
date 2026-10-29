"""S2 Tests for the Gemini grader and its keyword-grading fallback.

Written ahead of the grader itself: every test here is skipped until
app/evaluation/gemini_grader.py exists. The tests expect this interface:

    GeminiGrader(api_key, http_client=None, model=..., timeout=...)
        .grade(question, answer, expected_keywords) -> result
        Calls the Gemini REST API (generateContent) with httpx and raises on any failure.

    grade_answer(question, answer, expected_keywords, gemini=None, keyword=None) -> result
        Tries Gemini first. On any HTTP error, exception, timeout or unusable reply it
        falls back to KeywordEvaluator (the Sprint 1 grader, unchanged).
        Raises GradingError if the keyword fallback fails as well.

    result has: score (int 0-100), correct (bool), matched, missing, reasons,
    and grader ("ai" or "keyword", same values as the feedback.grader column).

Gemini is asked to reply with JSON text like
    {"score": 85, "correct": true, "criteria_met": [...], "criteria_missed": [...],
     "evidence": [...], "reasons": [...]}

No test here touches the network except the live ones at the bottom, which run
only when GEMINI_API_KEY is set.
"""
import json
import os

import httpx
import pytest

from app.evaluation.keyword_evaluator import KeywordEvaluator

gemini_grader = pytest.importorskip(
    "app.evaluation.gemini_grader", reason="Gemini grader not implemented yet"
)
GeminiGrader = gemini_grader.GeminiGrader
GradingError = gemini_grader.GradingError
grade_answer = gemini_grader.grade_answer

QUESTION = "What is a stack and how do you add and remove items from it?"
KEYWORDS = ["LIFO", "push", "pop", "stack"]
STRONG_ANSWER = (
    "A stack is a LIFO structure: the last item added is the first one removed. "
    "You push to add an item to the top and pop to remove the top item."
)
WEAK_ANSWER = "It is a kind of list where you keep things."

GOOD_VERDICT = {
    "score": 90,
    "correct": True,
    "criteria_met": ["Explains LIFO order", "Names push and pop"],
    "criteria_missed": [],
    "evidence": ["the last item added is the first one removed", "push to add ... pop to remove"],
    "reasons": ["Clear and complete definition."],
}


def gemini_body(verdict):
    """A generateContent response whose text part is the verdict as JSON."""
    text = verdict if isinstance(verdict, str) else json.dumps(verdict)
    return {
        "candidates": [{
            "content": {"role": "model", "parts": [{"text": text}]},
            "finishReason": "STOP",
        }]
    }


class FakeGemini:
    """httpx transport standing in for the Gemini API; records each request."""

    def __init__(self, status=200, body=None, raises=None):
        self.status = status
        self.body = gemini_body(GOOD_VERDICT) if body is None else body
        self.raises = raises
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if self.raises is not None:
            raise self.raises
        if isinstance(self.body, (bytes, str)):
            return httpx.Response(self.status, content=self.body)
        return httpx.Response(self.status, json=self.body)


def make_grader(fake, api_key="test-key"):
    # timeout=None: the grader must set its own timeout, not rely on httpx's default.
    client = httpx.Client(transport=httpx.MockTransport(fake), timeout=None)
    return GeminiGrader(api_key=api_key, http_client=client)


def keyword_result(answer=STRONG_ANSWER):
    return KeywordEvaluator().score_answer(answer, KEYWORDS)


def assert_keyword_fallback(result, answer=STRONG_ANSWER):
    expected = keyword_result(answer)
    assert result.grader == "keyword"
    assert result.score == expected.score
    assert result.correct == expected.correct
    assert result.matched == expected.matched
    assert result.missing == expected.missing


class BrokenKeywordEvaluator:
    def score_answer(self, answer, expected_keywords):
        raise RuntimeError("keyword grader exploded")


# --- successful Gemini call ---------------------------------------------------

def test_successful_call_returns_valid_ai_result():
    fake = FakeGemini()
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(fake))

    assert len(fake.requests) == 1
    assert result.grader == "ai"
    assert isinstance(result.score, int) and 0 <= result.score <= 100
    assert isinstance(result.correct, bool)
    # Gemini's verdict is passed through, not replaced by keyword matching.
    assert result.score == GOOD_VERDICT["score"]
    assert result.correct is True
    assert result.reasons == GOOD_VERDICT["reasons"]


def test_grader_reports_low_score_for_weak_answer():
    weak = {**GOOD_VERDICT, "score": 15, "correct": False,
            "criteria_met": [], "criteria_missed": ["Explains LIFO order", "Names push and pop"],
            "evidence": [], "reasons": ["Does not explain how items are added or removed."]}
    result = grade_answer(QUESTION, WEAK_ANSWER, KEYWORDS, gemini=make_grader(FakeGemini(body=gemini_body(weak))))

    assert result.grader == "ai"
    assert result.score == 15
    assert result.correct is False


def test_request_sends_question_and_answer_to_gemini():
    fake = FakeGemini()
    make_grader(fake).grade(QUESTION, STRONG_ANSWER, KEYWORDS)

    request = fake.requests[0]
    assert request.method == "POST"
    assert request.url.host == "generativelanguage.googleapis.com"
    assert "generateContent" in request.url.path
    sent = request.content.decode()
    assert QUESTION in sent
    assert json.dumps(STRONG_ANSWER)[1:-1] in sent  # answer text, JSON-escaped


def test_request_has_a_timeout():
    fake = FakeGemini()
    make_grader(fake).grade(QUESTION, STRONG_ANSWER, KEYWORDS)

    timeout = fake.requests[0].extensions.get("timeout", {})
    assert timeout.get("read") is not None, "a Gemini call must never wait forever"


def test_reply_wrapped_in_markdown_code_fence_is_accepted():
    fenced = "```json\n" + json.dumps(GOOD_VERDICT) + "\n```"
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(FakeGemini(body=gemini_body(fenced))))

    assert result.grader == "ai"
    assert result.score == GOOD_VERDICT["score"]


# --- fallback to keyword grading ----------------------------------------------

@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 502, 503, 504])
def test_http_error_falls_back_to_keyword_grading(status):
    fake = FakeGemini(status=status, body={"error": {"code": status, "message": "nope"}})
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(fake))

    assert len(fake.requests) >= 1
    assert_keyword_fallback(result)


@pytest.mark.parametrize("exc", [
    httpx.ConnectTimeout("connect timed out"),
    httpx.ReadTimeout("read timed out"),
    httpx.WriteTimeout("write timed out"),
    httpx.PoolTimeout("pool timed out"),
    httpx.ConnectError("connection refused"),
    httpx.RemoteProtocolError("server hung up"),
    RuntimeError("unexpected"),
], ids=lambda e: type(e).__name__)
def test_exception_or_timeout_falls_back_to_keyword_grading(exc):
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(FakeGemini(raises=exc)))

    assert_keyword_fallback(result)


@pytest.mark.parametrize("body", [
    b"<html>Bad Gateway</html>",                               # not JSON at all
    {},                                                        # no candidates
    {"candidates": []},                                        # empty candidates
    {"promptFeedback": {"blockReason": "SAFETY"}},             # prompt blocked
    gemini_body("Great answer, 9/10!"),                        # text is not JSON
    gemini_body({"correct": True, "reasons": []}),             # score missing
    gemini_body({**GOOD_VERDICT, "score": 150}),               # score above 100
    gemini_body({**GOOD_VERDICT, "score": -5}),                # score below 0
    gemini_body({**GOOD_VERDICT, "score": "ninety"}),          # score not a number
], ids=["html", "empty", "no-candidates", "blocked", "prose", "no-score",
        "score-high", "score-low", "score-text"])
def test_unusable_reply_falls_back_to_keyword_grading(body):
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(FakeGemini(body=body)))

    assert_keyword_fallback(result)


def test_missing_api_key_uses_keyword_grading_without_calling_gemini():
    fake = FakeGemini()
    result = grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=make_grader(fake, api_key=""))

    assert fake.requests == []
    assert_keyword_fallback(result)


def test_no_gemini_grader_uses_keyword_grading():
    assert_keyword_fallback(grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS, gemini=None))


def test_fallback_keeps_keyword_rules_for_blank_answer():
    fake = FakeGemini(status=503)
    result = grade_answer(QUESTION, "   ", KEYWORDS, gemini=make_grader(fake))

    assert_keyword_fallback(result, answer="   ")
    assert result.score == 0
    assert result.correct is False


def test_fallback_uses_the_keyword_evaluator_passed_in():
    strict = KeywordEvaluator(threshold=100)
    result = grade_answer(QUESTION, "A stack is LIFO.", KEYWORDS,
                          gemini=make_grader(FakeGemini(status=500)), keyword=strict)

    assert result.grader == "keyword"
    assert result.score == 50
    assert result.correct is False  # strict threshold, not the default 50


# --- both graders fail --------------------------------------------------------

@pytest.mark.parametrize("fake", [
    FakeGemini(status=500),
    FakeGemini(raises=httpx.ReadTimeout("read timed out")),
], ids=["http-500", "timeout"])
def test_clear_error_when_gemini_and_keyword_grading_both_fail(fake):
    with pytest.raises(GradingError) as info:
        grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS,
                     gemini=make_grader(fake), keyword=BrokenKeywordEvaluator())

    message = str(info.value)
    assert "Gemini" in message
    assert "keyword" in message.lower()
    assert info.value.__cause__ is not None  # keeps the underlying error for the logs


def test_api_key_is_not_leaked_in_the_error_message():
    fake = FakeGemini(status=401)
    with pytest.raises(GradingError) as info:
        grade_answer(QUESTION, STRONG_ANSWER, KEYWORDS,
                     gemini=make_grader(fake, api_key="secret-key-123"), keyword=BrokenKeywordEvaluator())

    assert "secret-key-123" not in str(info.value)


# --- live Gemini (manual, needs GEMINI_API_KEY) -------------------------------

live = pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")


@pytest.fixture
def live_grader():
    return GeminiGrader(api_key=os.environ["GEMINI_API_KEY"])


@live
def test_live_gemini_returns_valid_result(live_grader):
    result = live_grader.grade(QUESTION, STRONG_ANSWER, KEYWORDS)

    assert result.grader == "ai"
    assert isinstance(result.score, int) and 0 <= result.score <= 100
    assert isinstance(result.correct, bool)


@live
def test_live_gemini_ranks_strong_answer_above_weak_answer(live_grader):
    strong = live_grader.grade(QUESTION, STRONG_ANSWER, KEYWORDS)
    weak = live_grader.grade(QUESTION, WEAK_ANSWER, KEYWORDS)

    assert strong.correct is True
    assert weak.correct is False
    assert strong.score > weak.score


@live
def test_live_gemini_credits_answer_without_exact_keywords(live_grader):
    # The point of AI grading: a correct answer in other words should still pass.
    paraphrase = ("Items come off in reverse order of arrival: you place each new item on the top "
                  "and always take from the top, so the newest one leaves first.")
    result = live_grader.grade(QUESTION, paraphrase, KEYWORDS)

    assert result.correct is True
    assert result.score > keyword_result(paraphrase).score
