"""Flask CLI commands for environment, schema, and bootstrap operations.

This module defines operational commands that make first-run and update flows
repeatable: environment file initialization, schema creation, and admin
credential provisioning.

Constraints:
- commands are idempotent where practical
- generated admin credentials are human-readable for bootstrap usage
- DB provisioning and filesystem side effects are explicit and testable
"""

from __future__ import annotations

import secrets
from pathlib import Path

import click
from flask import Flask
from flask_security.utils import hash_password

from webauthn_test.activity import log_event
from webauthn_test.env_registry import merged_env, parse_env_file, render_env_file
from webauthn_test.extensions import db
from webauthn_test.models import User, user_datastore


def generate_readable_password(groups: int = 4, group_len: int = 4) -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    chunks = []
    for _ in range(groups):
        chunks.append("".join(secrets.choice(alphabet) for _ in range(group_len)))
    return "-".join(chunks)


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        db.create_all()
        click.echo("Initialized database tables.")

    @app.cli.command("init-env")
    @click.option("--rp-origin", type=str, help="External canonical origin.")
    @click.option("--rp-name", type=str, help="WebAuthn relying party display name.")
    @click.option(
        "--env-file",
        type=click.Path(path_type=Path),
        default=Path(".env"),
        show_default=True,
    )
    def init_env(rp_origin: str | None, rp_name: str | None, env_file: Path) -> None:
        existing = parse_env_file(env_file)
        supplied = {"RP_ORIGIN": rp_origin or "", "RP_NAME": rp_name or ""}

        if not existing.get("RP_ORIGIN") and not supplied["RP_ORIGIN"]:
            supplied["RP_ORIGIN"] = click.prompt(
                "RP_ORIGIN",
                default="https://webauthn.home.koehntopp.de",
                show_default=True,
            )
        if not existing.get("RP_NAME") and not supplied["RP_NAME"]:
            supplied["RP_NAME"] = click.prompt(
                "RP_NAME", default="WebAuthn Demo", show_default=True
            )

        merged = merged_env(existing, supplied)
        env_file.write_text(render_env_file(merged), encoding="utf-8")
        click.echo(f"Wrote {env_file}")

    @app.cli.command("init-admin")
    @click.option(
        "--output-file",
        type=click.Path(path_type=Path),
        default=Path(".admin"),
        show_default=True,
    )
    @click.option("--force", is_flag=True, help="Overwrite existing .admin file.")
    @click.option(
        "--provision-db/--no-provision-db",
        default=True,
        show_default=True,
        help="Create or update the admin role/user in the database.",
    )
    def init_admin(output_file: Path, force: bool, provision_db: bool) -> None:
        if output_file.exists() and not force:
            click.echo(f"{output_file} exists. Use --force to overwrite.")
            return

        username = "admin"
        password = generate_readable_password()
        output_file.write_text(f"{username}\n{password}\n", encoding="utf-8")
        click.echo(f"Wrote {output_file}")

        if not provision_db:
            return

        db.create_all()

        admin_role = user_datastore.find_role("admin")
        if not admin_role:
            admin_role = user_datastore.create_role(name="admin")

        admin = user_datastore.find_user(username=username)
        if not admin:
            admin_email = app.config["ADMIN_EMAIL"]
            admin = user_datastore.create_user(
                email=admin_email,
                username=username,
                password=hash_password(password),
                active=True,
                full_name="Administrator",
                pii="",
            )
        else:
            admin.password = hash_password(password)

        if isinstance(admin, User) and not admin.has_role("admin"):
            user_datastore.add_role_to_user(admin, admin_role)

        db.session.commit()
        click.echo("Provisioned admin role/user in database.")

    @app.cli.command("set-pass")
    @click.argument("username", type=str)
    @click.argument("password", type=str)
    def set_pass(username: str, password: str) -> None:
        user = user_datastore.find_user(username=username)
        if not user:
            msg = f"User '{username}' not found."
            raise click.ClickException(msg)

        user.password = hash_password(password)
        db.session.add(user)
        db.session.commit()
        log_event(event="password_set_by_cli", user=user, detail=f"username={username}")
        click.echo(f"Updated password for '{username}'.")
