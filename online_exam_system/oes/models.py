"""Domain models for the Online Examination System."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

QUESTION_TYPES = ("mcq", "true_false", "short")
DIFFICULTIES = ("easy", "medium", "hard")
ROLES = ("student", "admin")


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class Question:
    """A single exam question (MCQ, True/False or short answer)."""

    text: str
    qtype: str
    answer: str
    options: List[str] = field(default_factory=list)
    marks: int = 1
    difficulty: str = "medium"
    qid: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Question text cannot be empty")
        if self.qtype not in QUESTION_TYPES:
            raise ValueError(f"Unknown question type: {self.qtype}")
        if self.difficulty not in DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {self.difficulty}")
        if self.marks <= 0:
            raise ValueError("Marks must be positive")
        if self.qtype == "true_false":
            self.options = ["True", "False"]
            self.answer = self.answer.strip().capitalize()
        if self.qtype == "mcq" and len(self.options) < 2:
            raise ValueError("MCQ needs at least two options")
        if self.qtype in ("mcq", "true_false") and self.answer not in self.options:
            raise ValueError("Answer must be one of the options")

    def is_correct(self, response: Optional[str]) -> bool:
        """Case-insensitive comparison of a response with the answer."""
        if response is None:
            return False
        return str(response).strip().lower() == self.answer.strip().lower()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        return cls(**data)


@dataclass
class Exam:
    """An exam made of questions with timing and grading rules."""

    title: str
    subject: str
    duration_minutes: int = 30
    pass_percentage: float = 50.0
    negative_marking: float = 0.0
    questions: List[Question] = field(default_factory=list)
    exam_id: str = field(default_factory=_new_id)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Exam title cannot be empty")
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        if not 0 <= self.pass_percentage <= 100:
            raise ValueError("Pass percentage must be between 0 and 100")
        if not 0 <= self.negative_marking <= 1:
            raise ValueError("Negative marking must be between 0 and 1")

    @property
    def total_marks(self) -> int:
        return sum(q.marks for q in self.questions)

    def is_ready(self) -> bool:
        return len(self.questions) > 0

    def add_question(self, question: Question) -> None:
        if any(q.text.lower() == question.text.lower() for q in self.questions):
            raise ValueError("Duplicate question")
        self.questions.append(question)

    def remove_question(self, qid: str) -> bool:
        before = len(self.questions)
        self.questions = [q for q in self.questions if q.qid != qid]
        return len(self.questions) < before

    def get_question(self, qid: str) -> Optional[Question]:
        return next((q for q in self.questions if q.qid == qid), None)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Exam":
        payload = dict(data)
        payload["questions"] = [Question.from_dict(q) for q in payload.get("questions", [])]
        return cls(**payload)


@dataclass
class User:
    """A registered user (student or admin)."""

    username: str
    password_hash: str
    salt: str
    role: str = "student"

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"Unknown role: {self.role}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(**data)


@dataclass
class Result:
    """Outcome of one exam attempt."""

    username: str
    exam_id: str
    exam_title: str
    score: float
    total: int
    correct: int
    wrong: int
    skipped: int
    passed: bool
    time_taken: float
    responses: Dict[str, str] = field(default_factory=dict)
    submitted_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def percentage(self) -> float:
        return round(self.score / self.total * 100, 2) if self.total else 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Result":
        return cls(**data)
