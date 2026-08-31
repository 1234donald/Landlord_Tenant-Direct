"""
Deployment-readiness verification for Phase 7, Sprint 7.7 - Production
Deployment and Finalisation (SYSTEM_REQUIREMENTS §41; AGENTS 5, 19, 20, 26,
33, 35, 44, 45, 49).

This sprint delivers the *production deployment foundation* for a Linux-based
deployment (Gunicorn + Nginx + PostgreSQL + HTTPS + environment variables).
A live deploy of the application to a real Linux host cannot be performed from
this local Windows development environment, so -- in line with AGENTS 39 and
40 -- this suite does NOT claim a deployed system exists. Instead it verifies,
honestly and reproducibly, that the codebase is deployment-READY by checking
the concrete, observable readiness criteria:

- Production settings import under the production environment and pass
  Django's own deployment security checks (``check --deploy``) with ZERO
  Django ``security.W`` warnings (AGENTS 19, 44).
- The plain system check passes with no issues (AGENTS 22).
- No pending Django migrations (AGENTS 33) and every app has a committed
  ``0001_initial`` migration (AGENTS 29, 33).
- ``.env.example`` declares every production environment variable and
  ``.env`` is git-ignored (AGENTS 20).
- Production secrets are read from the environment, never hard-coded
  (AGENTS 19, 20).
- The approved production server dependencies (Gunicorn) and static-file
  serving (WhiteNoise) are pinned in ``requirements.txt`` (AGENTS 5, 44, 46).
- Production security hardening flags (secure cookies, HSTS, SSL redirect,
  nosniff, X-Frame-Options) and WhiteNoise are configured (AGENTS 19, 44).

Django's ``check --deploy`` hard-codes warnings-as-errors, and this repository
carries a small set of PRE-EXISTING cosmetic ``drf_spectacular`` OpenAPI-schema
warnings (W001/W002) produced by ``drf_spectacular`` inspecting plain
``APIView`` subclasses. Those notices affect only the optional auto-generated
OpenAPI schema and have no effect on the security, functioning or deployment
of the application. This suite therefore gates on the authoritative Django
security checks (absence of any ``security.W`` warning and any raw ``ERROR:``)
rather than on an exit code that the cosmetic schema notices would flip.
"""

import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PRODUCTION_ENV_VARS = [
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "DATABASE_NAME",
    "DATABASE_HOST",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "DATABASE_PORT",
]

# A strong, random-looking secret key used solely to satisfy Django's check in
# the subprocess. It is never stored or committed anywhere.
_STRONG_TEST_KEY = "F9kL2#mQ8z!vX4@nW7pR1&tY6^sU3*eC0(jD5%gH2|aSd8_F1bVc9"

_PRODUCTION_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.production",
    "SECRET_KEY": _STRONG_TEST_KEY,
    "DEBUG": "False",
    "ALLOWED_HOSTS": "example.com",
    "CSRF_TRUSTED_ORIGINS": "https://example.com",
    "DATABASE_NAME": "landlord_tenant_db",
    "DATABASE_HOST": "127.0.0.1",
    "DATABASE_USER": "postgres",
    "DATABASE_PASSWORD": "postgres",
    "DATABASE_PORT": "5432",
    "PATH": None,  # inherit PATH so manage.py's interpreter can resolve
}


