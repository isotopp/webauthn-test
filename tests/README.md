# Test Strategy

This test suite is designed to validate behavior that matters for correctness,
security, and state transitions.

## What We Functionally Test

### Authentication and account lifecycle
- registration persists users with hashed passwords
- login updates user activity state
- password reset updates credentials and logs security events

### Authorization boundaries
- protected routes reject anonymous users
- admin routes enforce admin role boundaries

### User/Admin mutations with persistence checks
- user defaults actions mutate database state correctly
- admin edit/delete operations mutate target records correctly
- deletion flows enforce safety constraints (for example admin self-delete block)
- security-relevant actions generate activity log rows

### WebAuthn lifecycle
- registration begin stores server challenge state
- registration finish persists WebAuthn credential material
- authentication begin enforces active credential-version semantics
- authentication finish updates sign count and creates authenticated session state

### Operational CLI behavior
- schema/bootstrap commands create expected tables and admin bootstrap state
- `.env` initialization preserves existing values and fills required defaults

## What We Intentionally Do Not Test (Low Value / Brittle)

- static template markup snapshots that fail on cosmetic HTML changes
- framework internals of Flask-Security or the `webauthn` package itself
- exact cryptographic hash string formats beyond semantic checks (e.g. not plaintext)
- exact timestamp values at sub-second precision
- browser-native authenticator UI behavior (outside server test scope)

These exclusions are intentional so tests remain stable, behavior-focused, and
useful for detecting regressions in application-owned logic.
