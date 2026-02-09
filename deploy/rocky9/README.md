# Rocky Linux 9 Deployment Notes

This directory contains deployment templates for running `webauthn-test` as
user `webauthn:webauthn` behind Apache TLS termination.

## Assumptions

- OS: Rocky Linux 9
- Process user: `webauthn:webauthn`
- Reverse proxy: Apache on `:443`
- App backend: uWSGI HTTP socket on `127.0.0.1:8080`
- Canonical external origin: `https://webauthn.home.koehntopp.de`

## Install baseline packages

```bash
sudo dnf install -y httpd mod_ssl uwsgi
```

(If your uWSGI package split requires python plugin packages, install those as
well according to your repository policy.)

## Application location

Deploy the repository to:
- `/opt/webauthn-test/current`

Ensure ownership:

```bash
sudo chown -R webauthn:webauthn /opt/webauthn-test
```

## Application bootstrap

Run as `webauthn` in `/opt/webauthn-test/current`:

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

## systemd

Install service file:

```bash
sudo cp deploy/rocky9/webauthn.service /etc/systemd/system/webauthn.service
sudo systemctl daemon-reload
sudo systemctl enable --now webauthn.service
sudo systemctl status webauthn.service
```

## Apache

Install vhost template and reload Apache:

```bash
sudo cp deploy/rocky9/apache-vhost.conf /etc/httpd/conf.d/webauthn.conf
sudo apachectl configtest
sudo systemctl reload httpd
```

## uWSGI config

Template is provided at:
- `deploy/rocky9/uwsgi.ini`

Adjust process/thread counts to host sizing if needed.

## Update procedure

```bash
cd /opt/webauthn-test/current
git pull
uv sync
uv run flask --app webauthn_test.app:create_app db upgrade
uv run pytest
sudo systemctl restart webauthn.service
```
