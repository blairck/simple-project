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

If `uv run simple-project` raises `ModuleNotFoundError: No module named
'simple_project'` on Python 3.14, some process on the machine (Spotlight,
iCloud Drive, backup or security software — commonly triggered under
`~/Documents`) has set the macOS "hidden" flag on files inside `.venv`. Python
3.14's `site.py` intentionally skips any `.pth` file with that flag as a
security hardening measure, and setuptools editable installs rely entirely on
a `.pth` file to expose the package. `chflags -R nohidden .venv` clears the
flag for one run, but it can reappear moments later from the same background
process, breaking the install again.

The durable fix is to stop depending on the `.pth` file at all: install the
project as a non-editable wheel every time. Since this must survive every new
terminal, set it once per machine in your shell profile (e.g. `~/.bash_profile`
or `~/.zshrc`) rather than exporting it per session:

```bash
echo 'export UV_NO_EDITABLE=true' >> ~/.bash_profile
```

`uv.toml` and `.env` files cannot express this (uv rejects `no-editable` as a
config key, and `.env` loads too late to affect `uv`'s own sync step), so the
shell profile is the only place this setting reliably persists.

### Updating simple-project code

To update the `simple-project` code in your existing project, follow these steps:

1. Pull the latest changes from the `simple-project` repository.
2. Copy the updated `src/simple_project/` directory into your project's source directory.
3. Run `export UV_NO_EDITABLE=true && uv sync --reinstall` to ensure all dependencies and scripts are up to date. Note the UV_NO_EDITABLE is only needed if your bash_profile file doesn't already have it.
4. Start the CLI from the project root with `uv run simple-project`.

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