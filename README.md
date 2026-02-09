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

Bootstrap phase: documentation and development guardrails are in place, implementation is next.

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
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

## Repository Docs

- Contributor and LLM guardrails: `AGENTS.md`
- PyCharm Junie context config: `.junie/config.json`
