"""SQLite persistence for local tickets."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import subprocess


STATUSES = frozenset({"open", "closed", "cancelled", "active"})
COMMIT_TYPES = frozenset({"build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test"})


@dataclass(frozen=True)
class Ticket:
    """Represent a locally stored ticket."""

    id: int
    type: str
    title: str
    description: str
    status: str
    tags: tuple[str, ...]
    updated_at: str


@dataclass(frozen=True)
class Comment:
    """Represent a comment attached to a ticket."""

    id: int
    ticket_id: int
    author: str
    body: str
    created_at: str


class TicketStore:
    """Persist and query repository-local tickets in SQLite."""

    def __init__(self, repository_root: Path) -> None:
        """Initialize the store using the repository's local database path."""
        self.repository_root = repository_root
        self.database_path = repository_root / ".simple-project.db"

    def initialize(self) -> None:
        """Create the ticket database schema when it does not already exist."""
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL DEFAULT 'chore' CHECK(type IN ('build', 'chore', 'ci', 'docs', 'feat', 'fix', 'perf', 'refactor', 'revert', 'style', 'test')),
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('open', 'closed', 'cancelled', 'active')),
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
                    author TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_ticket
                ON tickets(status) WHERE status = 'active';
                """
            )
            columns = {column[1] for column in connection.execute("PRAGMA table_info(tickets)")}
            if "type" not in columns:
                connection.execute("ALTER TABLE tickets ADD COLUMN type TEXT NOT NULL DEFAULT 'chore'")

    def create_ticket(self, title: str, description: str, ticket_type: str, status: str, tags: str) -> Ticket:
        """Create and return a ticket with a validated type and normalized tags."""
        self._validate_type(ticket_type)
        self._validate_status(status)
        normalized_tags = self.normalize_tags(tags)
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO tickets(type, title, description, status, tags) VALUES (?, ?, ?, ?, ?)",
                    (ticket_type, title.strip(), description.strip(), status, ",".join(normalized_tags)),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("Only one ticket can be active.") from error
        return self.get_ticket(cursor.lastrowid)

    def get_ticket(self, ticket_id: int) -> Ticket:
        """Return the ticket identified by its SQLite primary key."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, type, title, description, status, tags, updated_at FROM tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Ticket {ticket_id} does not exist.")
        return self._ticket_from_row(row)

    def active_ticket(self) -> Ticket | None:
        """Return the active ticket, if the repository has one."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, type, title, description, status, tags, updated_at FROM tickets WHERE status = 'active'"
            ).fetchone()
        return self._ticket_from_row(row) if row else None

    def update_status(self, ticket_id: int, status: str) -> Ticket:
        """Set a ticket status and return the updated ticket."""
        self._validate_status(status)
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    "UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, ticket_id),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("Only one ticket can be active.") from error
        if cursor.rowcount == 0:
            raise ValueError(f"Ticket {ticket_id} does not exist.")
        return self.get_ticket(ticket_id)

    def add_comment(self, ticket_id: int, body: str) -> Comment:
        """Add a comment from the repository's Git user and refresh the ticket."""
        author = self._comment_author()
        with self._connect() as connection:
            if connection.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
                raise ValueError(f"Ticket {ticket_id} does not exist.")
            cursor = connection.execute(
                "INSERT INTO comments(ticket_id, author, body) VALUES (?, ?, ?)",
                (ticket_id, author, body.strip()),
            )
            connection.execute("UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
            row = connection.execute(
                "SELECT id, ticket_id, author, body, created_at FROM comments WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return Comment(*row)

    def ticket_comments(self, ticket_id: int) -> list[Comment]:
        """Return comments for a ticket in creation order."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, ticket_id, author, body, created_at FROM comments WHERE ticket_id = ? ORDER BY created_at ASC, id ASC",
                (ticket_id,),
            ).fetchall()
        return [Comment(*row) for row in rows]

    def recent_tickets(self, limit: int = 5) -> list[Ticket]:
        """Return the most recently updated tickets."""
        return self._list_tickets(
            "SELECT id, type, title, description, status, tags, updated_at FROM tickets ORDER BY updated_at DESC, id DESC LIMIT ?",
            (limit,),
        )

    def search_tickets(self, query: str, limit: int = 5) -> list[Ticket]:
        """Return recent tickets whose text or tags match a query."""
        term = f"%{query.strip()}%"
        return self._list_tickets(
                """SELECT id, type, title, description, status, tags, updated_at FROM tickets
                    WHERE type LIKE ? OR title LIKE ? OR description LIKE ? OR tags LIKE ?
               ORDER BY updated_at DESC, id DESC LIMIT ?""",
                (term, term, term, term, limit),
        )

    @staticmethod
    def normalize_tags(tags: str) -> tuple[str, ...]:
        """Return unique, sorted, lowercase tags parsed from comma-separated text."""
        return tuple(sorted({tag.strip().lower() for tag in tags.split(",") if tag.strip()}))

    def _list_tickets(self, query: str, parameters: tuple[object, ...]) -> list[Ticket]:
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._ticket_from_row(row) for row in rows]

    @staticmethod
    def _ticket_from_row(row: sqlite3.Row) -> Ticket:
        return Ticket(*row[:5], tuple(filter(None, row[5].split(","))), row[6])

    @staticmethod
    def _validate_type(ticket_type: str) -> None:
        if ticket_type not in COMMIT_TYPES:
            raise ValueError(f"Type must be one of: {', '.join(sorted(COMMIT_TYPES))}.")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(STATUSES))}.")

    def _comment_author(self) -> str:
        try:
            result = subprocess.run(
                ["git", "config", "--get", "user.name"],
                cwd=self.repository_root,
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError:
            return "Me"
        return result.stdout.strip() or "Me"

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()