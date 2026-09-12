"""Interactive command-line interface for Simple Project."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import readline

from termcolor import colored

from .code_search import CodeResult, search_code
from .tickets import COMMIT_TYPES, STATUSES, Ticket, TicketStore

ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _configure_readline() -> None:
    """Enable single-key navigation for terminal line editing."""
    try:
        readline.parse_and_bind("\x1b[D: backward-char")
        readline.parse_and_bind("\x1b[C: forward-char")
    except Exception:
        pass


def main() -> None:
    """Run the interactive Simple Project command-line interface."""
    parser = argparse.ArgumentParser(description="Offline tickets and Python code search.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository to manage (default: current directory).")
    arguments = parser.parse_args()
    store = TicketStore(arguments.root.resolve())
    _configure_readline()
    store.initialize()
    _menu(store, arguments.root.resolve())


def _menu(store: TicketStore, repository_root: Path) -> None:
    while True:
        print(_tui("\nSimple Project\n1) View active ticket\n2) Create ticket\n3) Update ticket status\n4) Search tickets\n5) Search code\n6) Recently updated tickets\n0) Exit"))
        choice = _read_input(_tui("$ ")).strip()
        try:
            if choice == "1":
                _view_active_ticket(store, repository_root)
            elif choice == "2":
                _create_ticket(store)
            elif choice == "3":
                _update_status(store)
            elif choice == "4":
                _show_tickets(store.search_tickets(_read_input(_tui("Search text or tag: "))))
            elif choice == "5":
                _show_code_results(search_code(repository_root, _read_input(_tui("Search code: "))), repository_root)
            elif choice == "6":
                _show_tickets(store.recent_tickets())
            elif choice == "0":
                return
            else:
                print(_warning("Choose a listed option."))
        except ValueError as error:
            print(_warning(f"Warning: {error}"))


def _create_ticket(store: TicketStore) -> None:
    title = _read_input(_tui("Title: "))
    description = _read_input(_tui("Description: "))
    ticket_type = _read_input(_tui(f"Type ({', '.join(sorted(COMMIT_TYPES))}): ")).strip().lower()
    status = _read_input(_tui(f"Status ({', '.join(sorted(STATUSES))}) [active]: ")).strip().lower()
    if not status:
        status = "active"
    tags = _read_input(_tui("Tags (comma-separated): "))
    ticket = store.create_ticket(title, description, ticket_type, status, tags)
    print(_tui(f"Created ticket #{ticket.id}."))


def _update_status(store: TicketStore) -> None:
    ticket_id = int(_read_input(_tui("Ticket ID: ")))
    status = _read_input(_tui(f"Status ({', '.join(sorted(STATUSES))}): ")).strip().lower()
    print(_tui(f"Updated ticket #{store.update_status(ticket_id, status).id}."))


def _view_active_ticket(store: TicketStore, repository_root: Path) -> None:
    ticket = store.active_ticket()
    if ticket is None:
        print(_warning("No active ticket."))
        return
    print(_tui(f"\nTicket #{ticket.id}"))
    print(f"{_tui('Type:')} {_user_text(ticket.type)}")
    print(f"{_tui('Title:')} {_user_text(ticket.title)}")
    print(f"{_tui('Description:')} {_user_text(ticket.description)}")
    print(f"{_tui('Status:')} {_user_text(ticket.status)}")
    print(f"{_tui('Tags:')} {_user_text(', '.join(ticket.tags))}")
    print(f"{_tui('Updated:')} {_date(ticket.updated_at)}")
    comments = store.ticket_comments(ticket.id)
    if comments:
        print(_tui("Comments:"))
        for comment in comments:
            print(f"  {_user_text(comment.author)} ({_date(comment.created_at)}) {_user_text(comment.body)}")
    print(_tui("1) Find related code\n2) Update ticket status\n3) Add comment\n0) Back"))
    choice = _read_input(_tui("$ ")).strip()
    if choice == "1":
        _show_code_results(search_code(repository_root, f"{ticket.title} {ticket.description}"), repository_root)
    elif choice == "2":
        status = _read_input(_tui(f"Status ({', '.join(sorted(STATUSES))}): ")).strip().lower()
        store.update_status(ticket.id, status)
    elif choice == "3":
        store.add_comment(ticket.id, _read_input(_tui("Comment: ")))


def _read_input(prompt: str) -> str:
    """Read a line from stdin while allowing terminal editing and stripping raw escape bytes."""
    value = input(prompt)
    return _strip_ansi_escape_sequences(value)


def _strip_ansi_escape_sequences(text: str) -> str:
    """Drop ANSI cursor-control sequences that can leak from arrow-key input."""
    return ANSI_ESCAPE_SEQUENCE.sub("", text)


def _show_tickets(tickets: list[Ticket]) -> None:
    if not tickets:
        print(_warning("No tickets found."))
    for ticket in tickets:
        print(
            f"{_tui(f'#{ticket.id} [{ticket.type}] [{ticket.status}]')} {_user_text(ticket.title)} "
            f"{_user_text(f'({', '.join(ticket.tags)})')} {_date(ticket.updated_at)}"
        )


def _show_code_results(results: list[CodeResult], repository_root: Path) -> None:
    if not results:
        print(_warning("No code results found."))
    for result in results:
        print(_tui(f"{result.path.relative_to(repository_root)}:{result.line}:1 ({result.entity_type})"))
        print(f"  {_user_text(_docstring_preview(result.docstring))}")
        print(f"  {_date(f'Score: {result.score}')}")


def _docstring_preview(docstring: str) -> str:
    return " ".join(docstring.split())[:100]


def _tui(text: str) -> str:
    return colored(text, "blue")


def _user_text(text: str) -> str:
    return colored(text, "white")


def _date(text: str) -> str:
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    date_text = match.group(0) if match else text
    return colored(date_text, "green")


def _warning(text: str) -> str:
    return colored(text, "yellow")


if __name__ == "__main__":
    main()