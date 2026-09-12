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
keep `simple_project` unchanged. Delete the template tests before adding tests
for the new application. The CLI stores its repository-local data in
`.simple-project.db`, which should be committed.

## Create a project

Clone this repository for the new project, then rename `src/template_app/` to
the application package name. Delete the inherited template tests with
`rm tests/test_*.py`. Update `project.name` and the `template-app` entry under
`[project.scripts]` in `pyproject.toml`.

Keep `src/simple_project/`, the `simple-project` script entry, `.python-version`,
and the `uv_build` configuration unchanged. From the new repository root, run:

```bash
git init
uv sync
uv run pre-commit install
uv run simple-project
```

The final command opens the local ticket CLI. It creates a
`.simple-project.db` file at the repository root that should be committed and
searches `src/` and `tests/` lazily when requested.

## Add to an existing project

To add the CLI to an existing `uv`-managed Python project, copy
`src/simple_project/` into its source directory and install its runtime
dependency:

```bash
uv add termcolor
```

Add this entry to `[project.scripts]` in `pyproject.toml`, preserving any
existing script entries:

```toml
simple-project = "simple_project.cli:main"
```

Projects using `uv_build` must also include `simple_project` in
`[tool.uv.build-backend].module-name`. Run `uv sync`, then start the CLI from
the project root with `uv run simple-project`. Commit the resulting
`.simple-project.db` file with the project.

## Usage

```bash
uv run simple-project
```

Comments use the Git `user.name` configured for the repository as their author.
When no Git name is available, the CLI uses `Me`.

The template pins Python 3.14 and uses `uv` managed Python installations. Its
packages are installed directly into the local environment, avoiding macOS
editable-install path issues.

Run tests with:

```bash
uv run python -m unittest discover -s tests -v
```