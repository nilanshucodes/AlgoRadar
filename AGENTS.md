# Repository Guidelines

## Project Structure & Module Organization

- `app.py` contains the Flask application, SQLAlchemy model, CList API integration, cache, routes, and database CLI commands.
- `wsgi.py` exposes the application for local WSGI use; `index.py` is the Vercel entry point configured by `vercel.json`.
- `templates/` contains Jinja pages. Extend `templates/base.html` for shared navigation, flash messages, and theme behavior.
- `static/style.css` holds site-wide styles; platform logos live in `static/images/`.
- Keep runtime SQLite files under `instance/`. Do not commit local databases, virtual environments, caches, or `.env` files.

## Package Manager & Setup

- Use Python 3.9+ and `pip` with `requirements.txt`.
- Create the ignored environment with `python3 -m venv venv`, then run `source venv/bin/activate`.
- Install dependencies with `python -m pip install -r requirements.txt`.
- Copy the environment variables documented in `README.md` into `.env`; never commit real API keys, admin credentials, or `SECRET_KEY` values.

## Build, Test, and Development Commands

| Task | Command |
| --- | --- |
| Initialize database | `flask --app app init-db` |
| Run development server | `flask --app app run --debug` |
| Production-style server | `gunicorn app:app` |
| Compile smoke check | `python -m compileall app.py wsgi.py index.py` |

## File-Scoped Commands

| Task | Command |
| --- | --- |
| Check one Python file | `python -m py_compile path/to/file.py` |
| Run one future test | `pytest tests/test_routes.py -k test_name` |

## Coding Style & Naming Conventions

- Use four-space Python indentation, `snake_case` for functions and variables, `PascalCase` for models, and uppercase names for configuration constants.
- Keep route handlers small, use parameterized ORM operations, and preserve the existing Jinja/template organization.
- No formatter or linter is configured; match surrounding code and keep imports grouped by standard library, third-party, then local modules.

## Testing Guidelines

- No automated test suite or coverage threshold currently exists. Add Flask tests under `tests/` using `test_*.py` names and isolate database/API dependencies with fixtures or mocks.
- For route or UI changes, verify `/`, `/contact`, `/privacy`, and the affected admin flow. Include responsive and dark-mode checks for template or CSS work.

## Commit & Pull Request Guidelines

- Follow the history’s short imperative subjects: `Add Privacy Policy page`, `Update footer year`, or `Remove obsolete script`.
- Keep each commit focused. Pull requests must explain behavior changes, configuration or migration steps, and validation performed; link relevant issues and include screenshots for visual changes.

## Commit Attribution

- AI-authored commits must include `Co-Authored-By: <agent model and attribution byline>` in the commit message trailer.
