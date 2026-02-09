from __future__ import annotations

import secrets
from pathlib import Path

import click
from flask import Flask

from webauthn_test.env_registry import merged_env, parse_env_file, render_env_file


def generate_readable_password(groups: int = 4, group_len: int = 4) -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    chunks = []
    for _ in range(groups):
        chunks.append("".join(secrets.choice(alphabet) for _ in range(group_len)))
    return "-".join(chunks)


def register_cli(app: Flask) -> None:
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
    def init_admin(output_file: Path, force: bool) -> None:
        if output_file.exists() and not force:
            click.echo(f"{output_file} exists. Use --force to overwrite.")
            return

        username = "admin"
        password = generate_readable_password()
        output_file.write_text(f"{username}\n{password}\n", encoding="utf-8")
        click.echo(f"Wrote {output_file}")
