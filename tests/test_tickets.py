"""Tests for repository-local SQLite ticket storage."""

from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from simple_project.tickets import TicketStore


class TicketStoreTests(unittest.TestCase):
    """Verify ticket persistence invariants and comment behavior."""

    def setUp(self) -> None:
        """Create an isolated initialized ticket store."""
        self.temporary_directory = TemporaryDirectory()
        self.store = TicketStore(Path(self.temporary_directory.name))
        self.store.initialize()

    def tearDown(self) -> None:
        """Remove the temporary ticket store directory."""
        self.temporary_directory.cleanup()

    def test_only_one_ticket_can_be_active(self) -> None:
        """Reject creation of a second active ticket."""
        self.store.create_ticket("First", "", "feat", "active", "API, api")

        with self.assertRaisesRegex(ValueError, "one ticket can be active"):
            self.store.create_ticket("Second", "", "fix", "active", "")

    @patch("simple_project.tickets.subprocess.run")
    def test_comment_updates_ticket_and_uses_git_name_as_author(self, run: unittest.mock.Mock) -> None:
        """Normalize tags and attribute locally created comments to the Git user."""
        run.return_value.stdout = "Ada Lovelace\n"
        ticket = self.store.create_ticket("First", "", "fix", "open", "Feature, feature")
        comment = self.store.add_comment(ticket.id, "Investigating")

        self.assertEqual(comment.author, "Ada Lovelace")
        self.assertEqual(self.store.get_ticket(ticket.id).type, "fix")
        self.assertEqual(self.store.get_ticket(ticket.id).tags, ("feature",))

    @patch("simple_project.tickets.subprocess.run", side_effect=OSError)
    def test_comment_uses_me_as_author_without_git_configuration(self, run: unittest.mock.Mock) -> None:
        """Keep the local fallback author when Git cannot provide a name."""
        ticket = self.store.create_ticket("First", "", "docs", "open", "")

        self.assertEqual(self.store.add_comment(ticket.id, "Investigating").author, "Me")

    def test_rejects_unknown_conventional_commit_type(self) -> None:
        """Require a recognized Conventional Commits type for new tickets."""
        with self.assertRaisesRegex(ValueError, "Type must be one of"):
            self.store.create_ticket("First", "", "feature", "open", "")

    def test_migrates_existing_tickets_to_chore_type(self) -> None:
        """Preserve old tickets by assigning the default Conventional Commit type."""
        self.store.database_path.unlink()
        with sqlite3.connect(self.store.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE tickets (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO tickets(title, description, status, tags)
                VALUES ('Existing', '', 'open', '');
                """
            )

        self.store.initialize()

        self.assertEqual(self.store.get_ticket(1).type, "chore")