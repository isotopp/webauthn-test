from webauthn_test.cli import generate_readable_password


def test_generate_readable_password_shape() -> None:
    password = generate_readable_password()
    chunks = password.split("-")
    assert len(chunks) == 4
    assert all(len(chunk) == 4 for chunk in chunks)
