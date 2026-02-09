# webauthn-test

`webauthn-test` is a Flask demo application that combines Flask-Security account flows with WebAuthn passkeys.

Primary UX goal:
- after successful authentication, show `hello, {username}`

## Current State

Implemented:
- Signup, login, and password reset via Flask-Security
- User defaults page (username updates, PII updates, credential version rotation, account deletion, logout)
- Admin page (user list/edit/delete, activity log visibility)
- WebAuthn passkey registration and passkey login
- SQLite + SQLAlchemy + Flask-Migrate schema management
- Integration-heavy tests for auth/state/security relevant behavior

## User-Facing: How To Use

### 1. Register an account
- Open `/auth/register`
- Fill `email`, `username`, and password fields

### 2. Log in with password
- Open `/auth/login`
- Authenticate using username or email + password

### 3. Register a passkey
- After login, open `/user/defaults`
- Click `Register New Passkey`
- Complete the browser authenticator ceremony

### 4. Log in with passkey
- Open `/`
- Enter username in `Passkey Login`
- Click `Sign in with Passkey`

### 5. Manage account defaults
- Open `/user/defaults`
- Change username
- Edit PII
- Rotate credential version (invalidates older passkeys)
- Logout or delete account

## Admin-Facing: Install, Deploy, Update, Migrate, Operate

### Local install/bootstrap

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app db upgrade
uv run flask --app webauthn_test.app:create_app init-admin
uv run flask --app webauthn_test.app:create_app run --debug
```

What this does:
- creates/completes `.env`
- applies DB schema migrations
- writes `.admin` with two lines (`admin` and generated password)
- provisions admin user and role in the database

### Deploy model (Apache TLS terminator, Rocky 9)

Requirements:
- set canonical external URL in `RP_ORIGIN` (for example `https://webauthn.home.koehntopp.de`)
- derive `RP_ID` from the canonical host
- TLS certificates are managed by Apache (for example via `mod_md`)

Primary deployment mode (matches your existing pattern):
- Apache `mod_wsgi` daemon mode via repository `app.wsgi`
- no separate backend port required

Rocky Linux 9 deployment templates:
- `/Users/kris/PycharmProjects/webauthn-test/deploy/rocky9/README.md`
- `/Users/kris/PycharmProjects/webauthn-test/deploy/rocky9/apache-macro-mod_wsgi.conf`

Optional alternative mode:
- Apache reverse proxy to uWSGI HTTP backend on `127.0.0.1:<port>`
- templates retained in:
  - `/Users/kris/PycharmProjects/webauthn-test/deploy/rocky9/webauthn.service`
  - `/Users/kris/PycharmProjects/webauthn-test/deploy/rocky9/uwsgi.ini`
  - `/Users/kris/PycharmProjects/webauthn-test/deploy/rocky9/apache-vhost.conf`

### Update

```bash
git pull
uv sync
uv run flask --app webauthn_test.app:create_app db upgrade
uv run pytest
```

### Migrate

Create migration:

```bash
uv run flask --app webauthn_test.app:create_app db migrate -m "<description>"
```

Apply migration:

```bash
uv run flask --app webauthn_test.app:create_app db upgrade
```

### Use admin facilities
- `/admin` to list/edit/delete users
- `/admin` activity log table for authentication and user-management events

## Configuration

Configuration is loaded from `.env` via `python-dotenv`.

Important variables:
- `RP_ORIGIN` (canonical external URL including `https://`)
- `RP_NAME`
- `RP_ID` (derived from `RP_ORIGIN` host)
- `DATABASE_PATH` (default `resources/app.sqlite3`)
- `LOG_DIR`, `LOG_FILENAME`, `LOG_MAX_KB`, `LOG_LEVEL`
- `SECRET_KEY`, `SECURITY_PASSWORD_SALT`, `SECURITY_PASSWORD_HASH`
- `ADMIN_EMAIL`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`, `SECURITY_EMAIL_SENDER`
- `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`, `IMAP_PASSWORD` (ops reference; not consumed by runtime)
- `APP_HOST`, `APP_PORT` (backend bind target for reverse proxy)

## Endpoints

HTML:
- `/`
- `/auth/register`
- `/auth/login`
- `/auth/reset`
- `/user/defaults`
- `/admin`

WebAuthn JSON:
- `POST /webauthn/register/begin`
- `POST /webauthn/register/finish`
- `POST /webauthn/login/begin`
- `POST /webauthn/login/finish`

## Quality Gates

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

## Test Strategy Notes

See `/Users/kris/PycharmProjects/webauthn-test/tests/README.md` for:
- what behavior the test suite functionally validates
- what is intentionally not tested because it is brittle/low-value
