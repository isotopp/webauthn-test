# AGENTS.md

Diese Datei ist die gemeinsame Arbeitsgrundlage für menschliche Entwickler und Agents im Repository.

## 1. Zweck und Scope

Das Projekt liefert eine WebAuthn/Passkey-Demo auf Flask-Basis mit:
- klassischer Authentifizierung (Signup/Login/Reset)
- Passkey-Registrierung und Passkey-Login
- User-Self-Service
- Admin-Management und Activity-Logging

## 2. Dokumentation für menschliche Devs

### Lokaler Ablauf (Standard)

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app db upgrade
uv run flask --app webauthn_test.app:create_app init-admin
uv run flask --app webauthn_test.app:create_app run --debug
```

### Qualitätsbefehle (immer vor Abschluss)

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src
uv run pytest
```

### Testing-Grundsätze

- Änderungen mit DB-/State-Mutationen müssen Tests haben.
- Security-relevante Flows sind Pflicht: AuthN/AuthZ, Account-Löschung, Admin-Operationen, WebAuthn-Verify.
- Keine reinen Existenz-/Callability-Tests ohne Verhaltenswert.

### Migrations-Grundsätze

- Schemaänderungen nur mit Alembic-Migration.
- Bei Modelländerungen:

```bash
uv run flask --app webauthn_test.app:create_app db migrate -m "<beschreibung>"
uv run flask --app webauthn_test.app:create_app db upgrade
```

- Commit ohne passende Migration ist nicht akzeptabel.

## 3. Dokumentation für Agents

### Technische Leitplanken

- Nutze `uv` für alle Python-Befehle.
- Nutze vorhandene App-Factory: `webauthn_test.app:create_app`.
- Behandle `RP_ORIGIN` als kanonische externe URL.
- Bei Credential-Regeneration muss Credential-Version-Semantik erhalten bleiben.
- Bei User-Delete müssen abhängige Datensätze konsistent behandelt werden.

### Änderungsstrategie

- Kleine, nachvollziehbare Commits/Änderungsblöcke.
- Erst Verhalten ändern, dann Tests ergänzen/aktualisieren.
- Vor Abschluss immer `ruff` + `mypy` + `pytest` ausführen.
- README aktualisieren, wenn User- oder Admin-Workflow sich ändert.

### Minimaler Test-Anspruch je Feature

- Happy Path
- Mindestens ein relevanter Fehlerfall
- Nachweis der Persistenz-/State-Änderung (DB-Assertion)

## 4. Guardrails für AGENTS (hinterer Teil)

Diese Regeln sind verbindlich für Agents:

- Keine Umgehung von `uv`; kein direktes `pip install`, `python -m pytest`, etc.
- Keine stillen schema-relevanten Modelländerungen ohne Migration.
- Keine „Fake“-Tests (nur Statuscode ohne Zustandseffekt), wenn Zustandseffekt zentral ist.
- Keine Secrets im Repository einchecken (`.env`, `.admin`, reale Zugangsdaten).
- Keine Abschwächung von AuthZ-Regeln (insb. Admin-Grenzen) ohne explizite Anforderung.
- Keine regressiven Änderungen am Logging sicherheitsrelevanter Events ohne Ersatz.
- Bei Unsicherheit über Security-Auswirkungen: konservativ bleiben, Risiko benennen, Tests ergänzen.

## 5. Guardrails für README/AGENTS-Updates (Tests & Pass)

Diese Regeln sind Teil der Pass-Kriterien:

- Wenn sich User- oder Admin-Workflow ändert, muss `README.md` im selben Change aktualisiert werden.
- Wenn sich Arbeitsregeln, Tooling-Prozess oder Agent-Verhalten ändert, muss `AGENTS.md` im selben Change aktualisiert werden.
- Ein Change gilt nicht als „fertig/pass“, wenn Code-Verhalten geändert wurde, aber `README.md`/`AGENTS.md` offensichtlich veraltet sind.
- Review-/Test-Check umfasst daher immer auch einen Dokumentations-Stand-Check für `README.md` und `AGENTS.md`.
- Mindestanforderung für „pass“:
  - `uv run ruff format .`
  - `uv run ruff check --fix .`
  - `uv run mypy src`
  - `uv run pytest`
  - plus: README/AGENTS-Konsistenz bestätigt
