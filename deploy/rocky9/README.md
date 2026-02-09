# Rocky Linux 9 Deployment Notes

This directory contains deployment templates for running `webauthn-test` as
user `webauthn:webauthn` on Rocky Linux 9 with Apache TLS termination.

## Assumptions

- OS: Rocky Linux 9
- Process user: `webauthn:webauthn`
- Canonical app path: `/home/webauthn/webauth`
- Canonical external origin: `https://webauthn.home.koehntopp.de`
- Apache TLS automation via mod_md (or equivalent)

## Install baseline packages

For Apache + mod_wsgi deployment:

```bash
sudo dnf install -y httpd mod_ssl mod_wsgi mod_macro
```

For Apache reverse proxy to uWSGI HTTP backend, also install `uwsgi`.

## Application location

Deploy the repository to:
- `/home/webauthn/webauth`

Ensure ownership:

```bash
sudo chown -R webauthn:webauthn /home/webauthn/webauth
```

## Application bootstrap

Run as `webauthn` in `/home/webauthn/webauth`:

```bash
uv sync
uv run flask --app webauthn_test.app:create_app init-env
uv run flask --app webauthn_test.app:create_app db upgrade
uv run flask --app webauthn_test.app:create_app init-admin
```

## SMTP/IMAPS config in `.env`

Set at least:
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`, `SECURITY_EMAIL_SENDER`

Optional ops-reference fields (not used by app runtime):
- `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`, `IMAP_PASSWORD`

## Apache + mod_wsgi (recommended for your current setup)

Use:
- `app.wsgi` at repository root
- `deploy/rocky9/apache-macro-mod_wsgi.conf` as a macro template

Important details:
- use `python-home=$appdir/.venv` (uv creates `.venv`)
- no backend localhost port is required in this mode
- mod_md (or your existing TLS automation) handles certificate lifecycle

Install config and reload Apache:

```bash
sudo cp deploy/rocky9/apache-macro-mod_wsgi.conf /etc/httpd/conf.sites.d/webauthn.home.koehntopp.de.conf
sudo apachectl configtest
sudo systemctl reload httpd
```

## Apache reverse proxy + uWSGI backend (optional alternative)

If you prefer a separate service with `127.0.0.1:8080` backend:
- `deploy/rocky9/webauthn.service`
- `deploy/rocky9/uwsgi.ini`
- `deploy/rocky9/apache-vhost.conf`

## Update procedure

```bash
cd /home/webauthn/webauth
git pull
uv sync
uv run flask --app webauthn_test.app:create_app db upgrade
uv run pytest
# For mod_wsgi mode:
sudo systemctl reload httpd
# For uWSGI backend mode:
# sudo systemctl restart webauthn.service
```
