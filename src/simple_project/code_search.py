"""Lazy AST indexing and relevance scoring for Python source files."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import quote


WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")
CAMEL_CASE_PATTERN = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


@dataclass(frozen=True)
class CodeResult:
    """Describe a documented Python entity matching a code search."""

    name: str
    path: Path
    line: int
    docstring: str
    entity_type: str
    score: int

    @property
    def vscode_link(self) -> str:
        """Return a VS Code deep link to the entity's source location."""
        return f"vscode://file/{quote(str(self.path.resolve()))}:{self.line}:1"


def search_code(repository_root: Path, query: str, directories: tuple[Path, ...] | None = None, limit: int = 5) -> list[CodeResult]:
    """Return the highest-scoring documented entities for a query."""
    search_directories = directories or (repository_root / "src", repository_root / "tests")
    cli_directory = repository_root / "src" / "simple_project"
    query_words = Counter(word.lower() for word in WORD_PATTERN.findall(query))
    results: list[CodeResult] = []
    for directory in search_directories:
        if not directory.is_dir():
            continue
        for source_file in directory.rglob("*.py"):
            if source_file.is_relative_to(cli_directory):
                continue
            results.extend(_score_file(source_file, query_words))
    return sorted(results, key=lambda result: (-result.score, result.name, str(result.path)))[:limit]


def _score_file(source_file: Path, query_words: Counter[str]) -> list[CodeResult]:
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    results: list[CodeResult] = []
    for node, name in _documented_entities(tree):
        docstring = ast.get_docstring(node) or ""
        searchable_name = CAMEL_CASE_PATTERN.sub(" ", name.replace("_", " "))
        words = Counter(word.lower() for word in WORD_PATTERN.findall(f"{searchable_name} {docstring}"))
        score = sum(count * words[word] for word, count in query_words.items())
        if score:
            results.append(
                CodeResult(
                    name,
                    source_file,
                    getattr(node, "lineno", 1),
                    docstring,
                    _entity_type(node),
                    score,
                )
            )
    return results


def _entity_type(node: ast.AST) -> str:
    if isinstance(node, ast.Module):
        return "Python module"
    if isinstance(node, ast.ClassDef):
        return "Python class"
    return "Python function"


def _documented_entities(tree: ast.Module) -> list[tuple[ast.AST, str]]:
    results: list[tuple[ast.AST, str]] = []

    def visit(node: ast.AST, parents: tuple[str, ...]) -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified_name = ".".join((*parents, node.name))
            if ast.get_docstring(node) is not None:
                results.append((node, qualified_name))
            for child in ast.iter_child_nodes(node):
                visit(child, (*parents, node.name))
        else:
            for child in ast.iter_child_nodes(node):
                visit(child, parents)

    if ast.get_docstring(tree) is not None:
        results.append((tree, "<module>"))
    visit(tree, ())
    return results