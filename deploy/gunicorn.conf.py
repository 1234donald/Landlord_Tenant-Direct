"""
Gunicorn configuration for the Landlord-Tenant Direct Connect Platform
(Sprint 7.7, production deployment reference).

This is a REFERENCE configuration for a Linux production host (AGENTS 44).
It is NOT executed in this local Windows development environment; it is the
documented configuration an operator uses to serve the deployed Django
application behind Nginx over HTTPS (Gunicorn -> Django; Nginx terminates TLS
and proxies to Gunicorn).

Start the application:

    gunicorn --config deploy/gunicorn.conf.py config.wsgi:application

Adjust the paths below for the deployment user and the project location.
"""

import multiprocessing
import os

# Bind to a local unix socket (or 127.0.0.1:8000) that Nginx proxies to.
# A unix socket is recommended; update the socket path/group as needed.
bind = "unix:/run/gunicorn/landlord_tenant.sock"

# Number of worker processes. A safe default is (2 x CPU cores) + 1.
workers = multiprocessing.cpu_count() * 2 + 1

# Sync worker is a simple, reliable choice. Enable this when the project is
# ready for a threaded/async worker class.
worker_class = "sync"

# Timeout in seconds for a request; tune for the recommendation endpoint.
timeout = 120
graceful_timeout = 30
keepalive = 5

# Drop privileges. Replace with the dedicated deployment service user.
user = "www-data"
group = "www-data"

# TLS is terminated by Nginx, so Gunicorn speaks plain HTTP on the socket.
# Forward the original scheme/address received from Nginx so Django can
# enforce HTTPS redirects and secure cookies correctly (SECURE_PROXY_SSL_HEADER).
forwarded_allow_ips = "127.0.0.1"
proxy_protocol = False

# Environment is provided by the process supervisor (systemd/nginx env vars).
# Nothing secret is hard-coded here (AGENTS 19, 20).

# Access log writes to the console; a process supervisor (journald) collects it.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Name Gunicorn's worker processes for clarity in process listings.
proc_name = "landlord_tenant_gunicorn"
