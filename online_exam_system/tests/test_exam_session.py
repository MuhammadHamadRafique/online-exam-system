import random

import pytest

from oes.exam import ExamError, ExamSession, score_responses
from oes.models import Exam, Question


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def exam():
    e = Exam("T", "S", duration_minutes=1, pass_percentage=50, negative_marking=0.5)
    e.add_question(Question("a?", "mcq", "x", options=["x", "y"], marks=2))
    e.add_question(Question("b?", "true_false", "true", marks=2))
    e.add_question(Question("c?", "short", "z", marks=1))
    return e


def test_scoring_with_negative_marking(exam):
    qa, qb, qc = exam.questions
    responses = {qa.qid: "x", qb.qid: "False", qc.qid: "no"}
    score, correct, wrong, skipped = score_responses(exam, responses)
    assert (score, correct, wrong, skipped) == (1.0, 1, 2, 0)


def test_scoring_skipped_and_floor(exam):
    qa, qb, _ = exam.questions
    assert score_responses(exam, {})[3] == 3
    score, *_ = score_responses(exam, {qa.qid: "y", qb.qid: "False"})
    assert score == 0.0


def test_session_requires_questions():
    with pytest.raises(ExamError):
        ExamSession(Exam("T", "S"), "ali")


def test_full_session_pass(exam):
    clock = FakeClock()
    s = ExamSession(exam, "ali", rng=random.Random(1), clock=clock)
    s.start()
    clock.now += 30
    for q in exam.questions:
        s.answer(q.qid, q.answer)
    assert s.progress() == (3, 3) and s.unanswered() == []
    result = s.submit()
    assert result.passed and result.percentage == 100.0 and result.time_taken == 30


def test_no_shuffle_keeps_order(exam):
    s = ExamSession(exam, "ali", shuffle=False)
    assert s.questions == exam.questions


def test_cannot_start_twice_or_before_start(exam):
    s = ExamSession(exam, "ali")
    with pytest.raises(ExamError):
        s.time_remaining()
    with pytest.raises(ExamError):
        s.submit()
    s.start()
    with pytest.raises(ExamError):
        s.start()


def test_timeout_blocks_answers(exam):
    clock = FakeClock()
    s = ExamSession(exam, "ali", clock=clock)
    s.start()
    clock.now += 61
    assert s.is_expired()
    with pytest.raises(ExamError, match="Time"):
        s.answer(exam.questions[0].qid, "x")
    assert s.submit().time_taken == 60


def test_answer_validation_and_double_submit(exam):
    s = ExamSession(exam, "ali")
    s.start()
    with pytest.raises(ExamError):
        s.answer("bogus", "x")
    s.submit()
    with pytest.raises(ExamError):
        s.submit()
    with pytest.raises(ExamError):
        s.answer(exam.questions[0].qid, "x")
