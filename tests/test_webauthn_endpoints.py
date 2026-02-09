from __future__ import annotations

from dataclasses import dataclass

from webauthn.helpers import bytes_to_base64url

from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, Authenticator, User


@dataclass
class _FakeVerifiedRegistration:
    credential_id: bytes
    credential_public_key: bytes
    sign_count: int
    aaguid: str
    credential_device_type: object
    credential_backed_up: bool


@dataclass
class _FakeVerifiedAuthentication:
    new_sign_count: int


class _ValueWrap:
    def __init__(self, value: str) -> None:
        self.value = value


def test_webauthn_register_begin_sets_challenge(
    client, app, login, user_factory, monkeypatch
) -> None:
    user_id = user_factory(email="passkey-user@example.com", username="passkey-user")
    login("passkey-user@example.com", "Secretpass1!")

    def fake_begin_registration(**kwargs):
        return (
            {
                "challenge": "challenge-1",
                "user": {"id": "dXNlcg", "name": "passkey-user"},
                "rp": {"id": "webauthn.example.test", "name": "WebAuthn Test"},
            },
            "challenge-1",
        )

    monkeypatch.setattr(
        "webauthn_test.routes.begin_registration",
        fake_begin_registration,
    )
    response = client.post("/webauthn/register/begin")
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "challenge-1"

    with client.session_transaction() as session:
        assert session["webauthn_register_challenge"] == "challenge-1"
        assert session["webauthn_register_user_id"] == user_id


def test_webauthn_register_finish_persists_authenticator(
    client, app, login, user_factory, monkeypatch
) -> None:
    user_id = user_factory(email="passkey-reg@example.com", username="passkey-reg")
    login("passkey-reg@example.com", "Secretpass1!")

    verified = _FakeVerifiedRegistration(
        credential_id=b"cred-id-1",
        credential_public_key=b"public-key-1",
        sign_count=17,
        aaguid="aaguid-1",
        credential_device_type=_ValueWrap("single_device"),
        credential_backed_up=True,
    )

    monkeypatch.setattr(
        "webauthn_test.routes.finish_registration",
        lambda **kwargs: verified,
    )
    monkeypatch.setattr(
        "webauthn_test.routes.public_key_bytes_to_b64",
        lambda value: "credential-id-b64",
    )

    with client.session_transaction() as session:
        session["webauthn_register_challenge"] = "challenge-1"
        session["webauthn_register_user_id"] = user_id

    response = client.post(
        "/webauthn/register/finish",
        json={
            "id": "credential-id-b64",
            "response": {"transports": ["internal"]},
        },
    )
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    with app.app_context():
        authenticator = Authenticator.query.filter_by(
            user_id=user_id, credential_id=b"cred-id-1"
        ).first()
        assert authenticator is not None
        assert authenticator.sign_count == 17
        assert authenticator.public_key == b"public-key-1"
        assert (
            authenticator.credential_version
            == db.session.get(User, user_id).credential_version
        )
        event = ActivityLog.query.filter_by(
            user_id=user_id,
            event="webauthn_registered",
        ).first()
        assert event is not None


def test_webauthn_login_begin_requires_existing_authenticator(
    client, login, user_factory
) -> None:
    user_factory(email="no-passkey@example.com", username="no-passkey")
    response = client.post(
        "/webauthn/login/begin",
        json={"username": "no-passkey"},
    )
    assert response.status_code == 400


def test_webauthn_login_begin_rejects_stale_credential_version(
    client, app, user_factory
) -> None:
    user_id = user_factory(email="stale-passkey@example.com", username="stale-passkey")
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        db.session.add(
            Authenticator(
                user_id=user_id,
                credential_id=b"stale-credential",
                public_key=b"stale-public-key",
                sign_count=1,
                transports=["internal"],
                aaguid="aaguid-stale",
                device_type="single_device",
                backup_state=False,
                credential_version=1,
                name="stale-passkey",
                usage="first",
                extensions="",
            )
        )
        user.credential_version = 2
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/webauthn/login/begin",
        json={"username": "stale-passkey"},
    )
    assert response.status_code == 400


def test_webauthn_login_finish_logs_in_and_updates_counter(
    client, app, user_factory, monkeypatch
) -> None:
    user_id = user_factory(email="passkey-login@example.com", username="passkey-login")
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        auth = Authenticator(
            user_id=user_id,
            credential_id=b"credential-login",
            public_key=b"public-key-login",
            sign_count=3,
            transports=["internal"],
            aaguid="aaguid-login",
            device_type="single_device",
            backup_state=False,
            credential_version=user.credential_version,
            name="credential-login",
            usage="first",
            extensions="",
        )
        db.session.add(auth)
        db.session.commit()

    monkeypatch.setattr(
        "webauthn_test.routes.finish_authentication",
        lambda **kwargs: _FakeVerifiedAuthentication(new_sign_count=9),
    )

    with client.session_transaction() as session:
        session["webauthn_login_challenge"] = "challenge-login"
        session["webauthn_login_user_id"] = user_id

    response = client.post(
        "/webauthn/login/finish",
        json={"id": bytes_to_base64url(b"credential-login"), "response": {}},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["redirect"] == "/"

    with app.app_context():
        auth = Authenticator.query.filter_by(credential_id=b"credential-login").first()
        assert auth is not None
        assert auth.sign_count == 9
        assert auth.lastuse_datetime is not None
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.last_seen_at is not None
        event = ActivityLog.query.filter_by(
            user_id=user_id, event="webauthn_login"
        ).first()
        assert event is not None

    protected = client.get("/user/defaults")
    assert protected.status_code == 200
