"""Exam session: timing, answering and scoring."""
from __future__ import annotations

import random
import time
from typing import Callable, Dict, List, Optional, Tuple

from .models import Exam, Question, Result


class ExamError(Exception):
    """Raised for invalid exam-session operations."""


def score_responses(exam: Exam, responses: Dict[str, str]) -> Tuple[float, int, int, int]:
    """Return (score, correct, wrong, skipped) applying negative marking."""
    score = 0.0
    correct = wrong = skipped = 0
    for question in exam.questions:
        response = responses.get(question.qid)
        if response is None or not str(response).strip():
            skipped += 1
        elif question.is_correct(response):
            correct += 1
            score += question.marks
        else:
            wrong += 1
            if question.qtype != "short":
                score -= question.marks * exam.negative_marking
    return max(0.0, round(score, 2)), correct, wrong, skipped


class ExamSession:
    """One student's attempt at one exam."""

    def __init__(
        self,
        exam: Exam,
        username: str,
        shuffle: bool = True,
        rng: Optional[random.Random] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not exam.is_ready():
            raise ExamError("This exam has no questions yet")
        self.exam = exam
        self.username = username
        self.clock = clock
        self.questions: List[Question] = list(exam.questions)
        if shuffle:
            (rng or random.Random()).shuffle(self.questions)
        self.responses: Dict[str, str] = {}
        self.started_at: Optional[float] = None
        self.finished = False

    def start(self) -> None:
        if self.started_at is not None:
            raise ExamError("Exam already started")
        self.started_at = self.clock()

    def time_remaining(self) -> float:
        if self.started_at is None:
            raise ExamError("Exam not started")
        deadline = self.started_at + self.exam.duration_minutes * 60
        return max(0.0, deadline - self.clock())

    def is_expired(self) -> bool:
        return self.time_remaining() <= 0

    def answer(self, qid: str, response: str) -> None:
        if self.finished:
            raise ExamError("Exam already submitted")
        if self.is_expired():
            raise ExamError("Time is over")
        if self.exam.get_question(qid) is None:
            raise ExamError("Unknown question")
        self.responses[qid] = response

    def unanswered(self) -> List[Question]:
        return [q for q in self.questions if q.qid not in self.responses]

    def progress(self) -> Tuple[int, int]:
        return len(self.responses), len(self.questions)

    def submit(self) -> Result:
        if self.finished:
            raise ExamError("Exam already submitted")
        if self.started_at is None:
            raise ExamError("Exam not started")
        self.finished = True
        score, correct, wrong, skipped = score_responses(self.exam, self.responses)
        total = self.exam.total_marks
        elapsed = min(self.clock() - self.started_at, self.exam.duration_minutes * 60)
        percentage = score / total * 100 if total else 0.0
        return Result(
            username=self.username,
            exam_id=self.exam.exam_id,
            exam_title=self.exam.title,
            score=score,
            total=total,
            correct=correct,
            wrong=wrong,
            skipped=skipped,
            passed=percentage >= self.exam.pass_percentage,
            time_taken=round(elapsed, 1),
            responses=dict(self.responses),
        )
