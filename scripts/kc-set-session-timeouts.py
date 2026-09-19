#!/usr/bin/env python3
# ============================================================================
# kc-set-session-timeouts — make the till stay signed in for a shift, not for a bank session.
#
#   python3 scripts/kc-set-session-timeouts.py            # apply
#   python3 scripts/kc-set-session-timeouts.py --show     # just print what is set now
#
# WHY THIS EXISTS (2026-08-07). Angel, mid-test: "for some bizarre reason i get logged out
# for no reason." Diagnosed from the logs: POST /pos/refresh returned 401 five times while
# his ACCESS token still worked (the next request after each one was a clean 200), and the
# session only died when the access token itself expired — "JWT validation failed: Signature
# has expired". So the refresh TOKEN had died first, on its own.
#
# The refresh token lives exactly `ssoSessionIdleTimeout`, which the realm shipped at
# **30 minutes**. The session survives only because the notification poller fires every 45s
# and renews the token roughly every 5 minutes — and **that poller stops when the tab is in
# the background**, because Chrome throttles and then freezes background timers. His POS tab
# sat behind a dozen others; nothing refreshed; the idle clock ran out.
#
# It is not only a laptop problem. At 30 minutes, a quiet Tuesday afternoon signs the cashier
# out mid-shift, and so does a tablet with the screen off.
#
# THE NUMBER IS ANGEL'S, and his reasoning is the right way to pick it:
#
#     "if she is not using it for 1 hour means they left for the day or fell asleep in the
#      back office -- i have never seen a day at the shop where nothing happens for an hour
#      so it would be better -- 30 minutes is not un-common"
#
# That is a shop-calibrated number rather than a copied default: 30 minutes of quiet is an
# ordinary afternoon, a full hour of nothing is somebody having gone home.
#
# ---------------------------------------------------------------------------
# REVISED 2026-09-19 — 1h → 10h idle, and the max lifespan 10h → 14h.
#
# The paragraph above USED TO END "what this deliberately does NOT touch:
# ssoSessionMaxLifespan (10h)". It does now, and Angel called it with the trade-off in
# front of him. Both halves of the old reasoning are kept above on purpose: the rule was
# right for the day it was written against, and here is the day that broke it.
#
# WHAT BROKE IT. Layla worked the shop on 2026-09-18 doing INTAKE, not selling — walking
# the shelves with the gun and photographing packets, which touches no authenticated
# endpoint. Gaps between her feedback tickets: 122, 79, 118 and 70 minutes. Four times past
# the one-hour idle clock. Angel's premise ("i have never seen a day at the shop where
# nothing happens for an hour") holds for TRADING and does not hold for intake — and intake
# is most of what onboarding a shop actually is.
#
# The cost, in the log: `POST /pos/refresh 401` then `POST /api/v1/pos/shift/end 401`, four
# times. The presence row is closed as a side effect of logout, so a dead session means the
# row never closes. Four rows on the live shop were still ACTIVE days later.
#
# WHY THE MAX MOVED TOO, and this is the part to be deliberate about. Idle 10h against a
# max of 10h means the idle timer CAN NEVER FIRE — max always wins — so setting idle alone
# would have removed the "nobody is here" protection while pretending to lengthen it. At
# 10h idle / 14h max the idle timer is real again and still covers a full day plus closing
# up. The overnight re-login the original note protected survives: 14h from a morning login
# is the same evening, not the next morning.
#
# ⚠️ ACCEPTED, EYES OPEN: a till abandoned mid-morning now stays signed in until the
# afternoon. That is the trade Angel made for a shop that does not sign itself out during
# an intake session. If the shop ever leaves the tablet unattended in reach of the public,
# this number is the first thing to revisit — and the tablet's own screen lock, not this,
# is the right tool for that job.
#
# Idempotent. Safe to re-run. Zero dependencies — Python 3 stdlib.
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

