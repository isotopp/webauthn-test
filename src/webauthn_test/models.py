"""Database model definitions for identity, security, and audit state.

The module composes Flask-Security-compatible role/user/WebAuthn models with
application-specific fields (username, PII, credential version) and an
activity log table.

Constraints:
- table/field compatibility with Flask-Security mixins must be preserved
- WebAuthn credential storage must support verification replay protections
- audit rows remain query-friendly for the admin interface
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from flask_security import SQLAlchemyUserDatastore
from flask_security.models import fsqla_v3 as fsqla
from webauthn.helpers import bytes_to_base64url

from webauthn_test.extensions import db

fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):  # type: ignore[misc, type-arg, name-defined]
    __tablename__ = "role"


class User(db.Model, fsqla.FsUserMixin):  # type: ignore[misc, type-arg, name-defined]
    __tablename__ = "user"

    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False, default="")
    pii = db.Column(db.Text, nullable=False, default="")
    credential_version = db.Column(db.Integer, nullable=False, default=1)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)


class ActivityLog(db.Model):  # type: ignore[misc, type-arg, name-defined]
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    event = db.Column(db.String(64), nullable=False, index=True)
    detail = db.Column(db.Text, nullable=False, default="")
    ip_address = db.Column(db.String(64), nullable=False, default="")
    user_agent = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    user = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic"))


class WebAuthn(db.Model, fsqla.FsWebAuthnMixin):  # type: ignore[misc, type-arg, name-defined]
    __tablename__ = "webauthn"

    aaguid = db.Column(db.String(64), nullable=False, default="")
    credential_version = db.Column(db.Integer, nullable=False, default=1, index=True)
    lastuse_datetime = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )

    def credential_id_b64(self) -> str:
        return bytes_to_base64url(cast(bytes, self.credential_id))

    def transports_list(self) -> list[str]:
        transports = cast(list[str] | None, self.transports)
        if not transports:
            return []
        return [str(item) for item in transports]


Authenticator = WebAuthn


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
