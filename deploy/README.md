# Deployment Guide — Landlord–Tenant Direct Connect Platform

**Sprint 7.7 — Production Deployment and Finalisation (SYSTEM_REQUIREMENTS §41;
AGENTS 44).**

This document is the **reference deployment guide** for putting the platform
into production on a Linux host (the approved production target: Gunicorn +
Nginx + PostgreSQL + HTTPS + environment variables). It is accompanied by the
reference configurations in this directory:

- `gunicorn.conf.py` — Gunicorn worker configuration for the Django app.
- `nginx.conf` — Nginx configuration terminating TLS and proxying to Gunicorn.

> **Honest status (AGENTS 39, 40):** A live deployment of this application to
> an internet-accessible Linux host has **NOT** been performed from the local
> Windows development environment, because that environment has no server,
> domain, TLS certificate or managed PostgreSQL. This sprint therefore delivers
> the *deployment package* (settings verified with Django's `check --deploy`,
> environment contract, reference configs, backups/logging guidance) and
> documents the exact steps an operator follows. The system is
> **deployment-ready**, not **deployed**.

## 1. Production architecture

```
Internet
   │  HTTPS
   ▼
 Nginx (terminates TLS)
   │
   ▼
 Gunicorn (Django)
   │
   ▼
 PostgreSQL
```

- **Nginx** terminates HTTPS and proxies requests to Gunicorn, and may serve
  static/media assets directly.
- **Gunicorn** runs the Django WSGI application (`config.wsgi:application`).
- **WhiteNoise** (enabled in `config/settings/production.py`) serves static
  files from within Django as a robust default.
- **PostgreSQL** is the production database.
- All secrets come from **environment variables** — never hard-coded.

## 2. Environment variables

Create the production environment (e.g. a `systemd` unit or shell profile)
with the same variables declared in `.env.example`. Do **not** reuse the local
`.env` (it is never committed, AGENTS 20):

| Variable               | Example                              | Notes                          |
|------------------------|--------------------------------------|--------------------------------|
| `SECRET_KEY`           | `(long random string)`               | **Required**; strong + random. |
| `DEBUG`                | `False`                              | Must be `False` in production. |
| `ALLOWED_HOSTS`        | `example.com,www.example.com`        | Comma separated.               |
| `CSRF_TRUSTED_ORIGINS` | `https://example.com`                | Comma separated.               |
| `DATABASE_NAME`        | `landlord_tenant_db`                 |                                |
| `DATABASE_HOST`        | `127.0.0.1` or managed DB endpoint  |                                |
| `DATABASE_USER`        | `landlord_user`                      |                                |
| `DATABASE_PASSWORD`    | `(strong password)`                  | From the environment only.     |
| `DATABASE_PORT`        | `5432`                               |                                |

## 3. Deploying the application (reference steps)

1. Clone the repository onto the Linux host into a dedicated deployment user's
   home (e.g. `/opt/landlord_tenant` or `~/landlord_tenant`).
2. Create and activate a Python virtual environment:
   `python3 -m venv .venv && source .venv/bin/activate`
3. Install pinned dependencies:
   `pip install -r requirements.txt`
4. Create `.env` **on the server** from `.env.example` and set the production
   values (DEBUG=False, a strong SECRET_KEY, the domain in ALLOWED_HOSTS /
   CSRF_TRUSTED_ORIGINS, and PostgreSQL credentials).
5. Apply migrations:
   `python manage.py migrate`
6. Collect static files:
   `python manage.py collectstatic --noinput`
7. Run Django's own deployment checks to confirm readiness:
   `python manage.py check --deploy`
   (A small set of cosmetic `drf_spectacular` OpenAPI-schema warnings may
   appear; these affect only the optional generated schema and are not
   security issues. There must be no Django `security.*` warnings.)
8. Start Gunicorn (see `gunicorn.conf.py`):
   `gunicorn --config deploy/gunicorn.conf.py config.wsgi:application`
9. Configure Nginx with `deploy/nginx.conf`, pointing the certificate paths
   and the Gunicorn socket at your deployment, then reload Nginx.
10. Obtain/enable a TLS certificate (e.g. Let's Encrypt / certbot) and rely on
    the HTTPS redirect in `nginx.conf` plus `SECURE_SSL_REDIRECT` in Django.

## 4. Database backups

Schedule regular PostgreSQL backups. Example using `pg_dump`:

```bash
pg_dump -U landlord_user landlord_tenant_db \
  | gzip > /backups/landlord_tenant_$(date +%F).sql.gz
```

Keep backups off the application host, test restoration regularly, and secure
backup files (they contain tenant/landlord data).

## 5. Logging

- Gunicorn writes access + error logs to the console (`accesslog = "-"`,
  `errorlog = "-"`); a process supervisor (e.g. `journald`) collects them.
- Django's production `LOGGING` writes application logs to the console at
  `INFO` level. Route logs to a central location in non-local deployments.

## 6. Health checks

Expose a simple health endpoint (or use Django's built-in `/admin` login page
to confirm the app responds) and configure the load balancer / monitoring to
alert when the host is unreachable.

## 7. Relation to this repository's automated readiness suite

The Sprint 7.7 deliverable is verified by
`tests/integration/test_deployment_readiness.py`, which:
- runs `manage.py check` and confirms no issues;
- runs `manage.py check --deploy` and confirms **no Django `security.*`
  warnings or errors**;
- confirms no pending migrations and committed initial migrations for every
  app;
- confirms `.env.example` declares every production variable and that `.env`
  is git-ignored;
- confirms production secrets are read from the environment, not hard-coded;
- confirms the production security-hardening flags and WhiteNoise are set;
- confirms Gunicorn, WhiteNoise and PostgreSQL drivers are pinned.

Run it with:

```bash
python -m pytest tests/integration/test_deployment_readiness.py --reuse-db
```

This documents real, reproducible readiness — it does not fabricate a
deployment (AGENTS 39, 40).