# ── the settings, and why each one is what it is ────────────────────────────
# ssoSessionIdleTimeout — how long a session survives with NO token refresh. This is the one
#   that was biting. 3600 = one hour of literally nothing happening.
# ssoSessionMaxLifespan — the hard ceiling regardless of activity. Left at 10h: one shift,
#   then a real login. This is what keeps the idle bump honest.
# accessTokenLifespan — how often the silent refresh runs. 5 minutes is fine and normal; a
#   short access token is the thing that makes a stolen one useless quickly.
TARGET = {
    "ssoSessionIdleTimeout": 36000,     # 10 hours (was 3600 — 1 hour; 2026-09-19, see below)
    "ssoSessionMaxLifespan": 50400,     # 14 hours (was 36000 — 10 hours; a day PLUS closing up)
    "accessTokenLifespan": 300,         # 5 min   — unchanged
}

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


def _mins(v):
    try:
        return f"{int(v) / 60:.0f} min"
    except (TypeError, ValueError):
        return str(v)


def main():
    show_only = "--show" in sys.argv
    kc_base = f"http://localhost:{_env('KC_HOST_PORT', '8080')}"
    realm = _env("POS_REALM", "kc-pos-realm-dev")
    admin_user = _env("HX_SUPER_NAME", "admin")
    admin_pass = _env("HX_SUPER_PASSWORD", "")

    if not admin_pass:
        print(f"{C['red']}❌ HX_SUPER_PASSWORD not set in .env — cannot log in to Keycloak.{C['x']}")
        return 1

    # 1) admin token (retry — KC may still be booting)
    token = None
    for attempt in range(20):
        try:
            st, tok = _req("POST", f"{kc_base}/realms/master/protocol/openid-connect/token",
                           data={"client_id": "admin-cli", "grant_type": "password",
                                 "username": admin_user, "password": admin_pass}, form=True)
            token = (tok or {}).get("access_token")
            if token:
                break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f"{C['red']}❌ Keycloak rejected the admin login "
                      f"(HX_SUPER_NAME / HX_SUPER_PASSWORD).{C['x']}")
                return 1
        except Exception:
            pass
        if attempt == 0:
            print(f"{C['dim']}waiting for Keycloak on {kc_base}…{C['x']}")
        time.sleep(6)
    if not token:
        print(f"{C['red']}❌ Keycloak didn't answer on {kc_base}. (docker compose logs keycloak){C['x']}")
        return 1

    # 2) read the realm
    try:
        st, rep = _req("GET", f"{kc_base}/admin/realms/{urllib.parse.quote(realm)}", token=token)
    except Exception as e:
        print(f"{C['red']}❌ Could not read realm '{realm}': {type(e).__name__}{C['x']}")
        return 1

    print(f"{C['dim']}realm: {realm} @ {kc_base}{C['x']}")
    changed = []
    for k, want in TARGET.items():
        have = rep.get(k)
        mark = "=" if have == want else "→"
        colour = C["dim"] if have == want else C["yel"]
        print(f"  {colour}{k:24} {_mins(have):>9} {mark} {_mins(want):>9}{C['x']}")
        if have != want:
            changed.append(k)

    if show_only:
        return 0
    if not changed:
        print(f"{C['grn']}✅ already set — nothing to do.{C['x']}")
        return 0

    rep.update(TARGET)
    try:
        _req("PUT", f"{kc_base}/admin/realms/{urllib.parse.quote(realm)}", token=token, data=rep)
    except Exception as e:
        print(f"{C['red']}❌ Could not update realm: {type(e).__name__}: {e}{C['x']}")
        return 1

    # 3) PROVE it, don't assume it — re-read rather than trust the PUT
    st, back = _req("GET", f"{kc_base}/admin/realms/{urllib.parse.quote(realm)}", token=token)
    bad = {k: back.get(k) for k, v in TARGET.items() if back.get(k) != v}
    if bad:
        print(f"{C['red']}❌ Keycloak did not keep the values: {bad}{C['x']}")
        return 1

    print(f"{C['grn']}✅ updated {', '.join(changed)}{C['x']}")
    print(f"{C['dim']}   Existing sessions keep their OLD timeout — sign out and back in to "
          f"get the new one.{C['x']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
