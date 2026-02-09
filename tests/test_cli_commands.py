from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from webauthn_test.extensions import db
from webauthn_test.models import User


def test_init_db_creates_expected_tables(app) -> None:
    runner = app.test_cli_runner()
    result = runner.invoke(args=["init-db"])
    assert result.exit_code == 0

    with app.app_context():
        table_names = set(inspect(db.engine).get_table_names())
    assert {
        "user",
        "role",
        "roles_users",
        "activity_logs",
        "webauthn",
    }.issubset(table_names)


def test_init_admin_provisions_db_and_writes_file(app, tmp_path: Path) -> None:
    runner = app.test_cli_runner()
    admin_file = tmp_path / ".admin"

    result = runner.invoke(
        args=["init-admin", "--output-file", str(admin_file), "--force"]
    )
    assert result.exit_code == 0
    assert admin_file.exists()

    lines = admin_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0] == "admin"
    plain_password = lines[1]

    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        assert admin is not None
        assert admin.password != plain_password
        assert admin.has_role("admin")


def test_init_admin_no_provision_only_writes_file(app, tmp_path: Path) -> None:
    runner = app.test_cli_runner()
    admin_file = tmp_path / ".admin"

    result = runner.invoke(
        args=[
            "init-admin",
            "--output-file",
            str(admin_file),
            "--force",
            "--no-provision-db",
        ]
    )
    assert result.exit_code == 0
    assert admin_file.exists()

    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        assert admin is None


def test_init_admin_without_force_preserves_existing_file(app, tmp_path: Path) -> None:
    runner = app.test_cli_runner()
    admin_file = tmp_path / ".admin"
    admin_file.write_text("admin\nfixed-password\n", encoding="utf-8")

    result = runner.invoke(args=["init-admin", "--output-file", str(admin_file)])
    assert result.exit_code == 0
    assert "exists. Use --force to overwrite." in result.output
    assert admin_file.read_text(encoding="utf-8") == "admin\nfixed-password\n"
