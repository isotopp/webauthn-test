from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from flask_security.utils import hash_password

from webauthn_test.app import create_app
from webauthn_test.extensions import db
from webauthn_test.models import user_datastore


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RP_ORIGIN", "https://webauthn.example.com")
    monkeypatch.setenv("RP_NAME", "WebAuthn Test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SECURITY_PASSWORD_SALT", "test-salt")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")

    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECURITY_CSRF_PROTECT_MECHANISMS": [],
            "SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL": False,
            "SECURITY_EMAIL_VALIDATOR_ARGS": {"check_deliverability": False},
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def user_factory(app) -> Callable[..., int]:
    def _create_user(
        *,
        email: str,
        username: str,
        password: str = "Secretpass1!",
        admin: bool = False,
    ) -> int:
        with app.app_context():
            user = user_datastore.create_user(
                email=email,
                username=username,
                password=hash_password(password),
                active=True,
                full_name="",
                pii="",
            )
            if admin:
                role = user_datastore.find_role("admin")
                if not role:
                    role = user_datastore.create_role(name="admin")
                user_datastore.add_role_to_user(user, role)
            db.session.commit()
            return int(user.id)

    return _create_user


@pytest.fixture
def login(client: FlaskClient) -> Callable[[str, str], None]:
    def _login(email: str, password: str) -> None:
        response = client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"hello," in response.data

    return _login
