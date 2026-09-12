"""Tests for Simple Project terminal output."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from simple_project.cli import _date, _show_code_results, _strip_ansi_escape_sequences, _view_active_ticket
from simple_project.code_search import CodeResult
from simple_project.tickets import TicketStore


class CodeResultDisplayTests(unittest.TestCase):
    """Verify code-search result rendering."""

    def test_displays_relative_path_docstring_preview_and_score(self) -> None:
        """Show result details across the requested three lines."""
        repository_root = Path("/project")
        result = CodeResult(
            name="read_foo",
            path=repository_root / "src/api.py",
            line=12,
            docstring="Read a Foo record.\n\nThis detail does not need to appear.",
            entity_type="Python module",
            score=7,
        )
        output = StringIO()

        with redirect_stdout(output):
            _show_code_results([result], repository_root)

        self.assertEqual(
            output.getvalue(),
            "src/api.py:12:1 (Python module)\n"
            "  Read a Foo record. This detail does not need to appear.\n"
            "  Score: 7\n",
        )

    def test_view_active_ticket_shows_comments(self) -> None:
        """Display every stored comment under the ticket details."""
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            store = TicketStore(repository_root)
            store.initialize()
            ticket = store.create_ticket("Fix login", "", "fix", "active", "")
            store.add_comment(ticket.id, "Investigating")
            store.add_comment(ticket.id, "Found the bug")
            output = StringIO()

            with redirect_stdout(output), patch("simple_project.cli._read_input", return_value="0"):
                _view_active_ticket(store, repository_root)

        self.assertIn("Comments:", output.getvalue())
        self.assertIn("Investigating", output.getvalue())
        self.assertIn("Found the bug", output.getvalue())

    def test_strip_ansi_escape_sequences_from_input(self) -> None:
        """Drop terminal arrow-key escape sequences before user text is stored."""
        self.assertEqual(_strip_ansi_escape_sequences("hello\x1b[D\x1b[Cworld"), "helloworld")

    def test_blank_status_defaults_to_active_when_creating_ticket(self) -> None:
        """Use active status when the user accepts the default on enter."""
        with TemporaryDirectory() as temporary_directory:
            store = TicketStore(Path(temporary_directory))
            store.initialize()

            with patch("simple_project.cli._read_input", side_effect=["Fix login", "Investigate it", "fix", "", "api"]):
                from simple_project.cli import _create_ticket
                _create_ticket(store)

            self.assertEqual(store.active_ticket().status, "active")

    def test_date_displays_year_month_day_only(self) -> None:
        """Render stored timestamps without the time portion in UI output."""
        self.assertEqual(_date("2024-05-15 22:41:12"), "2024-05-15")