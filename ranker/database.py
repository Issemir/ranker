"""Database and user management for the ranker application."""

import sqlite3
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from werkzeug.security import generate_password_hash, check_password_hash


class Database:
    """Manages user accounts and ranking history."""

    def __init__(self, db_path: str = "data/ranker.db"):
        """Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rankings history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_name TEXT,
                items TEXT NOT NULL,
                rounds INTEGER NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def user_exists(self, email: str) -> bool:
        """Check if user exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def create_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Create a new user.
        
        Args:
            email: User email
            password: User password (will be hashed)
            
        Returns:
            Tuple of (success, message)
        """
        if self.user_exists(email):
            return False, "Email already registered"

        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            return True, "Account created successfully"
        except Exception as e:
            return False, f"Error creating account: {str(e)}"
        finally:
            conn.close()

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[int]]:
        """Authenticate user.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (authenticated, user_id)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            return True, user["id"]
        return False, None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def get_all_users(self) -> List[Dict]:
        """Get all users with their info."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY email")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users

    def save_ranking(
        self,
        user_id: int,
        items: List[str],
        rounds: int,
        results: List[Tuple[str, float]],
        session_name: Optional[str] = None
    ) -> bool:
        """Save a completed ranking to history.
        
        Args:
            user_id: User ID
            items: List of items that were ranked
            rounds: Number of rounds
            results: List of (name, score) tuples
            session_name: Optional name for this ranking session
            
        Returns:
            True if successful
        """
        import json
        
        conn = self.get_connection()
        cursor = conn.cursor()

        items_json = json.dumps(items)
        results_json = json.dumps(results)

        try:
            cursor.execute(
                """INSERT INTO rankings (user_id, session_name, items, rounds, results)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, session_name, items_json, rounds, results_json)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving ranking: {e}")
            return False
        finally:
            conn.close()

    def get_user_rankings(self, user_id: int) -> List[Dict]:
        """Get all rankings for a user.

        Args:
            user_id: User ID

        Returns:
            List of ranking history dictionaries
        """
        import json

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, session_name, items, rounds, results, created_at
               FROM rankings WHERE user_id = ? ORDER BY created_at DESC""",
            (user_id,)
        )
        rankings = []
        for row in cursor.fetchall():
            rankings.append({
                "id": row["id"],
                "session_name": row["session_name"],
                "items": json.loads(row["items"]),
                "rounds": row["rounds"],
                "results": json.loads(row["results"]),
                "created_at": row["created_at"]
            })
        conn.close()
        return rankings

    def get_user_rankings_public(self, user_id: int) -> List[Dict]:
        """Get all public rankings for a user.

        Args:
            user_id: User ID

        Returns:
            List of ranking dictionaries
        """
        import json

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, session_name, items, rounds, results, created_at, user_id
               FROM rankings WHERE user_id = ? ORDER BY created_at DESC""",
            (user_id,)
        )
        rankings = []
        for row in cursor.fetchall():
            rankings.append({
                "id": row["id"],
                "session_name": row["session_name"],
                "items": json.loads(row["items"]),
                "rounds": row["rounds"],
                "results": json.loads(row["results"]),
                "created_at": row["created_at"]
            })
        conn.close()
        return rankings

    def get_ranking_by_id(self, ranking_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific ranking by ID (verify user ownership)."""
        import json

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, session_name, items, rounds, results, created_at
               FROM rankings WHERE id = ? AND user_id = ?""",
            (ranking_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row["id"],
            "session_name": row["session_name"],
            "items": json.loads(row["items"]),
            "rounds": row["rounds"],
            "results": json.loads(row["results"]),
            "created_at": row["created_at"]
        }

    def get_ranking_by_id_public(self, ranking_id: int) -> Optional[Dict]:
        """Get a specific ranking by ID (public, no ownership check). Includes owner info."""
        import json

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.id, r.session_name, r.items, r.rounds, r.results, r.created_at, r.user_id, u.email
               FROM rankings r
               JOIN users u ON r.user_id = u.id
               WHERE r.id = ?""",
            (ranking_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row["id"],
            "session_name": row["session_name"],
            "items": json.loads(row["items"]),
            "rounds": row["rounds"],
            "results": json.loads(row["results"]),
            "created_at": row["created_at"],
            "owner_id": row["user_id"],
            "owner_email": row["email"]
        }
