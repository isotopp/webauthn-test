"""mod_wsgi entrypoint for Apache daemon-mode deployments.

This file allows Apache `WSGIScriptAlias` setups to load the Flask app directly
without a separate reverse-proxy backend port. It is intended for deployments
where Apache handles TLS and process management via `WSGIDaemonProcess`.
"""

from webauthn_test.app import create_app

application = create_app()
