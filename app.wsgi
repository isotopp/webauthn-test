"""mod_wsgi entrypoint for Apache daemon-mode deployments.

This file allows Apache `WSGIScriptAlias` setups to load the Flask app directly
without a separate reverse-proxy backend port. It is intended for deployments
where Apache handles TLS and process management via `WSGIDaemonProcess`.
"""

from pathlib import Path
import sys

# Ensure src-layout packages are importable in Apache/mod_wsgi daemon mode.
APP_DIR = Path(__file__).resolve().parent
SRC_DIR = APP_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from webauthn_test.app import create_app

application = create_app()
