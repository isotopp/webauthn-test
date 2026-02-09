from webauthn_test.app import create_app

__all__ = ["create_app"]


def main() -> None:
    print("Use `uv run flask --app webauthn_test.app:create_app ...`")
