"""Security and audit activity logging utilities.

This module records authentication and account-management events into the
activity log table and connects selected Flask-Security signals to persistent
audit entries.

Constraints and structure:
- log writes are synchronous and explicit (commit-per-event) for traceability
- request metadata is captured opportunistically without breaking if absent
- event schema is intentionally simple for admin-facing inspection
"""

from __future__ import annotations

from flask import Flask, Request, request
from flask_security import current_user
from flask_security.signals import (
    password_reset,
    user_authenticated,
    user_registered,
)

from webauthn_test.extensions import db
from webauthn_test.models import ActivityLog, User


def _request_value(req: Request | None, name: str, fallback: str = "") -> str:
    if req is None:
        return fallback
    value = req.headers.get(name, fallback)
    return str(value)


def log_event(
    *,
    event: str,
    user: User | None = None,
    detail: str = "",
    req: Request | None = None,
) -> None:
    entry = ActivityLog(
        event=event,
        user_id=user.id if user else None,
        detail=detail,
        ip_address=_request_value(
            req, "X-Forwarded-For", req.remote_addr or "" if req else ""
        ),
        user_agent=_request_value(req, "User-Agent"),
    )
    db.session.add(entry)
    db.session.commit()


def register_activity_signals(app: Flask) -> None:
    @user_registered.connect_via(app)
    def _on_user_registered(sender, user, **extra):  # type: ignore[no-untyped-def]
        log_event(event="user_registered", user=user, req=request)

    @user_authenticated.connect_via(app)
    def _on_user_authenticated(sender, user, authn_via, **extra):  # type: ignore[no-untyped-def]
        user.last_seen_at = db.func.now()
        db.session.add(user)
        db.session.commit()
        log_event(event="user_login", user=user, detail=f"via={authn_via}", req=request)

    @password_reset.connect_via(app)
    def _on_password_reset(sender, user, **extra):  # type: ignore[no-untyped-def]
        log_event(event="password_reset", user=user, req=request)


def log_current_user_event(event: str, detail: str = "") -> None:
    user = current_user if current_user.is_authenticated else None
    log_event(event=event, user=user, detail=detail, req=request)
