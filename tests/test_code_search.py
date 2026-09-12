"""Tests for lazy Python AST code search."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from simple_project.code_search import search_code


class CodeSearchTests(unittest.TestCase):
    """Verify documented entity discovery and scoring."""

    def test_finds_documented_module_at_first_line(self) -> None:
        """Return a documented module result with a line-one source link."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_directory = root / "src"
            source_directory.mkdir()
            (source_directory / "draft.py").write_text(
                '\"\"\"Draft analysis helpers.\"\"\"\n', encoding="utf-8"
            )

            results = search_code(root, "draft")

        self.assertEqual(results[0].name, "<module>")
        self.assertEqual(results[0].line, 1)

    def test_finds_documented_entities_in_configured_directory(self) -> None:
        """Find a documented function and score its name and docstring words."""
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_directory = root / "src"
            source_directory.mkdir()
            (source_directory / "api.py").write_text(
                'def read_foo():\n    """Read a Foo record."""\n', encoding="utf-8"
            )

            results = search_code(root, "read foo")

        self.assertEqual(results[0].name, "read_foo")
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[0].docstring, "Read a Foo record.")
        self.assertEqual(results[0].entity_type, "Python function")
        self.assertTrue(results[0].vscode_link.startswith("vscode://file/"))