"""Runtime configuration model for app, security, storage, and logging.

This module resolves environment variables (via python-dotenv), derives
WebAuthn relying-party identity values, and exposes a single config object
consumed by the Flask factory.

Constraints:
- RP origin/ID semantics must remain canonical and deterministic
- defaults are safe for local development, not production hardening
- path-based resources are resolved relative to repository structure
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "resources" / "app.sqlite3"


def derive_rp_id(rp_origin: str) -> str:
    parsed = urlparse(rp_origin)
    if parsed.scheme not in {"http", "https"}:
        msg = "RP_ORIGIN must include http or https scheme."
        raise ValueError(msg)
    if not parsed.hostname:
        msg = "RP_ORIGIN must include a hostname."
        raise ValueError(msg)
    return parsed.hostname


class Config:
    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")

        rp_origin = os.getenv("RP_ORIGIN", "https://example.invalid")
        rp_name = os.getenv("RP_NAME", "WebAuthn Demo")

        configured_db_path = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))
        if configured_db_path.is_absolute():
            database_path = configured_db_path
        else:
            database_path = BASE_DIR / configured_db_path
        database_path.parent.mkdir(parents=True, exist_ok=True)

        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.SECURITY_PASSWORD_SALT = os.getenv(
            "SECURITY_PASSWORD_SALT", "dev-salt-change-me"
        )
        self.SECURITY_PASSWORD_HASH = os.getenv(
            "SECURITY_PASSWORD_HASH", "pbkdf2_sha512"
        )
        self.SECURITY_RECOVERABLE = True
        self.SECURITY_REGISTERABLE = True
        self.SECURITY_CHANGEABLE = True
        self.SECURITY_SEND_REGISTER_EMAIL = False
        self.SECURITY_UNIFIED_SIGNIN = False
        self.SECURITY_URL_PREFIX = "/auth"
        self.SECURITY_POST_LOGIN_VIEW = "/"
        self.SECURITY_POST_LOGOUT_VIEW = "/"
        self.SECURITY_POST_REGISTER_VIEW = "/user/defaults"
        self.SECURITY_POST_RESET_VIEW = "/"
        self.SECURITY_EMAIL_SENDER = os.getenv(
            "SECURITY_EMAIL_SENDER", "noreply@localhost"
        )

        self.MAIL_SERVER = os.getenv("MAIL_SERVER", "127.0.0.1")
        self.MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
        self.MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
        self.MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
        self.MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
        self.MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
        self.MAIL_DEFAULT_SENDER = os.getenv(
            "MAIL_DEFAULT_SENDER", self.SECURITY_EMAIL_SENDER
        )
        self.MAIL_SUPPRESS_SEND = (
            os.getenv("MAIL_SUPPRESS_SEND", "false").lower() == "true"
        )

        self.APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
        self.APP_PORT = int(os.getenv("APP_PORT", "8080"))

        self.RP_ORIGIN = rp_origin
        self.RP_NAME = rp_name
        self.RP_ID = os.getenv("RP_ID") or derive_rp_id(rp_origin)

        self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path}"
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        self.LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILENAME = os.getenv("LOG_FILENAME", "app.log")
        self.LOG_MAX_KB = int(os.getenv("LOG_MAX_KB", "1024"))

        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.invalid")
