from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user, logout_user, roles_required

from webauthn_test.activity import log_current_user_event, log_event
from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, User

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return render_template("index.html", username=current_user.username)
    return render_template("index.html", username=None)


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
            db.session.delete(user)
            db.session.commit()
            logout_user()
            flash("Account deleted.", "info")
            return redirect(url_for("main.index"))

        elif action == "logout":
            log_current_user_event("logout")
            logout_user()
            flash("Logged out.", "info")
            return redirect(url_for("main.index"))

        return redirect(url_for("main.user_defaults"))

    return render_template("user_defaults.html", user=current_user)


@bp.route("/admin", methods=["GET", "POST"])
@auth_required()
@roles_required("admin")
def admin_panel():
    if request.method == "POST":
        action = request.form.get("action", "")
        user_id = int(request.form.get("user_id", "0"))
        target = db.session.get(User, user_id)
        if not target:
            flash("User not found.", "error")
            return redirect(url_for("main.admin_panel"))

        if action == "delete_user":
            if target.id == current_user.id:
                flash("Cannot delete currently logged-in admin.", "error")
            else:
                username = target.username
                db.session.delete(target)
                db.session.commit()
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
