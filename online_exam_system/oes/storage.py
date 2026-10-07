"""JSON based persistence and repositories."""
from __future__ import annotations

import json
import os
import tempfile
from typing import List, Optional

from .models import Exam, Result


class StorageError(Exception):
    """Raised when the data file cannot be read."""


class JsonStore:
    """Very small key-value store backed by one JSON file."""

    def __init__(self, path: str) -> None:
        self.path = path

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise StorageError(f"Corrupted data file: {self.path}") from exc

    def read(self, key: str, default=None):
        return self._load().get(key, default)

    def write(self, key: str, value) -> None:
        data = self._load()
        data[key] = value
        folder = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(folder, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        os.replace(tmp_path, self.path)


class ExamRepository:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def all(self) -> List[Exam]:
        return [Exam.from_dict(e) for e in self.store.read("exams", [])]

    def get(self, exam_id: str) -> Optional[Exam]:
        return next((e for e in self.all() if e.exam_id == exam_id), None)

    def save(self, exam: Exam) -> None:
        exams = [e for e in self.all() if e.exam_id != exam.exam_id]
        exams.append(exam)
        self.store.write("exams", [e.to_dict() for e in exams])

    def delete(self, exam_id: str) -> bool:
        exams = self.all()
        remaining = [e for e in exams if e.exam_id != exam_id]
        self.store.write("exams", [e.to_dict() for e in remaining])
        return len(remaining) < len(exams)


class ResultRepository:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def all(self) -> List[Result]:
        return [Result.from_dict(r) for r in self.store.read("results", [])]

    def add(self, result: Result) -> None:
        items = self.store.read("results", [])
        items.append(result.to_dict())
        self.store.write("results", items)

    def for_user(self, username: str) -> List[Result]:
        return [r for r in self.all() if r.username == username]

    def for_exam(self, exam_id: str) -> List[Result]:
        return [r for r in self.all() if r.exam_id == exam_id]
