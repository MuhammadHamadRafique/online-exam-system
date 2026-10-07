from oes.analytics import format_report, grade_for, leaderboard, question_difficulty, summarize
from oes.models import Exam, Question, Result


def res(user, score, total=10, passed=True, t=10.0, responses=None):
    return Result(user, "e", "T", score, total, 0, 0, 0, passed, t, responses or {})


def test_grades():
    assert [grade_for(p) for p in (90, 75, 65, 55, 10)] == ["A", "B", "C", "D", "F"]


def test_summarize_empty_and_values():
    assert summarize([])["attempts"] == 0
    s = summarize([res("a", 9), res("b", 5), res("c", 2, passed=False)])
    assert s["highest"] == 90 and s["lowest"] == 20
    assert s["average"] == 53.33 and s["median"] == 50
    assert s["pass_rate"] == 66.67


def test_leaderboard_best_attempt_and_ranking():
    rows = leaderboard([res("a", 5), res("a", 8), res("b", 8, t=5.0), res("c", 3)], top=2)
    assert [r["username"] for r in rows] == ["b", "a"]
    assert rows[0]["rank"] == 1 and rows[1]["grade"] == "B"


def test_leaderboard_keeps_better_when_later_is_worse():
    rows = leaderboard([res("a", 8), res("a", 3)])
    assert rows[0]["percentage"] == 80.0


def test_question_difficulty_and_report():
    exam = Exam("T", "S")
    q1 = Question("easyq", "short", "a")
    q2 = Question("hardq", "short", "b")
    q3 = Question("unseen", "short", "c")
    for q in (q1, q2, q3):
        exam.add_question(q)
    results = [
        res("a", 1, responses={q1.qid: "a", q2.qid: "x"}),
        res("b", 1, responses={q1.qid: "a", q2.qid: "x"}),
        res("c", 1, responses={q1.qid: "x", q2.qid: "b"}),
    ]
    labels = {i["text"]: i["label"] for i in question_difficulty(exam, results)}
    assert labels == {"easyq": "medium", "hardq": "hard", "unseen": "no data"}
    report = format_report(exam, results)
    assert "Attempts: 3" in report and "hardq" in report
