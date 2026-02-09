from __future__ import annotations

from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, User


def test_user_defaults_requires_auth(client) -> None:
    response = client.get("/user/defaults")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_admin_requires_admin_role(client, login, user_factory) -> None:
    user_factory(
        email="normal@example.com",
        username="normal-user",
    )
    login("normal@example.com", "Secretpass1!")
    response = client.get("/admin")
    assert response.status_code in {302, 403}


def test_change_username_mutates_and_logs(client, app, login, user_factory) -> None:
    user_id = user_factory(email="u1@example.com", username="before-name")
    login("u1@example.com", "Secretpass1!")

    response = client.post(
        "/user/defaults",
        data={"action": "change_username", "username": "after-name"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.username == "after-name"
        event = ActivityLog.query.filter_by(
            user_id=user_id, event="username_changed"
        ).first()
        assert event is not None


def test_change_username_duplicate_does_not_mutate(
    client, app, login, user_factory
) -> None:
    user_id = user_factory(email="u2@example.com", username="first-user")
    user_factory(email="u3@example.com", username="taken-name")
    login("u2@example.com", "Secretpass1!")

    response = client.post(
        "/user/defaults",
        data={"action": "change_username", "username": "taken-name"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.username == "first-user"
        events = ActivityLog.query.filter_by(
            user_id=user_id, event="username_changed"
        ).all()
        assert events == []


def test_edit_pii_mutates_and_logs(client, app, login, user_factory) -> None:
    user_id = user_factory(email="u4@example.com", username="pii-user")
    login("u4@example.com", "Secretpass1!")

    response = client.post(
        "/user/defaults",
        data={"action": "edit_pii", "full_name": "Alice Demo", "pii": "demo pii"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.full_name == "Alice Demo"
        assert user.pii == "demo pii"
        event = ActivityLog.query.filter_by(
            user_id=user_id, event="pii_updated"
        ).first()
        assert event is not None


def test_regen_credentials_increments_and_logs(
    client, app, login, user_factory
) -> None:
    user_id = user_factory(email="u5@example.com", username="cred-user")
    login("u5@example.com", "Secretpass1!")

    with app.app_context():
        before = db.session.get(User, user_id)
        assert before is not None
        before_version = int(before.credential_version)

    response = client.post(
        "/user/defaults",
        data={"action": "regen_credentials"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert int(user.credential_version) == before_version + 1
        event = ActivityLog.query.filter_by(
            user_id=user_id, event="credentials_regenerated"
        ).first()
        assert event is not None


def test_delete_account_deletes_user_logs_and_logs_out(
    client, app, login, user_factory
) -> None:
    user_id = user_factory(email="u6@example.com", username="delete-me")
    login("u6@example.com", "Secretpass1!")

    response = client.post(
        "/user/defaults",
        data={"action": "delete_account"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is None
        event = ActivityLog.query.filter_by(event="account_deleted").first()
        assert event is not None

    protected = client.get("/user/defaults")
    assert protected.status_code == 302
    assert "/auth/login" in protected.headers["Location"]


def test_admin_edit_user_mutates_and_logs(client, app, login, user_factory) -> None:
    admin_id = user_factory(
        email="admin1@example.com",
        username="admin-1",
        admin=True,
    )
    target_id = user_factory(email="target1@example.com", username="target-before")
    login("admin1@example.com", "Secretpass1!")

    response = client.post(
        "/admin",
        data={
            "action": "edit_user",
            "user_id": str(target_id),
            "username": "target-after",
            "full_name": "Target User",
            "pii": "edited",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        target = db.session.get(User, target_id)
        assert target is not None
        assert target.username == "target-after"
        assert target.full_name == "Target User"
        assert target.pii == "edited"
        event = ActivityLog.query.filter_by(
            user_id=admin_id, event="admin_edited_user"
        ).first()
        assert event is not None


def test_admin_delete_user_mutates_and_logs(client, app, login, user_factory) -> None:
    admin_id = user_factory(
        email="admin2@example.com",
        username="admin-2",
        admin=True,
    )
    target_id = user_factory(email="target2@example.com", username="target-delete")
    login("admin2@example.com", "Secretpass1!")

    response = client.post(
        "/admin",
        data={"action": "delete_user", "user_id": str(target_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        target = db.session.get(User, target_id)
        assert target is None
        event = ActivityLog.query.filter_by(
            user_id=admin_id, event="admin_deleted_user"
        ).first()
        assert event is not None


def test_admin_cannot_delete_self(client, app, login, user_factory) -> None:
    admin_id = user_factory(
        email="admin3@example.com",
        username="admin-3",
        admin=True,
    )
    login("admin3@example.com", "Secretpass1!")

    response = client.post(
        "/admin",
        data={"action": "delete_user", "user_id": str(admin_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        admin = db.session.get(User, admin_id)
        assert admin is not None
        events = ActivityLog.query.filter_by(
            user_id=admin_id, event="admin_deleted_user"
        ).all()
        assert events == []


def test_admin_invalid_user_id_returns_clean_response(
    client, login, user_factory
) -> None:
    user_factory(
        email="admin4@example.com",
        username="admin-4",
        admin=True,
    )
    login("admin4@example.com", "Secretpass1!")

    response = client.post(
        "/admin",
        data={"action": "edit_user", "user_id": "not-an-int"},
        follow_redirects=True,
    )
    assert response.status_code == 200
