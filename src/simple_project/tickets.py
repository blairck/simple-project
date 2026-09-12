"""SQLite persistence for local tickets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3


STATUSES = frozenset({"open", "closed", "cancelled", "active"})


@dataclass(frozen=True)
class Ticket:
    """Represent a locally stored ticket."""

    id: int
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
        self.database_path = repository_root / ".simple-project.db"

    def initialize(self) -> None:
        """Create the ticket database schema when it does not already exist."""
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY,
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

    def create_ticket(self, title: str, description: str, status: str, tags: str) -> Ticket:
        """Create and return a ticket with normalized tags."""
        self._validate_status(status)
        normalized_tags = self.normalize_tags(tags)
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO tickets(title, description, status, tags) VALUES (?, ?, ?, ?)",
                    (title.strip(), description.strip(), status, ",".join(normalized_tags)),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("Only one ticket can be active.") from error
        return self.get_ticket(cursor.lastrowid)

    def get_ticket(self, ticket_id: int) -> Ticket:
        """Return the ticket identified by its SQLite primary key."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, description, status, tags, updated_at FROM tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Ticket {ticket_id} does not exist.")
        return self._ticket_from_row(row)

    def active_ticket(self) -> Ticket | None:
        """Return the active ticket, if the repository has one."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, description, status, tags, updated_at FROM tickets WHERE status = 'active'"
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
        """Add a comment from Me and refresh the ticket update time."""
        with self._connect() as connection:
            if connection.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
                raise ValueError(f"Ticket {ticket_id} does not exist.")
            cursor = connection.execute(
                "INSERT INTO comments(ticket_id, author, body) VALUES (?, 'Me', ?)",
                (ticket_id, body.strip()),
            )
            connection.execute("UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ticket_id,))
            row = connection.execute(
                "SELECT id, ticket_id, author, body, created_at FROM comments WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return Comment(*row)

    def recent_tickets(self, limit: int = 5) -> list[Ticket]:
        """Return the most recently updated tickets."""
        return self._list_tickets(
            "SELECT id, title, description, status, tags, updated_at FROM tickets ORDER BY updated_at DESC, id DESC LIMIT ?",
            (limit,),
        )

    def search_tickets(self, query: str, limit: int = 5) -> list[Ticket]:
        """Return recent tickets whose text or tags match a query."""
        term = f"%{query.strip()}%"
        return self._list_tickets(
            """SELECT id, title, description, status, tags, updated_at FROM tickets
               WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
               ORDER BY updated_at DESC, id DESC LIMIT ?""",
            (term, term, term, limit),
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
        return Ticket(*row[:4], tuple(filter(None, row[4].split(","))), row[5])

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(STATUSES))}.")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection