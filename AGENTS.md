# AGENTS.md

This file is the shared operating guide for human developers and coding agents working in this repository.

## 1. Purpose and Scope

This project implements a WebAuthn/passkey demo on Flask with:
- classic account authentication (signup/login/password reset)
- passkey registration and passkey login
- user self-service defaults
- admin user management and activity logging

## 2. Human Developer Guide

### Standard local workflow

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app db upgrade
uv run flask --app webauthn_test.app:create_app init-admin
uv run flask --app webauthn_test.app:create_app run --debug
```

### Mandatory quality commands before completion

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

### Testing expectations

- Any change that mutates DB/application state must have tests.
- Security-sensitive paths are mandatory test targets: authn/authz, account deletion, admin actions, WebAuthn verification paths.
- Existence-only tests (import/callability/static response) are insufficient unless they protect critical wiring.

### Migration expectations

- Schema changes require Alembic migrations.
- For model changes:

```bash
uv run flask --app webauthn_test.app:create_app db migrate -m "<description>"
uv run flask --app webauthn_test.app:create_app db upgrade
```

- Changes are not acceptable when model/schema drift exists without migration updates.

## 3. Agent Guide

### Technical constraints

- Use `uv` for Python dependency and command execution.
- Use the existing app factory: `webauthn_test.app:create_app`.
- Treat `RP_ORIGIN` as the canonical external origin.
- Preserve credential-version invalidation semantics when rotating credentials.
- Preserve referential consistency when deleting users and related records.
- Every module under `src/` must have a high-quality top-level English docstring.
- Module docstrings must explain purpose, architectural role, and key constraints; avoid trivial method listings.

### Change sequencing

- Prefer small, auditable change sets.
- Update behavior first, then update tests.
- Run `ruff` + `mypy` + `pytest` before finalizing.
- Update README when user/admin workflows change.
- Update AGENTS when engineering process/agent rules change.

### Minimum test bar per feature

- At least one happy path
- At least one relevant failure path
- Explicit persistence/state assertions for core side effects

## 4. Agent Guardrails (required)

- Do not bypass `uv` with direct `pip` or ad-hoc tooling execution.
- Do not change schema-relevant models without migration updates.
- Do not submit fake tests where stateful behavior is central.
- Do not commit secrets (`.env`, `.admin`, real credentials/tokens).
- Do not weaken authorization boundaries (especially admin boundaries) without explicit request.
- Do not remove/erode security event logging without equivalent replacement.
- When security impact is unclear, choose conservative behavior and add tests.

## 5. README/AGENTS Update Guardrails (part of pass criteria)

These are required pass criteria, not optional hygiene:

- If user/admin behavior changes, `README.md` must be updated in the same change.
- If process/tooling/agent behavior changes, `AGENTS.md` must be updated in the same change.
- A change is not considered "pass" if code behavior changed while `README.md`/`AGENTS.md` are clearly stale.
- Review/test checks must include README/AGENTS consistency.
- Review/test checks must include module-docstring quality and coverage for `src/` modules.

Minimum pass checklist:
- `uv run ruff format .`
- `uv run ruff check --fix .`
- `uv run mypy src`
- `uv run pytest`
- documentation consistency confirmed for `README.md` and `AGENTS.md`
- `src/` module docstring requirements confirmed
