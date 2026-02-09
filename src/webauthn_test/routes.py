"""HTTP routes for user flows, admin actions, and WebAuthn ceremonies.

This blueprint contains:
- user-facing pages and account mutation actions
- admin management actions with role-gated authorization
- JSON endpoints for WebAuthn registration and login begin/finish steps

Constraints:
- state-changing paths must enforce authentication/authorization boundaries
- WebAuthn challenge state is bound to server-side session context
- security-relevant mutations write audit events
"""

from __future__ import annotations
from datetime import UTC, datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_user
from flask_security import auth_required, current_user, logout_user, roles_required

from webauthn_test.activity import log_current_user_event, log_event
from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, Authenticator, User
from webauthn_test.webauthn_service import (
    begin_authentication,
    begin_registration,
    credential_id_bytes_from_payload,
    finish_authentication,
    finish_registration,
    public_key_bytes_to_b64,
)

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return render_template("index.html", username=current_user.username)
    return render_template("index.html", username=None)


def _delete_user_with_related_records(user: User) -> None:
    ActivityLog.query.filter_by(user_id=user.id).update({"user_id": None})
    Authenticator.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()


@bp.route("/user/defaults", methods=["GET", "POST"])
@auth_required()
def user_defaults():
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "change_username":
            new_username = request.form.get("username", "").strip()
            if not new_username:
                flash("Username cannot be empty.", "error")
            elif User.query.filter(
                User.username == new_username, User.id != current_user.id
            ).first():
                flash("Username already exists.", "error")
            else:
                current_user.username = new_username
                db.session.add(current_user)
                db.session.commit()
                log_current_user_event("username_changed", f"username={new_username}")
                flash("Username updated.", "info")

        elif action == "edit_pii":
            full_name = request.form.get("full_name", "").strip()
            pii = request.form.get("pii", "").strip()
            current_user.full_name = full_name
            current_user.pii = pii
            db.session.add(current_user)
            db.session.commit()
            log_current_user_event("pii_updated")
            flash("Profile updated.", "info")

        elif action == "regen_credentials":
            current_user.credential_version = int(current_user.credential_version) + 1
            db.session.add(current_user)
            db.session.commit()
            log_current_user_event(
                "credentials_regenerated",
                f"credential_version={current_user.credential_version}",
            )
            flash("Credential version incremented.", "info")

        elif action == "delete_account":
            user = db.session.get(User, current_user.id)
            if not user:
                flash("User not found.", "error")
                return redirect(url_for("main.user_defaults"))
            username = user.username
            log_event(event="account_deleted", user=user, detail=f"username={username}")
            _delete_user_with_related_records(user)
            logout_user()
            flash("Account deleted.", "info")
            return redirect(url_for("main.index"))

        elif action == "logout":
            log_current_user_event("logout")
            logout_user()
            flash("Logged out.", "info")
            return redirect(url_for("main.index"))

        return redirect(url_for("main.user_defaults"))

    authenticators = (
        Authenticator.query.filter_by(
            user_id=current_user.id, credential_version=current_user.credential_version
        )
        .order_by(Authenticator.create_datetime.asc())
        .all()
    )
    return render_template(
        "user_defaults.html",
        user=current_user,
        authenticators=authenticators,
    )


@bp.post("/webauthn/register/begin")
@auth_required()
def webauthn_register_begin():
    user = db.session.get(User, current_user.id)
    if not user:
        return {"error": "User not found."}, 404

    existing = (
        Authenticator.query.filter_by(
            user_id=user.id,
            credential_version=user.credential_version,
        )
        .order_by(Authenticator.id.asc())
        .all()
    )
    options, challenge = begin_registration(
        user=user,
        rp_id=current_app.config["RP_ID"],
        rp_name=current_app.config["RP_NAME"],
        exclude_authenticators=existing,
    )
    session["webauthn_register_challenge"] = challenge
    session["webauthn_register_user_id"] = user.id
    return options, 200


