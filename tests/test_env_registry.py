from pathlib import Path

import pytest

from webauthn_test.env_registry import derive_rp_id, merged_env, parse_env_file


def test_derive_rp_id() -> None:
    assert (
        derive_rp_id("https://webauthn.home.koehntopp.de")
        == "webauthn.home.koehntopp.de"
    )


def test_merge_env_derives_rp_id() -> None:
    merged = merged_env({}, {"RP_ORIGIN": "https://example.com", "RP_NAME": "Demo"})
    assert merged["RP_ID"] == "example.com"
    assert "SECRET_KEY" in merged
    assert "SECURITY_PASSWORD_SALT" in merged


def test_parse_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nRP_ORIGIN=https://example.com\nRP_NAME=Demo\n",
        encoding="utf-8",
    )
    parsed = parse_env_file(env_file)
    assert parsed["RP_ORIGIN"] == "https://example.com"
    assert parsed["RP_NAME"] == "Demo"


def test_derive_rp_id_invalid() -> None:
    with pytest.raises(ValueError):
        derive_rp_id("not-a-url")
