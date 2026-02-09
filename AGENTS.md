# AGENTS.md

This file defines repo-local guardrails for LLM agents and contributors.

## Purpose

Build and maintain a Flask + Flask-Security WebAuthn demo app with secure defaults, test coverage, and repeatable tooling.

## Tooling Rules

- Use `uv` for environment, dependency, and command execution.
- Do not run tooling directly with `python`, `pip`, `pytest`, `ruff`, or `mypy`; use `uv run ...`.

## Required Quality Commands

Run these commands before proposing changes:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

If any command fails, fix issues before finalizing.

## Testing Expectations

- Add or update tests for every behavior change.
- Prefer small, focused tests with clear names.
- Cover auth flows, recovery flows, account deletion, and admin/user activity visibility.
- For bug fixes, include a regression test.

## Coding Expectations

- Keep code simple and explicit.
- Prefer typed functions and dataclasses where appropriate.
- Avoid hardcoded secrets and insecure defaults.
- Validate and sanitize user input.
- Preserve least-privilege behavior for admin functions.

## PR/Change Checklist

Before completing work, ensure:
- Formatting is clean (`ruff format`)
- Lint issues are fixed (`ruff check --fix`)
- Type checks pass (`mypy`)
- Tests pass (`pytest`)
- New behavior is documented in `README.md` when user-facing

## Project Scope (Current)

Target user/admin features:
- Signup, login, password recovery
- User defaults page (username update, credential regeneration, PII edit, account deletion, logout)
- Admin user management and login/activity log visibility