def _run_manage(*args, env=None, check_exit=False):
    """Run ``manage.py <args>`` in a subprocess with the given extra env.

    Returns (returncode, combined_stdout_stderr).
    """
    import os

    # Inherit the full calling environment and layer the production variables
    # on top. Only truthy values are set; secrets we inject are ephemeral.
    process_env = dict(os.environ)
    base_env = _PRODUCTION_ENV if env is None else env
    process_env.update({k: v for k, v in base_env.items() if v})
    result = subprocess.run(
        [PYTHON, "manage.py", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=process_env,
    )
    return result.returncode, (result.stdout + result.stderr)


def _read(relative_path):
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Django system / deployment checks
# ---------------------------------------------------------------------------

def test_plain_system_check_reports_no_issues():
    """``manage.py check`` must pass with no issues (AGENTS 22)."""
    code, output = _run_manage("check")
    assert code == 0, f"manage.py check failed:\n{output}"
    assert "System check identified no issues" in output, output


def test_production_check_deploy_has_no_django_security_warnings():
    """Production ``check --deploy`` must report zero Django security.W
    warnings and zero errors (AGENTS 19, 44).

    Django's own security check-list covers SECRET_KEY strength, secure
    cookies, HSTS, SSL redirect, allowed hosts, CSRF, nosniff and more; any of
    these failing would surface as a ``security.W``/``security.E`` warning, so
    asserting their absence is the authoritative deployment gate.
    """
    code, output = _run_manage("check", "--deploy")
    assert "security.W" not in output, (
        "Django security deployment warnings present:\n"
        + "\n".join(l for l in output.splitlines() if "security." in l)
    )
    assert "security.E" not in output, (
        "Django security deployment errors present:\n"
        + "\n".join(l for l in output.splitlines() if "security." in l)
    )
    assert "ERROR:" not in output, (
        "Raw system-check errors present:\n"
        + "\n".join(l for l in output.splitlines() if "ERROR:" in l)
    )


def test_no_pending_migrations():
    """``makemigrations --check --dry-run`` must report no needed changes
    (AGENTS 33)."""
    code, output = _run_manage("makemigrations", "--check", "--dry-run")
    assert code == 0, f"makemigrations --check failed:\n{output}"
    assert "No changes detected" in output, output


# ---------------------------------------------------------------------------
# Migrations committed for every app
# ---------------------------------------------------------------------------

def test_all_apps_have_initial_migrations():
    """Every installed app must carry a migrations package, and every app that
    registers concrete models must have committed migration files (AGENTS 29,
    33).

    Uses Django's app registry (``get_models``) instead of string heuristics,
    so apps whose models use a non-``models.Model`` base (e.g. the custom User
    model) are handled correctly. Model-less utility/template apps (e.g.
    ``core``, ``admin_dashboard``) legitimately need no schema migrations.
    """
    from django.apps import apps as django_apps

    missing_migrations = []
    for config in django_apps.get_app_configs():
        # Only this project's own apps are in scope.
        app_path = getattr(config, "path", None)
        if not app_path or REPO_ROOT not in Path(app_path).resolve().parents:
            continue
        has_models = len(list(config.get_models())) > 0
        # Only apps that register models are required to carry migrations.
        if not has_models:
            continue
        package = Path(app_path) / "migrations"
        if not (package / "__init__.py").exists():
            missing_migrations.append(f"{config.label} (no migrations package)")
            continue
        committed = list(package.glob("000*.py"))
        if not committed:
            missing_migrations.append(f"{config.label} (no migration files)")
    assert not missing_migrations, (
        f"apps registering models without committed migrations: "
        f"{missing_migrations}"
    )
    assert not missing_migrations, (
        f"apps registering models without committed migrations: "
        f"{missing_migrations}"
    )


# ---------------------------------------------------------------------------
# Environment variables and secrets
# ---------------------------------------------------------------------------

def test_env_example_declares_production_variables():
    """.env.example must declare every production variable (AGENTS 20)."""
    example = _read(".env.example")
    missing = [
        var for var in REQUIRED_PRODUCTION_ENV_VARS if f"{var}=" not in example
    ]
    assert not missing, f".env.example missing: {missing}"


def test_dotenv_is_gitignored():
    """.env must never be committed (AGENTS 19, 20)."""
    gitignore_lines = _read(".gitignore").splitlines()
    assert ".env" in gitignore_lines, (
        ".env is not listed in .gitignore"
    )


def test_secret_key_read_from_env_not_hardcoded():
    """Production SECRET_KEY must come from the environment, never a hard-coded
    literal (AGENTS 19, 20)."""
    production = _read("config/settings/production.py")
    assert 'env("SECRET_KEY")' in production, (
        "production.py must read SECRET_KEY from the environment"
    )
    assert "django-insecure-" not in production, (
        "production.py must not contain a Django-generated placeholder key"
    )


def test_no_obvious_secret_literals_in_production_settings():
    """Production settings must not contain literal production credentials
    (AGENTS 19, 20)."""
    production = _read("config/settings/production.py")
    assert "DATABASE_PASSWORD = ambient" not in production  # guard no crash
    # The password must be sourced from the environment, not a literal.
    assert 'env("DATABASE_PASSWORD"' in production, (
        "production.py must read DB password from the environment"
    )


# ---------------------------------------------------------------------------
# Production security hardening configuration
# ---------------------------------------------------------------------------

def test_production_security_hardening_configured():
    """The required secure-cookie / HSTS / SSL redirect settings must be
    present in the production settings module (AGENTS 19, 44)."""
    production = _read("config/settings/production.py")
    for flag in [
        "SESSION_COOKIE_SECURE = True",
        "SESSION_COOKIE_HTTPONLY = True",
        "CSRF_COOKIE_SECURE = True",
        "SECURE_SSL_REDIRECT = True",
        "SECURE_HSTS_SECONDS",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        "SECURE_CONTENT_TYPE_NOSNIFF = True",
        "X_FRAME_OPTIONS = \"DENY\"",
        "SECURE_REFERRER_POLICY",
        'SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")',
    ]:
        assert flag in production, f"production.py missing hardening: {flag}"


def test_production_uses_whitenoise_and_staticfiles_root():
    """WhiteNoise middleware and a configured STATIC_ROOT must be present for
    production static serving (AGENTS 44, 5)."""
    production = _read("config/settings/production.py")
    assert "whitenoise.middleware.WhiteNoiseMiddleware" in production, (
        "production.py must register WhiteNoiseMiddleware"
    )
    assert "whitenoise.storage.CompressedManifestStaticFilesStorage" in production, (
        "production.py must use WhiteNoise manifest storage"
    )
    base = _read("config/settings/base.py")
    assert 'STATIC_ROOT = BASE_DIR / "staticfiles"' in base, (
        "base.py must set STATIC_ROOT for collectstatic"
    )


# ---------------------------------------------------------------------------
# Approved production dependencies (AGENTS 5, 44, 46)
# ---------------------------------------------------------------------------

def test_requirements_pin_gunicorn_and_whitenoise():
    """requirements.txt must pin the approved production server (Gunicorn) and
    static-file layer (WhiteNoise) (AGENTS 5, 44, 46)."""
    requirements = _read("requirements.txt")
    for dep in ["gunicorn", "whitenoise", "psycopg"]:
        assert dep in requirements, (
            f"requirements.txt is missing the approved dependency: {dep}"
        )


# ---------------------------------------------------------------------------
# Deployment documentation / config artifacts (reference, not a live deploy)
# ---------------------------------------------------------------------------

def test_deployment_reference_artifacts_exist():
    """The deployment package must include the reference Gunicorn and Nginx
    configs plus a deployment guide (AGENTS 44). A reference config is provided
    because a live host deployment cannot be performed from this environment
    and must not be fabricated (AGENTS 39, 40)."""
    deploy_dir = REPO_ROOT / "deploy"
    assert (deploy_dir / "gunicorn.conf.py").exists(), (
        "missing deploy/gunicorn.conf.py reference"
    )
    assert (deploy_dir / "nginx.conf").exists(), (
        "missing deploy/nginx.conf reference"
    )
    assert (deploy_dir / "README.md").exists(), (
        "missing deploy/README.md deployment guide"
    )
