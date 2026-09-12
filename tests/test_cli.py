"""Tests for Simple Project terminal output."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest

from simple_project.cli import _show_code_results
from simple_project.code_search import CodeResult


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