"""Interactive command-line interface for Simple Project."""

from __future__ import annotations

import argparse
from pathlib import Path

from termcolor import colored

from .code_search import CodeResult, search_code
from .tickets import COMMIT_TYPES, STATUSES, Ticket, TicketStore


def main() -> None:
    """Run the interactive Simple Project command-line interface."""
    parser = argparse.ArgumentParser(description="Offline tickets and Python code search.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository to manage (default: current directory).")
    arguments = parser.parse_args()
    store = TicketStore(arguments.root.resolve())
    store.initialize()
    _menu(store, arguments.root.resolve())


def _menu(store: TicketStore, repository_root: Path) -> None:
    while True:
        print(_tui("\nSimple Project\n1) View active ticket\n2) Create ticket\n3) Update ticket status\n4) Search tickets\n5) Search code\n6) Recently updated tickets\n0) Exit"))
        choice = input(_tui("$ ")).strip()
        try:
            if choice == "1":
                _view_active_ticket(store, repository_root)
            elif choice == "2":
                _create_ticket(store)
            elif choice == "3":
                _update_status(store)
            elif choice == "4":
                _show_tickets(store.search_tickets(input(_tui("Search text or tag: "))))
            elif choice == "5":
                _show_code_results(search_code(repository_root, input(_tui("Search code: "))), repository_root)
            elif choice == "6":
                _show_tickets(store.recent_tickets())
            elif choice == "0":
                return
            else:
                print(_warning("Choose a listed option."))
        except ValueError as error:
            print(_warning(f"Warning: {error}"))


def _create_ticket(store: TicketStore) -> None:
    title = input(_tui("Title: "))
    description = input(_tui("Description: "))
    ticket_type = input(_tui(f"Type ({', '.join(sorted(COMMIT_TYPES))}): ")).strip().lower()
    status = input(_tui(f"Status ({', '.join(sorted(STATUSES))}): ")).strip().lower()
    tags = input(_tui("Tags (comma-separated): "))
    ticket = store.create_ticket(title, description, ticket_type, status, tags)
    print(_tui(f"Created ticket #{ticket.id}."))


def _update_status(store: TicketStore) -> None:
    ticket_id = int(input(_tui("Ticket ID: ")))
    status = input(_tui(f"Status ({', '.join(sorted(STATUSES))}): ")).strip().lower()
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
    print(_tui("1) Find related code\n2) Update ticket status\n3) Add comment\n0) Back"))
    choice = input(_tui("$ ")).strip()
    if choice == "1":
        _show_code_results(search_code(repository_root, f"{ticket.title} {ticket.description}"), repository_root)
    elif choice == "2":
        status = input(_tui(f"Status ({', '.join(sorted(STATUSES))}): ")).strip().lower()
        store.update_status(ticket.id, status)
    elif choice == "3":
        store.add_comment(ticket.id, input(_tui("Comment: ")))


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
    return colored(text, "green")


def _warning(text: str) -> str:
    return colored(text, "yellow")


if __name__ == "__main__":
    main()