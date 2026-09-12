"""Tests for repository-local SQLite ticket storage."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

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
        self.store.create_ticket("First", "", "active", "API, api")

        with self.assertRaisesRegex(ValueError, "one ticket can be active"):
            self.store.create_ticket("Second", "", "active", "")

    def test_comment_updates_ticket_and_uses_me_as_author(self) -> None:
        """Normalize tags and attribute locally created comments to Me."""
        ticket = self.store.create_ticket("First", "", "open", "Feature, feature")
        comment = self.store.add_comment(ticket.id, "Investigating")

        self.assertEqual(comment.author, "Me")
        self.assertEqual(self.store.get_ticket(ticket.id).tags, ("feature",))