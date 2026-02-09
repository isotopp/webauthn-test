from __future__ import annotations

from flask_security.recoverable import generate_reset_password_token
from flask_security.utils import verify_password

from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, User


def test_register_creates_user_with_hashed_password(client, app) -> None:
    response = client.post(
        "/auth/register",
        data={
            "email": "new-user@example.com",
            "username": "new-user",
            "password": "Secretpass1!",
            "password_confirm": "Secretpass1!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="new-user@example.com").first()
        assert user is not None
        assert user.username == "new-user"
        assert user.password != "Secretpass1!"
        assert verify_password("Secretpass1!", user.password)


def test_login_updates_last_seen_and_creates_activity(
    client, app, user_factory
) -> None:
    user_id = user_factory(
        email="login-user@example.com",
        username="login-user",
        password="Secretpass1!",
    )

    response = client.post(
        "/auth/login",
        data={"email": "login-user@example.com", "password": "Secretpass1!"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.last_seen_at is not None
        event = (
            ActivityLog.query.filter_by(user_id=user_id, event="user_login")
            .order_by(ActivityLog.id.desc())
            .first()
        )
        assert event is not None


def test_password_reset_changes_password_and_logs_event(
    client, app, user_factory
) -> None:
    user_id = user_factory(
        email="reset-user@example.com",
        username="reset-user",
        password="Oldsecret1!",
    )

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        token = generate_reset_password_token(user)

    response = client.post(
        f"/auth/reset/{token}",
        data={"password": "Newsecret1!", "password_confirm": "Newsecret1!"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert verify_password("Newsecret1!", user.password)
        assert not verify_password("Oldsecret1!", user.password)
        event = (
            ActivityLog.query.filter_by(user_id=user_id, event="password_reset")
            .order_by(ActivityLog.id.desc())
            .first()
        )
        assert event is not None
