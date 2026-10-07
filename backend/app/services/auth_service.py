import os
import sqlite3
import hashlib
import secrets


class AuthService:
    def __init__(self):
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(current_file)
            )
        )
        self.db_path = os.path.join(project_root, "app", "data", "users.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer'
            )
            """
        )
        conn.commit()
        conn.close()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            100_000,
        ).hex()

    def user_exists(self, username: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        return row is not None

    def create_user(self, username: str, password: str, role: str = "customer"):
        if self.user_exists(username):
            raise ValueError("Username already exists")

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO users (username, salt, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, salt, password_hash, role),
        )
        conn.commit()
        conn.close()

    def verify_user(self, username: str, password: str):
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT salt, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        conn.close()

        if row is None:
            return None

        salt, stored_hash, role = row
        candidate_hash = self._hash_password(password, salt)
        if secrets.compare_digest(candidate_hash, stored_hash):
            return role
        return None

    def seed_default_admin(self, username: str = "admin", password: str = "admin123"):
        if not self.user_exists(username):
            self.create_user(username, password, role="admin")