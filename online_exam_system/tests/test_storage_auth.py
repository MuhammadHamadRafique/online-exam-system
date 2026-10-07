import pytest

from oes.auth import (MAX_ATTEMPTS, AuthError, AuthService, hash_password,
                      password_problems, verify_password)
from oes.models import Exam, Question, Result
from oes.storage import ExamRepository, JsonStore, ResultRepository, StorageError


@pytest.fixture
def store(tmp_path):
    return JsonStore(str(tmp_path / "db.json"))


def test_store_read_write(store):
    assert store.read("x", "default") == "default"
    store.write("x", [1, 2])
    assert store.read("x") == [1, 2]


def test_store_corrupted_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    with pytest.raises(StorageError):
        JsonStore(str(path)).read("x")


def test_exam_repository(store):
    repo = ExamRepository(store)
    exam = Exam("T", "S")
    exam.add_question(Question("q", "short", "a"))
    repo.save(exam)
    repo.save(exam)
    assert len(repo.all()) == 1
    assert repo.get(exam.exam_id).title == "T"
    assert repo.get("missing") is None
    assert repo.delete(exam.exam_id)
    assert not repo.delete(exam.exam_id)


def test_result_repository(store):
    repo = ResultRepository(store)
    repo.add(Result("ali", "e1", "T", 1, 2, 1, 1, 0, True, 5))
    repo.add(Result("sara", "e2", "T", 2, 2, 2, 0, 0, True, 5))
    assert len(repo.all()) == 2
    assert len(repo.for_user("ali")) == 1
    assert len(repo.for_exam("e2")) == 1


def test_password_hashing():
    digest, salt = hash_password("Secret123")
    assert verify_password("Secret123", digest, salt)
    assert not verify_password("secret123", digest, salt)


def test_password_problems():
    assert password_problems("Strong123") == []
    assert len(password_problems("abc")) == 3


def test_register_and_login(store):
    auth = AuthService(store)
    auth.register("Ali_01", "Strong123")
    assert auth.login("ali_01", "Strong123").role == "student"


@pytest.mark.parametrize("name,password,role", [
    ("a", "Strong123", "student"),
    ("ali", "weak", "student"),
    ("ali", "Strong123", "boss"),
])
def test_register_rejects_bad_input(store, name, password, role):
    with pytest.raises(AuthError):
        AuthService(store).register(name, password, role)


def test_register_duplicate(store):
    auth = AuthService(store)
    auth.register("ali", "Strong123")
    with pytest.raises(AuthError):
        auth.register("ali", "Strong123")


def test_login_failures_and_lockout(store):
    auth = AuthService(store)
    auth.register("ali", "Strong123")
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(AuthError):
            auth.login("ali", "wrong")
    with pytest.raises(AuthError, match="locked"):
        auth.login("ali", "Strong123")


def test_login_unknown_user(store):
    with pytest.raises(AuthError):
        AuthService(store).login("ghost", "Strong123")
