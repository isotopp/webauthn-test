"""Application factory and top-level integration wiring.

This module composes the runtime system: configuration loading, extension
initialization, blueprint registration, security integration, CLI command
registration, proxy-awareness, and log setup.

Design intent:
- centralize cross-cutting initialization in one place
- support deterministic test setup via optional test config injection
- keep route/business concerns out of factory code
"""

from __future__ import annotations

from collections.abc import Mapping

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from webauthn_test.activity import register_activity_signals
from webauthn_test.cli import register_cli
from webauthn_test.config import Config
from webauthn_test.extensions import db, mail, migrate, security
from webauthn_test.forms import ExtendedRegisterForm
from webauthn_test.logging_utils import configure_logging
from webauthn_test.models import user_datastore
from webauthn_test.routes import bp as main_bp


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[assignment]
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)
    app.config["SECURITY_REGISTER_FORM"] = ExtendedRegisterForm
    app.config["SECURITY_FORM_REGISTER"] = ExtendedRegisterForm

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    security.init_app(app, user_datastore)
    app.register_blueprint(main_bp)
    register_activity_signals(app)
    register_cli(app)

    configure_logging(
        app_name=app.name,
        log_dir=app.config["LOG_DIR"],
        log_filename=app.config["LOG_FILENAME"],
        log_level=app.config["LOG_LEVEL"],
        log_max_kb=app.config["LOG_MAX_KB"],
    )

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
