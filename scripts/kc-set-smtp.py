#!/usr/bin/env python3
# ============================================================================
# kc-set-smtp — point Keycloak's email at Resend (so password-resets actually send).
#
# The realm ships with no SMTP (local dev uses MailHog). In production Keycloak needs
# a real mail server to send password-reset + staff-setup links. This writes the
# realm's smtpServer config from your .env Resend settings via the KC admin API.
#
#   python3 scripts/kc-set-smtp.py
#
# Reads SMTP_* from .env (set by scripts/go-live.py). Needs SMTP_PASSWORD (your Resend
# API key) — without it, it skips cleanly. Never prints the key. Idempotent. deploy-prod.sh
# runs it automatically when SMTP is configured. Zero dependencies — Python 3 stdlib.
# ============================================================================
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, ".env")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m", "dim": "\033[2m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def _env(name, default=""):
    if not os.path.exists(ENV):
        return default
    for line in open(ENV, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    return default


def _req(method, url, token=None, data=None, form=False):
    headers, body = {}, None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
        return r.status, (json.loads(raw) if raw else None)


def main():
    host = _env("SMTP_HOST", "smtp.resend.com")
    port = _env("SMTP_PORT", "587")
    user = _env("SMTP_USER", "resend")
    password = _env("SMTP_PASSWORD")
    mail_from = _env("SMTP_FROM")
    from_name = _env("SMTP_FROM_NAME", "Banco")

    if not password:
        print(f"{C['yel']}⚠ SMTP_PASSWORD (Resend API key) not set — skipping KC email wiring. "
              f"Add it via scripts/go-live.py, then re-run.{C['x']}")
        return 0
    if not mail_from:
        print(f"{C['red']}❌ SMTP_FROM not set — Keycloak needs a verified 'from' address (e.g. noreply@yourdomain).{C['x']}")
        return 1

    kc_base = f"http://localhost:{_env('KC_HOST_PORT', '8080')}"
    realm = _env("POS_REALM", "kc-pos-realm-dev")
    admin_user = _env("HX_SUPER_NAME", "admin")
    admin_pass = _env("HX_SUPER_PASSWORD", "")

    # port 465 = implicit SSL; anything else (587/2587) = STARTTLS.
    is_ssl = port.strip() == "465"
    smtp = {
        "host": host, "port": port, "from": mail_from, "fromDisplayName": from_name,
        "auth": "true", "user": user, "password": password,
        "ssl": "true" if is_ssl else "false",
        "starttls": "false" if is_ssl else "true",
    }

    # 1) admin token (retry — KC may still be booting)
    token = None
    for attempt in range(20):
        try:
            st, tok = _req("POST", f"{kc_base}/realms/master/protocol/openid-connect/token",
                           data={"client_id": "admin-cli", "grant_type": "password",
                                 "username": admin_user, "password": admin_pass}, form=True)
            token = tok.get("access_token")
            if token:
                break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f"{C['red']}❌ Keycloak rejected the admin login (HX_SUPER_NAME/PASSWORD).{C['x']}")
                return 1
        except Exception:
            pass
        if attempt == 0:
            print(f"{C['dim']}waiting for Keycloak…{C['x']}")
        time.sleep(6)
    if not token:
        print(f"{C['red']}❌ Keycloak didn't answer on {kc_base}. (docker compose logs keycloak){C['x']}")
        return 1

    # 2) GET the realm, merge smtpServer, PUT it back
    try:
        st, rep = _req("GET", f"{kc_base}/admin/realms/{urllib.parse.quote(realm)}", token=token)
    except Exception as e:
        print(f"{C['red']}❌ Could not read realm '{realm}': {type(e).__name__}{C['x']}")
        return 1
    rep["smtpServer"] = smtp
    try:
        _req("PUT", f"{kc_base}/admin/realms/{urllib.parse.quote(realm)}", token=token, data=rep)
    except Exception as e:
        print(f"{C['red']}❌ Update failed: {type(e).__name__}{C['x']}")
        return 1

    print(f"{C['grn']}✅ Keycloak email wired → {host}:{port} as {mail_from} (via {user}).{C['x']}")
    print(f"   {C['dim']}Test it: trigger a password reset, or KC admin → Realm settings → Email → Test connection.{C['x']}")
    print(f"   {C['dim']}Emails send only once Resend shows your sending domain VERIFIED.{C['x']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
