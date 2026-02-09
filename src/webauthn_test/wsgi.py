"""WSGI entrypoint for production process managers.

This module exists so servers such as uWSGI can import a stable module-level
`app` object without running CLI-only paths.
"""

from webauthn_test.app import create_app

app = create_app()
