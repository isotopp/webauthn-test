# webauthn-test

`webauthn-test` ist eine Flask-Demo für klassische Account-Authentifizierung (Flask-Security) plus WebAuthn/Passkeys.

Ziel-UX:
- Nach erfolgreicher Anmeldung: `hello, {username}`

## Aktueller Zustand

Implementiert:
- Signup, Login, Passwort-Reset (Flask-Security)
- User-Defaults-Seite (Username, PII, Credential-Version, Account-Löschung, Logout)
- Admin-Seite (User-Liste, Edit/Delete, Activity-Log)
- WebAuthn Passkey-Registrierung und Passkey-Login
- SQLite + SQLAlchemy + Flask-Migrate
- Test-Suite für auth-/state-/security-relevante Flows

## How To Use (User-Facing)

### 1. Account anlegen
- Öffne `/auth/register`
- Felder ausfüllen (`email`, `username`, `password`)

### 2. Klassisch anmelden
- Öffne `/auth/login`
- Mit E-Mail + Passwort anmelden

### 3. Passkey registrieren
- Nach Login auf `/user/defaults`
- „Register New Passkey“ klicken
- Browser/WebAuthn-Dialog abschließen

### 4. Passkey-Login nutzen
- Öffne `/`
- Im Abschnitt „Passkey Login“ Username eingeben
- „Sign in with Passkey“ klicken

### 5. Profil verwalten
- `/user/defaults`
- Username ändern
- PII ändern
- Credential-Version erhöhen (invalidiert alte Passkeys)
- Logout / Account löschen

## Admin-Facing

### Installation (lokal)

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app db upgrade
uv run flask --app webauthn_test.app:create_app init-admin
uv run flask --app webauthn_test.app:create_app run --debug
```

Ergebnisse:
- `.env` wird erzeugt/ergänzt
- DB-Schema wird per Migration aufgebaut
- `.admin` enthält 2 Zeilen: `admin` und generiertes Passwort
- Admin-User wird in DB provisioniert

### Deploy (uWSGI hinter Apache TLS-Terminator)

Voraussetzungen:
- Externe Canonical URL gesetzt als `RP_ORIGIN` (z. B. `https://webauthn.home.koehntopp.de`)
- `RP_ID` wird daraus abgeleitet (Hostname)
- Apache setzt Forward-Header korrekt (`Host`, `X-Forwarded-Proto`, `X-Forwarded-For`)
- LE/TLS wird durch Apache verwaltet

App-Start:
- WSGI-Entry: `webauthn_test.wsgi:app`
- Reverse Proxy auf uWSGI/HTTP-App-Port

### Update

```bash
git pull
uv sync
uv run flask --app webauthn_test.app:create_app db upgrade
uv run pytest
```

### Migrate

Neue Migration erzeugen:

```bash
uv run flask --app webauthn_test.app:create_app db migrate -m "<beschreibung>"
```

Migration anwenden:

```bash
uv run flask --app webauthn_test.app:create_app db upgrade
```

### Admin Facilities nutzen

- `/admin`: User sehen, editieren, löschen
- Activity-Log einsehen
- Sicherheitsrelevante Änderungen (Delete/Edit) werden im Log dokumentiert

## Konfiguration

Konfiguration via `.env` (python-dotenv).

Wichtige Variablen:
- `RP_ORIGIN` (canonical externe URL, inkl. `https://`)
- `RP_NAME`
- `RP_ID` (aus `RP_ORIGIN` abgeleitet)
- `DATABASE_PATH` (Default: `resources/app.sqlite3`)
- `LOG_DIR`, `LOG_FILENAME`, `LOG_MAX_KB`, `LOG_LEVEL`
- `SECRET_KEY`, `SECURITY_PASSWORD_SALT`, `SECURITY_PASSWORD_HASH`
- `ADMIN_EMAIL`

## Relevante Endpunkte

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

## Qualitätssicherung

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```
