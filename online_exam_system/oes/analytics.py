"""Statistics and reports computed from exam results."""
from __future__ import annotations

from statistics import median
from typing import Dict, List

from .models import Exam, Result


def grade_for(percentage: float) -> str:
    if percentage >= 85:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    return "F"


def summarize(results: List[Result]) -> Dict[str, float]:
    """Basic descriptive statistics for a list of results."""
    if not results:
        return {"attempts": 0, "average": 0.0, "highest": 0.0, "lowest": 0.0,
                "median": 0.0, "pass_rate": 0.0}
    percentages = [r.percentage for r in results]
    passed = sum(1 for r in results if r.passed)
    return {
        "attempts": len(results),
        "average": round(sum(percentages) / len(percentages), 2),
        "highest": max(percentages),
        "lowest": min(percentages),
        "median": median(percentages),
        "pass_rate": round(passed / len(results) * 100, 2),
    }


def leaderboard(results: List[Result], top: int = 5) -> List[Dict[str, object]]:
    """Best attempt per student, sorted by percentage then fastest time."""
    best: Dict[str, Result] = {}
    for result in results:
        current = best.get(result.username)
        if current is None or (result.percentage, -result.time_taken) > (
            current.percentage, -current.time_taken
        ):
            best[result.username] = result
    ranked = sorted(best.values(), key=lambda r: (-r.percentage, r.time_taken))
    return [
        {"rank": i + 1, "username": r.username, "percentage": r.percentage,
         "grade": grade_for(r.percentage)}
        for i, r in enumerate(ranked[:top])
    ]


def question_difficulty(exam: Exam, results: List[Result]) -> List[Dict[str, object]]:
    """Share of students who answered each question correctly."""
    stats = []
    for question in exam.questions:
        attempted = [r for r in results if question.qid in r.responses]
        if not attempted:
            stats.append({"qid": question.qid, "text": question.text,
                          "correct_ratio": None, "label": "no data"})
            continue
        right = sum(1 for r in attempted if question.is_correct(r.responses[question.qid]))
        ratio = round(right / len(attempted), 2)
        label = "hard" if ratio < 0.4 else "easy" if ratio > 0.75 else "medium"
        stats.append({"qid": question.qid, "text": question.text,
                      "correct_ratio": ratio, "label": label})
    return stats


def format_report(exam: Exam, results: List[Result]) -> str:
    summary = summarize(results)
    lines = [
        f"Report: {exam.title} ({exam.subject})",
        f"Attempts: {summary['attempts']}   Pass rate: {summary['pass_rate']}%",
        f"Average: {summary['average']}%   Highest: {summary['highest']}%   "
        f"Lowest: {summary['lowest']}%   Median: {summary['median']}%",
        "Question analysis:",
    ]
    for item in question_difficulty(exam, results):
        lines.append(f"  - [{item['label']}] {item['text']} (correct: {item['correct_ratio']})")
    return "\n".join(lines)
