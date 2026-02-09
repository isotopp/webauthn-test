from __future__ import annotations

from pathlib import Path

from webauthn_test.env_registry import parse_env_file


def test_init_env_completes_existing_file_and_preserves_values(
    app, tmp_path: Path
) -> None:
    runner = app.test_cli_runner()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "RP_ORIGIN=https://custom.example.com\nRP_NAME=Custom Name\nSECRET_KEY=kept-secret\n",
        encoding="utf-8",
    )

    result = runner.invoke(args=["init-env", "--env-file", str(env_file)])
    assert result.exit_code == 0
    values = parse_env_file(env_file)

    assert values["RP_ORIGIN"] == "https://custom.example.com"
    assert values["RP_NAME"] == "Custom Name"
    assert values["RP_ID"] == "custom.example.com"
    assert values["SECRET_KEY"] == "kept-secret"
    assert values["DATABASE_PATH"] == "resources/app.sqlite3"
    assert values["LOG_DIR"] == "logs"


def test_init_env_rp_origin_override_rederives_rp_id(app, tmp_path: Path) -> None:
    runner = app.test_cli_runner()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "RP_ORIGIN=https://before.example.com\nRP_NAME=Before\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        args=[
            "init-env",
            "--env-file",
            str(env_file),
            "--rp-origin",
            "https://after.example.com",
            "--rp-name",
            "After",
        ]
    )
    assert result.exit_code == 0

    values = parse_env_file(env_file)
    assert values["RP_ORIGIN"] == "https://after.example.com"
    assert values["RP_NAME"] == "After"
    assert values["RP_ID"] == "after.example.com"
