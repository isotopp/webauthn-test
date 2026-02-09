# webauthn-test

`webauthn-test` is a Flask demo application that showcases a full user account experience using WebAuthn and Flask-Security.

The primary user experience goal is:
- `hello, {username}` after successful authentication

## Planned Features

### Authentication
- User signup
- User login
- Password recovery/reset flow
- WebAuthn credential registration and authentication

### User Defaults Page
- Change username
- Change password / regenerate credentials
- Edit PII profile data
- Delete account
- Logout

### Admin Area
- List users
- View last login
- Edit user data
- Delete users
- View login log / user activity log

## Project Status

Initial app scaffold is implemented:
- Flask app factory with Flask-Security + SQLAlchemy integration
- Signup/login/password-recovery routes via Flask-Security
- User defaults page and admin page
- Activity logging model and admin-visible activity table

## Tech Stack
- Python
- Flask
- Flask-Security
- WebAuthn libraries (to be finalized during implementation)
- `uv` for dependency and environment management
- `ruff`, `mypy`, and `pytest` for quality gates

## Development Workflow

Use `uv` for all local commands.

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app init-db
uv run flask --app webauthn_test.app:create_app init-admin
uv run flask --app webauthn_test.app:create_app run --debug
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

Open:
- `/` for the "hello, {username}" landing page
- `/auth/register` for signup
- `/auth/login` for login
- `/auth/forgot` for password recovery
- `/user/defaults` for account defaults
- `/admin` for admin user + activity views

## Configuration Model

- Configuration is loaded from `.env` via `python-dotenv`.
- Required WebAuthn values:
  - `RP_ORIGIN` (canonical external URL)
  - `RP_NAME`
  - `RP_ID` (derived automatically from `RP_ORIGIN` hostname)
- SQLite database path defaults to `resources/app.sqlite3`.
- Logs default to `logs/app.log` and rotate on day-change or configured max KB.
- Password hashing defaults to `pbkdf2_sha512`.
- `init-admin` creates username `admin` with a generated readable password and writes two lines to `.admin`.

## Repository Docs

- Contributor and LLM guardrails: `AGENTS.md`
- PyCharm Junie context config: `.junie/config.json`
