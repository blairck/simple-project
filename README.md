# Simple Project

Simple Project is a `uv` template for Python applications. It includes a
dependency-free CLI for local ticket management and Python docstring search.

## Template layout

```text
src/
	simple_project/   # Retain this package in every generated repository.
	template_app/     # Rename this package for the generated application.
tests/
	test_code_search.py
	test_tickets.py
```

When creating a project from this template, rename `template_app`, update the
`project.name` and `template-app` console-script entry in `pyproject.toml`, and
keep `simple_project` and its tests unchanged. The CLI stores its repository
local data in `.simple-project.db`.

## Create a project

Create a new repository from this entire template, then rename
`src/template_app/` to the application package name. Update `project.name` and
the `template-app` entry under `[project.scripts]` in `pyproject.toml`.

Keep `src/simple_project/`, the `simple-project` script entry, `.python-version`,
and the `uv_build` configuration unchanged. From the new repository root, run:

```bash
git init
uv sync
uv run pre-commit install
uv run simple-project
```

The final command opens the local ticket CLI. It creates an ignored
`.simple-project.db` file at the repository root and searches `src/` and
`tests/` lazily when requested.

## Usage

```bash
uv run simple-project
```

The template pins Python 3.14 and uses `uv` managed Python installations. Its
packages are installed directly into the local environment, avoiding macOS
editable-install path issues.

Run tests with:

```bash
uv run python -m unittest discover -s tests -v
```