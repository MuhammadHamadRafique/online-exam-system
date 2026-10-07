"""Sample data so the application can be demonstrated immediately."""
from __future__ import annotations

from .auth import AuthError, AuthService
from .models import Exam, Question
from .storage import ExamRepository, JsonStore


def seed_sample_data(store: JsonStore) -> None:
    """Create a default admin and one sample exam (only if missing)."""
    try:
        AuthService(store).register("admin", "Admin1234", role="admin")
    except AuthError:
        pass
    repo = ExamRepository(store)
    if repo.all():
        return
    exam = Exam("Python Basics", "Programming", duration_minutes=10,
                pass_percentage=50, negative_marking=0.25)
    exam.add_question(Question("Which keyword defines a function in Python?", "mcq", "def",
                               options=["func", "def", "lambda", "function"], difficulty="easy"))
    exam.add_question(Question("Python lists are immutable.", "true_false", "False",
                               difficulty="easy"))
    exam.add_question(Question("What is the output of len('exam')?", "short", "4", marks=2))
    exam.add_question(Question("Which data type stores key-value pairs?", "mcq", "dict",
                               options=["list", "tuple", "dict", "set"], marks=2))
    exam.add_question(Question("Which keyword handles exceptions?", "short", "except",
                               marks=2, difficulty="hard"))
    repo.save(exam)
