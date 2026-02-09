"""Public package entry points for the webauthn-test application.

This module stays intentionally small and stable: it exports the Flask
application factory used by runtime and tooling, and provides a minimal CLI
hint for humans invoking the package script directly.

Constraints:
- avoid initialization side effects at import time
- keep import graph shallow so app discovery remains predictable
- expose only high-level entry points, not internal implementation details
"""

from webauthn_test.app import create_app

__all__ = ["create_app"]


def main() -> None:
    print("Use `uv run flask --app webauthn_test.app:create_app ...`")
