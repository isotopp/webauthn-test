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
        load_dotenv()

        rp_origin = os.getenv("RP_ORIGIN", "https://example.invalid")
        rp_name = os.getenv("RP_NAME", "WebAuthn Demo")

        database_path = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))
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
        self.MAIL_SUPPRESS_SEND = True

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
