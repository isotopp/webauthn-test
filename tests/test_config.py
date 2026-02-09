from pathlib import Path

from webauthn_test.config import BASE_DIR, Config


def test_relative_database_path_resolves_from_base_dir(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RP_ORIGIN", "https://webauthn.home.koehntopp.de")
    monkeypatch.setenv("RP_NAME", "WebAuthn Demo")
    monkeypatch.setenv("DATABASE_PATH", "resources/test-db.sqlite3")

    config = Config()
    expected = Path(BASE_DIR) / "resources" / "test-db.sqlite3"
    assert config.SQLALCHEMY_DATABASE_URI == f"sqlite:///{expected}"
