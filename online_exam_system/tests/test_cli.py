from oes.cli import CLI
from oes.seed import seed_sample_data
from oes.storage import ExamRepository, JsonStore


def run_cli(tmp_path, inputs, seed=True):
    store = JsonStore(str(tmp_path / "db.json"))
    if seed:
        seed_sample_data(store)
    feed = iter(inputs)
    out = []
    CLI(store, input_fn=lambda _p: next(feed), output_fn=out.append).run()
    return "\n".join(out), store


def test_seed_is_idempotent(tmp_path):
    store = JsonStore(str(tmp_path / "db.json"))
    seed_sample_data(store)
    seed_sample_data(store)
    assert len(ExamRepository(store).all()) == 1


def test_invalid_menu_and_exit(tmp_path):
    out, _ = run_cli(tmp_path, ["9", "3"])
    assert "Invalid choice" in out and "Goodbye" in out


def test_register_login_failures(tmp_path):
    out, _ = run_cli(tmp_path, ["2", "ab", "x", "2", "bob", "weak", "1", "ghost", "pw", "3"])
    assert out.count("Registration failed") == 2 and "Login failed" in out


def test_student_flow_take_exam(tmp_path):
    inputs = ["2", "sara", "Strong123", "1", "sara", "Strong123",
              "1", "1", *["1"] * 5, "2", "3", "1", "9", "4", "3"]
    out, store = run_cli(tmp_path, inputs)
    assert "Account created for sara" in out and "Welcome, sara" in out
    assert "Score" in out and "#1 sara" in out
    assert len(store.read("results")) == 1


def test_student_empty_answers_and_no_attempts(tmp_path):
    inputs = ["2", "sara", "Strong123", "1", "sara", "Strong123",
              "2", "1", "1", *[""] * 5, "9", "4", "3"]
    out, _ = run_cli(tmp_path, inputs)
    assert "No attempts yet" in out and "FAILED" in out


def test_admin_creates_exam_and_question(tmp_path):
    inputs = ["1", "admin", "Admin1234",
              "1", "Quiz", "Math", "x", "5", "50",
              "3",
              "2", "2", "mcq", "1+1?", "1,2,3", "2", "2",
              "2", "2", "short", "1+1?", "2", "",
              "2", "2", "mcq", "bad", "a", "zzz", "",
              "2", "2", "mcq", "1+1?", "1,2", "2", "",
              "4", "2", "5", "9", "3", "3"]
    out, store = run_cli(tmp_path, inputs)
    assert "Exam 'Quiz' created" in out and "Question added" in out
    assert "Could not add question" in out and "Please enter a number" in out
    assert "Attempts: 0" in out
    assert any(e["title"] == "Quiz" for e in store.read("exams"))


def test_admin_invalid_exam_and_empty_exam(tmp_path):
    inputs = ["1", "admin", "Admin1234",
              "1", " ", "S", "", "",
              "7", "5", "3"]
    out, _ = run_cli(tmp_path, inputs)
    assert "Could not create exam" in out and "Invalid choice" in out


def test_admin_login_fails_without_seed(tmp_path):
    inputs = ["1", "admin", "Admin1234", "3", "5", "3"]
    out, _ = run_cli(tmp_path, inputs, seed=False)
    assert "Login failed" in out


def test_admin_list_exams_does_not_prompt(tmp_path):
    inputs = ["1", "admin", "Admin1234", "3", "5", "3"]
    out, _ = run_cli(tmp_path, inputs)
    assert "Python Basics" in out and "Select exam number" not in out
