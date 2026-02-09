from __future__ import annotations

from datetime import UTC, datetime

from flask_security import SQLAlchemyUserDatastore
from flask_security.models import fsqla_v3 as fsqla

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
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True, index=True
    )
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


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
