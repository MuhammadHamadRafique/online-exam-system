"""Authentication: registration, password hashing and login."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
from typing import Dict, List, Optional, Tuple

from .models import ROLES, User
from .storage import JsonStore

MAX_ATTEMPTS = 3
ITERATIONS = 100_000


class AuthError(Exception):
    """Raised for registration or login failures."""


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Return (hash, salt) using PBKDF2-HMAC-SHA256."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


def password_problems(password: str) -> List[str]:
    """List the rules a password breaks (empty list means strong enough)."""
    problems = []
    if len(password) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"\d", password):
        problems.append("a digit")
    return problems


class AuthService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store
        self._failed: Dict[str, int] = {}

    def _users(self) -> Dict[str, User]:
        return {u["username"]: User.from_dict(u) for u in self.store.read("users", [])}

    def register(self, username: str, password: str, role: str = "student") -> User:
        username = username.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,20}", username):
            raise AuthError("Username must be 3-20 characters (letters, digits, underscore)")
        if role not in ROLES:
            raise AuthError("Invalid role")
        problems = password_problems(password)
        if problems:
            raise AuthError("Password needs " + ", ".join(problems))
        users = self._users()
        if username in users:
            raise AuthError("Username already taken")
        password_hash, salt = hash_password(password)
        user = User(username, password_hash, salt, role)
        users[username] = user
        self.store.write("users", [u.to_dict() for u in users.values()])
        return user

    def login(self, username: str, password: str) -> User:
        username = username.strip().lower()
        if self._failed.get(username, 0) >= MAX_ATTEMPTS:
            raise AuthError("Account locked after too many failed attempts")
        user = self._users().get(username)
        if user is None or not verify_password(password, user.password_hash, user.salt):
            self._failed[username] = self._failed.get(username, 0) + 1
            raise AuthError("Invalid username or password")
        self._failed.pop(username, None)
        return user
