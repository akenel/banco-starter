#!/usr/bin/env python3
# ============================================================================
# kc-set-redirect — teach Keycloak your production URL.
#
# The realm ships with localhost redirect URIs (fine for the laptop). In production
# Keycloak MUST also allow your real domain, or login dies with "Invalid redirect_uri"
# — the #1 go-live snag. This adds https://<APP_PUBLIC_HOST>/* + /pos/callback to the
# helix_pos_web client (redirectUris + webOrigins) via the Keycloak admin API.
#
# Idempotent: run it as often as you like; it only adds what's missing. deploy-prod.sh
# runs it automatically after the stack is up. Zero dependencies — Python 3 stdlib.
#
#   python3 scripts/kc-set-redirect.py
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
    headers = {}
    body = None
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
    app_host = _env("APP_PUBLIC_HOST")
    if not app_host:
        print(f"{C['red']}❌ APP_PUBLIC_HOST not set in .env — run scripts/go-live.py first.{C['x']}")
        return 1

    # KC admin is reached on the host (deploy-prod runs on the server); default 8080.
    kc_base = f"http://localhost:{_env('KC_HOST_PORT', '8080')}"
    realm = _env("POS_REALM", "kc-pos-realm-dev")
    admin_user = _env("HX_SUPER_NAME", "admin")
    admin_pass = _env("HX_SUPER_PASSWORD", "")
    client_id = "helix_pos_web"

    want_redirects = [f"https://{app_host}/*", f"https://{app_host}/pos/callback"]
    want_origins = [f"https://{app_host}"]

    # 1) admin token (master realm) — retry: KC's first prod boot can take a while.
    token = None
    for attempt in range(20):
        try:
            st, tok = _req("POST",
                           f"{kc_base}/realms/master/protocol/openid-connect/token",
                           data={"client_id": "admin-cli", "grant_type": "password",
                                 "username": admin_user, "password": admin_pass}, form=True)
            token = tok.get("access_token")
            if token:
                break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f"{C['red']}❌ Keycloak rejected the admin login (check HX_SUPER_NAME/PASSWORD).{C['x']}")
                return 1
        except Exception:
            pass
        if attempt == 0:
            print(f"{C['dim']}waiting for Keycloak to answer…{C['x']}")
        time.sleep(6)
    if not token:
        print(f"{C['red']}❌ Keycloak didn't answer in time on {kc_base}. Is it up? (docker compose logs keycloak){C['x']}")
        return 1

    # 2) find the client
    try:
        st, clients = _req("GET",
                           f"{kc_base}/admin/realms/{realm}/clients?clientId={urllib.parse.quote(client_id)}",
                           token=token)
    except Exception as e:
        print(f"{C['red']}❌ Could not query clients on realm '{realm}': {type(e).__name__}{C['x']}")
        return 1
    if not clients:
        print(f"{C['red']}❌ Client '{client_id}' not found in realm '{realm}'.{C['x']}")
        return 1
    client = clients[0]
    cuid = client["id"]

    # 3) merge in the prod URLs (idempotent — only add what's missing)
    redirects = list(client.get("redirectUris") or [])
    origins = list(client.get("webOrigins") or [])
    added = []
    for u in want_redirects:
        if u not in redirects:
            redirects.append(u)
            added.append(u)
    for o in want_origins:
        if o not in origins:
            origins.append(o)
            added.append(o)

    if not added:
        print(f"{C['grn']}✅ Keycloak already allows https://{app_host} — nothing to change.{C['x']}")
        return 0

    client["redirectUris"] = redirects
    client["webOrigins"] = origins
    try:
        _req("PUT", f"{kc_base}/admin/realms/{realm}/clients/{cuid}", token=token, data=client)
    except Exception as e:
        print(f"{C['red']}❌ Update failed: {type(e).__name__}{C['x']}")
        return 1

    print(f"{C['grn']}✅ Keycloak now allows login on https://{app_host}{C['x']}")
    for a in added:
        print(f"   {C['dim']}+ {a}{C['x']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