@bp.post("/webauthn/register/finish")
@auth_required()
def webauthn_register_finish():
    user = db.session.get(User, current_user.id)
    if not user:
        return {"error": "User not found."}, 404

    challenge = session.get("webauthn_register_challenge")
    session_user_id = session.get("webauthn_register_user_id")
    if not isinstance(challenge, str) or session_user_id != user.id:
        return {"error": "Registration challenge missing or mismatched."}, 400

    credential = request.get_json(silent=True)
    if not isinstance(credential, dict):
        return {"error": "Invalid credential payload."}, 400

    verified = finish_registration(
        credential=credential,
        expected_challenge=challenge,
        rp_id=current_app.config["RP_ID"],
        origin=current_app.config["RP_ORIGIN"],
    )

    credential_id_b64 = public_key_bytes_to_b64(verified.credential_id)
    if Authenticator.query.filter_by(credential_id=verified.credential_id).first():
        return {"error": "Credential already exists."}, 400

    raw_response = credential.get("response", {})
    transports: list[str] = []
    if isinstance(raw_response, dict):
        raw_transports = raw_response.get("transports", [])
        if isinstance(raw_transports, list):
            transports = [str(item) for item in raw_transports]

    authenticator = Authenticator(
        user_id=user.id,
        credential_id=verified.credential_id,
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        transports=transports,
        aaguid=verified.aaguid,
        device_type=str(verified.credential_device_type.value),
        backup_state=bool(verified.credential_backed_up),
        credential_version=user.credential_version,
        name=f"{user.username}-{credential_id_b64[:8]}",
        usage="first",
        extensions="",
        lastuse_datetime=datetime.now(UTC),
    )
    db.session.add(authenticator)
    db.session.commit()

    session.pop("webauthn_register_challenge", None)
    session.pop("webauthn_register_user_id", None)
    log_current_user_event("webauthn_registered", f"credential_id={credential_id_b64}")
    return {"ok": True}, 200


@bp.post("/webauthn/login/begin")
def webauthn_login_begin():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "Invalid request body."}, 400
    username = str(payload.get("username", "")).strip()
    if not username:
        return {"error": "username is required."}, 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return {"error": "Unknown user."}, 404

    authenticators = (
        Authenticator.query.filter_by(
            user_id=user.id,
            credential_version=user.credential_version,
        )
        .order_by(Authenticator.id.asc())
        .all()
    )
    if not authenticators:
        return {"error": "No active passkeys for this user."}, 400

    options, challenge = begin_authentication(
        rp_id=current_app.config["RP_ID"],
        allow_authenticators=authenticators,
    )
    session["webauthn_login_challenge"] = challenge
    session["webauthn_login_user_id"] = user.id
    return options, 200


@bp.post("/webauthn/login/finish")
def webauthn_login_finish():
    credential = request.get_json(silent=True)
    if not isinstance(credential, dict):
        return {"error": "Invalid credential payload."}, 400

    challenge = session.get("webauthn_login_challenge")
    user_id = session.get("webauthn_login_user_id")
    if not isinstance(challenge, str) or not isinstance(user_id, int):
        return {"error": "Login challenge missing."}, 400

    user = db.session.get(User, user_id)
    if not user:
        return {"error": "User not found."}, 404

    try:
        credential_id = credential_id_bytes_from_payload(credential)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    authenticator = Authenticator.query.filter_by(
        user_id=user.id,
        credential_id=credential_id,
        credential_version=user.credential_version,
    ).first()
    if not authenticator:
        return {"error": "Unknown credential."}, 404

    verified = finish_authentication(
        credential=credential,
        expected_challenge=challenge,
        rp_id=current_app.config["RP_ID"],
        origin=current_app.config["RP_ORIGIN"],
        credential_public_key=authenticator.public_key,
        credential_current_sign_count=authenticator.sign_count,
    )

    authenticator.sign_count = verified.new_sign_count
    authenticator.lastuse_datetime = datetime.now(UTC)
    user.last_seen_at = datetime.now(UTC)
    db.session.add(authenticator)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    session.pop("webauthn_login_challenge", None)
    session.pop("webauthn_login_user_id", None)
    credential_id_b64 = public_key_bytes_to_b64(credential_id)
    log_event(
        event="webauthn_login", user=user, detail=f"credential_id={credential_id_b64}"
    )
    return {"ok": True, "redirect": url_for("main.index")}, 200


@bp.route("/admin", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def admin_panel():
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            user_id = int(request.form.get("user_id", "0"))
        except ValueError:
            flash("Invalid user id.", "error")
            return redirect(url_for("main.admin_panel"))
        target = db.session.get(User, user_id)
        if not target:
            flash("User not found.", "error")
            return redirect(url_for("main.admin_panel"))

        if action == "delete_user":
            if target.id == current_user.id:
                flash("Cannot delete currently logged-in admin.", "error")
            else:
                username = target.username
                _delete_user_with_related_records(target)
                log_current_user_event("admin_deleted_user", f"username={username}")
                flash("User deleted.", "info")

        elif action == "edit_user":
            target.username = (
                request.form.get("username", target.username).strip() or target.username
            )
            target.full_name = request.form.get("full_name", target.full_name).strip()
            target.pii = request.form.get("pii", target.pii).strip()
            db.session.add(target)
            db.session.commit()
            log_current_user_event("admin_edited_user", f"user_id={target.id}")
            flash("User updated.", "info")

        return redirect(url_for("main.admin_panel"))

    users = User.query.order_by(User.id.asc()).all()
    activities = (
        ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    )
    return render_template("admin.html", users=users, activities=activities)
