import pytest

from oes.models import Exam, Question, Result, User


def make_mcq(text="2+2?"):
    return Question(text, "mcq", "4", options=["3", "4", "5"])


def test_mcq_valid_and_correct():
    q = make_mcq()
    assert q.is_correct(" 4 ")
    assert not q.is_correct("5")
    assert not q.is_correct(None)


def test_true_false_normalised():
    q = Question("Sky is blue", "true_false", "true")
    assert q.options == ["True", "False"]
    assert q.answer == "True"


@pytest.mark.parametrize("kwargs", [
    dict(text=" ", qtype="short", answer="x"),
    dict(text="q", qtype="essay", answer="x"),
    dict(text="q", qtype="short", answer="x", difficulty="insane"),
    dict(text="q", qtype="short", answer="x", marks=0),
    dict(text="q", qtype="mcq", answer="a", options=["a"]),
    dict(text="q", qtype="mcq", answer="z", options=["a", "b"]),
])
def test_question_validation(kwargs):
    with pytest.raises(ValueError):
        Question(**kwargs)


def test_question_roundtrip():
    q = make_mcq()
    assert Question.from_dict(q.to_dict()) == q


def test_exam_add_remove_total():
    exam = Exam("T", "S")
    assert not exam.is_ready()
    q = make_mcq()
    exam.add_question(q)
    assert exam.is_ready() and exam.total_marks == 1
    assert exam.get_question(q.qid) is q
    assert exam.remove_question(q.qid)
    assert not exam.remove_question("nope")
    assert exam.get_question(q.qid) is None


def test_exam_duplicate_question():
    exam = Exam("T", "S")
    exam.add_question(make_mcq("Same"))
    with pytest.raises(ValueError):
        exam.add_question(make_mcq("same"))


@pytest.mark.parametrize("kwargs", [
    dict(title=" ", subject="s"),
    dict(title="t", subject="s", duration_minutes=0),
    dict(title="t", subject="s", pass_percentage=101),
    dict(title="t", subject="s", negative_marking=2),
])
def test_exam_validation(kwargs):
    with pytest.raises(ValueError):
        Exam(**kwargs)


def test_exam_roundtrip():
    exam = Exam("T", "S")
    exam.add_question(make_mcq())
    assert Exam.from_dict(exam.to_dict()).questions[0].text == "2+2?"


def test_user_role_validation_and_roundtrip():
    user = User("ali", "h", "s")
    assert User.from_dict(user.to_dict()) == user
    with pytest.raises(ValueError):
        User("ali", "h", "s", role="hacker")


def test_result_percentage():
    r = Result("a", "e", "T", 3, 4, 3, 1, 0, True, 10.0)
    assert r.percentage == 75.0
    assert Result.from_dict(r.to_dict()) == r
    assert Result("a", "e", "T", 0, 0, 0, 0, 0, False, 0).percentage == 0.0
