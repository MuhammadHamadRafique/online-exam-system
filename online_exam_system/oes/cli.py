"""Menu-driven command line interface."""
from __future__ import annotations

from typing import Callable, Optional

from .analytics import format_report, grade_for, leaderboard
from .auth import AuthError, AuthService
from .exam import ExamError, ExamSession
from .models import Exam, Question, User
from .storage import ExamRepository, JsonStore, ResultRepository


class CLI:
    def __init__(self, store: JsonStore, input_fn: Callable[[str], str] = input,
                 output_fn: Callable[[str], None] = print) -> None:
        self.auth = AuthService(store)
        self.exams = ExamRepository(store)
        self.results = ResultRepository(store)
        self._in = input_fn
        self._out = output_fn

    # ---- helpers -------------------------------------------------
    def ask(self, prompt: str) -> str:
        return self._in(prompt).strip()

    def ask_int(self, prompt: str, default: Optional[int] = None) -> int:
        while True:
            raw = self.ask(prompt)
            if raw == "" and default is not None:
                return default
            try:
                return int(raw)
            except ValueError:
                self._out("Please enter a number.")

    def _list_exams(self) -> list:
        exams = self.exams.all()
        if not exams:
            self._out("No exams available.")
        for index, exam in enumerate(exams, start=1):
            self._out(f"{index}. {exam.title} [{exam.subject}] - "
                      f"{len(exam.questions)} questions, {exam.total_marks} marks")
        return exams

    def _pick_exam(self) -> Optional[Exam]:
        exams = self._list_exams()
        if not exams:
            return None
        choice = self.ask_int("Select exam number: ")
        if 1 <= choice <= len(exams):
            return exams[choice - 1]
        self._out("Invalid exam number.")
        return None

    # ---- main loop -----------------------------------------------
    def run(self) -> None:
        self._out("=== Online Examination System ===")
        while True:
            choice = self.ask("1) Login  2) Register  3) Exit : ")
            if choice == "1":
                user = self._login()
                if user:
                    self._dashboard(user)
            elif choice == "2":
                self._register()
            elif choice == "3":
                self._out("Goodbye!")
                return
            else:
                self._out("Invalid choice.")

    def _login(self) -> Optional[User]:
        try:
            user = self.auth.login(self.ask("Username: "), self.ask("Password: "))
        except AuthError as exc:
            self._out(f"Login failed: {exc}")
            return None
        self._out(f"Welcome, {user.username}!")
        return user

    def _register(self) -> None:
        try:
            user = self.auth.register(self.ask("Choose username: "), self.ask("Choose password: "))
        except AuthError as exc:
            self._out(f"Registration failed: {exc}")
            return
        self._out(f"Account created for {user.username}.")

    def _dashboard(self, user: User) -> None:
        if user.role == "admin":
            self._admin_menu()
        else:
            self._student_menu(user)

    # ---- admin ---------------------------------------------------
    def _admin_menu(self) -> None:
        while True:
            choice = self.ask("Admin: 1) Create exam 2) Add question 3) List exams "
                              "4) Exam report 5) Logout : ")
            if choice == "1":
                self._create_exam()
            elif choice == "2":
                self._add_question()
            elif choice == "3":
                self._list_exams()
            elif choice == "4":
                self._exam_report()
            elif choice == "5":
                return
            else:
                self._out("Invalid choice.")

    def _create_exam(self) -> None:
        title = self.ask("Title: ")
        subject = self.ask("Subject: ")
        duration = self.ask_int("Duration in minutes [30]: ", 30)
        pass_pct = self.ask_int("Pass percentage [50]: ", 50)
        try:
            exam = Exam(title, subject, duration, pass_pct)
        except ValueError as exc:
            self._out(f"Could not create exam: {exc}")
            return
        self.exams.save(exam)
        self._out(f"Exam '{exam.title}' created.")

    def _add_question(self) -> None:
        exam = self._pick_exam()
        if exam is None:
            return
        qtype = self.ask("Type (mcq/true_false/short): ")
        text = self.ask("Question: ")
        options = []
        if qtype == "mcq":
            options = [o.strip() for o in self.ask("Options (comma separated): ").split(",")]
        answer = self.ask("Correct answer: ")
        marks = self.ask_int("Marks [1]: ", 1)
        try:
            exam.add_question(Question(text, qtype, answer, options, marks))
        except ValueError as exc:
            self._out(f"Could not add question: {exc}")
            return
        self.exams.save(exam)
        self._out("Question added.")

    def _exam_report(self) -> None:
        exam = self._pick_exam()
        if exam:
            self._out(format_report(exam, self.results.for_exam(exam.exam_id)))

    # ---- student -------------------------------------------------
    def _student_menu(self, user: User) -> None:
        while True:
            choice = self.ask("Student: 1) Take exam 2) My results 3) Leaderboard 4) Logout : ")
            if choice == "1":
                self._take_exam(user)
            elif choice == "2":
                self._my_results(user)
            elif choice == "3":
                self._leaderboard()
            elif choice == "4":
                return
            else:
                self._out("Invalid choice.")

    def _take_exam(self, user: User) -> None:
        exam = self._pick_exam()
        if exam is None:
            return
        try:
            session = ExamSession(exam, user.username)
        except ExamError as exc:
            self._out(str(exc))
            return
        session.start()
        for number, question in enumerate(session.questions, start=1):
            if session.is_expired():
                self._out("Time is over - submitting.")
                break
            self._out(f"Q{number}. {question.text} ({question.marks} marks)")
            for index, option in enumerate(question.options, start=1):
                self._out(f"   {index}) {option}")
            response = self.ask("Your answer (blank to skip): ")
            if response.isdigit() and 1 <= int(response) <= len(question.options):
                response = question.options[int(response) - 1]
            if response:
                session.answer(question.qid, response)
        result = session.submit()
        self.results.add(result)
        status = "PASSED" if result.passed else "FAILED"
        self._out(f"Score {result.score}/{result.total} ({result.percentage}%) "
                  f"Grade {grade_for(result.percentage)} - {status}")

    def _my_results(self, user: User) -> None:
        results = self.results.for_user(user.username)
        if not results:
            self._out("No attempts yet.")
        for result in results:
            self._out(f"{result.exam_title}: {result.percentage}% "
                      f"({'pass' if result.passed else 'fail'}) on {result.submitted_at}")

    def _leaderboard(self) -> None:
        exam = self._pick_exam()
        if exam is None:
            return
        for row in leaderboard(self.results.for_exam(exam.exam_id)):
            self._out(f"#{row['rank']} {row['username']} - {row['percentage']}% ({row['grade']})")
