"""Environment-file schema and rendering helpers.

This module defines the expected `.env` shape as structured metadata and
provides parsing/merging/rendering utilities used by bootstrap commands.

Design constraints:
- existing user-provided values are preserved by default
- derived fields (notably RP_ID from RP_ORIGIN) stay internally consistent
- generated secrets are only created when absent
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class EnvField:
    key: str
    comment: str
    required: bool = False
    default: str | None = None
    derived_from: str | None = None


REGISTRY: tuple[EnvField, ...] = (
    EnvField("RP_ORIGIN", "Canonical external origin, must include scheme.", True),
    EnvField("RP_NAME", "Display name shown to authenticators.", True),
    EnvField(
        "RP_ID",
        "Derived from RP_ORIGIN hostname. Keep aligned with RP_ORIGIN.",
        True,
        derived_from="RP_ORIGIN",
    ),
    EnvField("SECRET_KEY", "Flask session/signing secret key.", True),
    EnvField("SECURITY_PASSWORD_SALT", "Password hashing/recovery salt.", True),
    EnvField(
        "SECURITY_PASSWORD_HASH",
        "Passlib scheme used for password hashing.",
        default="pbkdf2_sha512",
    ),
    EnvField(
        "DATABASE_PATH",
        "SQLite database location.",
        default="resources/app.sqlite3",
    ),
    EnvField("LOG_DIR", "Application log directory.", default="logs"),
    EnvField("LOG_FILENAME", "Application log filename.", default="app.log"),
    EnvField("LOG_LEVEL", "Python log level.", default="INFO"),
    EnvField(
        "LOG_MAX_KB",
        "Rotate logs when this size in KB is exceeded.",
        default="1024",
    ),
    EnvField(
        "ADMIN_EMAIL",
        "Email address used for the initial admin account.",
        default="admin@example.invalid",
    ),
    EnvField(
        "SECURITY_EMAIL_SENDER",
        "From-address used by Flask-Security email flows.",
        default="noreply@localhost",
    ),
    EnvField(
        "SECURITY_CHECK_EMAIL_DELIVERABILITY",
        "Set true to enforce deliverability checks on email fields.",
        default="false",
    ),
    EnvField("MAIL_SERVER", "SMTP submit host/IP.", default="127.0.0.1"),
    EnvField("MAIL_PORT", "SMTP submit port.", default="587"),
    EnvField("MAIL_USE_TLS", "Use STARTTLS for SMTP submit.", default="true"),
    EnvField("MAIL_USE_SSL", "Use implicit SSL for SMTP.", default="false"),
    EnvField("MAIL_USERNAME", "SMTP submit username.", default=""),
    EnvField("MAIL_PASSWORD", "SMTP submit password.", default=""),
    EnvField(
        "MAIL_DEFAULT_SENDER",
        "Envelope/header sender for app emails.",
        default="noreply@localhost",
    ),
    EnvField(
        "MAIL_SUPPRESS_SEND",
        "Set true to disable email delivery (tests/dev only).",
        default="false",
    ),
    EnvField(
        "IMAP_HOST",
        "IMAPS host/IP (ops reference; not used by app).",
        default="127.0.0.1",
    ),
    EnvField(
        "IMAP_PORT", "IMAPS port (ops reference; not used by app).", default="993"
    ),
    EnvField(
        "IMAP_USERNAME", "IMAPS username (ops reference; not used by app).", default=""
    ),
    EnvField(
        "IMAP_PASSWORD", "IMAPS password (ops reference; not used by app).", default=""
    ),
    EnvField(
        "APP_HOST",
        "HTTP bind host for local reverse-proxy target.",
        default="127.0.0.1",
    ),
    EnvField(
        "APP_PORT", "HTTP bind port for local reverse-proxy target.", default="8080"
    ),
)


def derive_rp_id(rp_origin: str) -> str:
    parsed = urlparse(rp_origin)
    if not parsed.hostname:
        msg = "Cannot derive RP_ID: RP_ORIGIN is missing a hostname."
        raise ValueError(msg)
    return parsed.hostname


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def generated_defaults(existing: dict[str, str]) -> dict[str, str]:
    defaults: dict[str, str] = {}
    if "SECRET_KEY" not in existing:
        defaults["SECRET_KEY"] = secrets.token_urlsafe(48)
    if "SECURITY_PASSWORD_SALT" not in existing:
        defaults["SECURITY_PASSWORD_SALT"] = secrets.token_urlsafe(32)
    return defaults


def merged_env(existing: dict[str, str], supplied: dict[str, str]) -> dict[str, str]:
    merged = dict(existing)
    merged.update({k: v for k, v in supplied.items() if v})
    merged.update(generated_defaults(merged))

    if "RP_ORIGIN" in merged and merged["RP_ORIGIN"]:
        merged["RP_ID"] = derive_rp_id(merged["RP_ORIGIN"])

    for field in REGISTRY:
        if field.key not in merged and field.default is not None:
            merged[field.key] = field.default

    return merged


def render_env_file(values: dict[str, str]) -> str:
    lines: list[str] = [
        "# Generated by: flask init-env",
        "# Update values as needed. Existing values are preserved on re-run.",
        "",
    ]
    for field in REGISTRY:
        lines.append(f"# {field.comment}")
        if field.derived_from:
            lines.append(f"# Derived from: {field.derived_from}")
        value = values.get(field.key, "")
        lines.append(f"{field.key}={value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
