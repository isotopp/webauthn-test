from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from webauthn_test.cli import register_cli
from webauthn_test.config import Config
from webauthn_test.extensions import db, migrate
from webauthn_test.logging_utils import configure_logging


def create_app() -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[assignment]
    app.config.from_object(Config())

    db.init_app(app)
    migrate.init_app(app, db)
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
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def index():
        return jsonify({"message": "hello, {username}"}), 200

    return app
