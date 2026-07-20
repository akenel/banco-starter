#!/usr/bin/env python3
# ============================================================================
# postboot-check — "did it come up right, and is it safe to go test?"
#
# The morning-after smoke test. banco-doctor asks "is the config YOURS yet?"
# (VAT, passwords, backups — go-live readiness). THIS asks the other question:
# right now, this minute, are all four pieces actually up and wired together,
# so a human can walk to the till and log in? It pokes the LIVE stack — the
# containers, the app's health endpoint, Keycloak's realm, the seeded catalog —
# and pumps out one plain verdict at the end:
#
#     ✅ SAFE TO TEST → open http://localhost:8000/pos and log in (pam / pam)
#   or
#     ❌ NOT READY → here's the ONE thing to fix.
#
#   python3 scripts/postboot-check.py        # run it after `docker compose up`
#
# Zero dependencies — plain Python 3 standard library. Exit 0 = safe, 1 = not.
# standup.sh runs it automatically at the end of a stand-up.
# ============================================================================
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")

EXPECTED_CONTAINERS = ("postgres", "keycloak", "minio", "app")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def read_env(path):
    """Parse a .env into a dict. Never executes it (values may hold specials)."""
    env = {}
    if not os.path.exists(path):
        return env
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def http(url, timeout=6):
    """GET a URL. Returns (status_or_None, body_or_error)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "postboot-check"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(4096).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def psql(env, query):
    """Run a query in the postgres container. Returns text or None if unreachable."""
    user = env.get("POSTGRES_USER") or "helix_user"
    db = env.get("POSTGRES_DB") or "helix_db"
    try:
        r = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres",
             "psql", "-U", user, "-d", db, "-tAc", query],
            cwd=ROOT, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def running_containers():
    """Names of compose services currently 'running'. Empty on any failure."""
    try:
        r = subprocess.run(["docker", "compose", "ps", "--format", "json"],
                           cwd=ROOT, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {}
    except Exception:
        return {}
    out = r.stdout.strip()
    rows = []
    if out.startswith("["):                       # older compose: one JSON array
        try:
            rows = json.loads(out)
        except Exception:
            rows = []
    else:                                          # newer compose: NDJSON
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    state = {}
    for row in rows:
        svc = row.get("Service") or row.get("Name") or ""
        state[svc] = (row.get("State") or row.get("Status") or "").lower()
    return state


def main():
    env = read_env(ENV_PATH)
    app_port = env.get("APP_HOST_PORT") or "8000"
    kc_port = env.get("KC_HOST_PORT") or "8080"
    realm = env.get("POS_REALM") or "kc-pos-realm-dev"
    pos_url = f"http://localhost:{app_port}/pos"

    print(f"\n{C['b']}🚦 Banco post-boot smoke test{C['x']}  {C['dim']}(is it up and safe to test?){C['x']}\n")

    findings = []   # (severity, line, critical)

    def ok(msg, critical=True):
        findings.append(("ok", msg, critical))
        print(f"  {C['grn']}✅ {msg}{C['x']}")

    def fail(msg, fix="", critical=True):
        findings.append(("fail", msg, critical))
        print(f"  {C['red']}❌ {msg}{C['x']}")
        if fix:
            print(f"       {C['grn']}→ {fix}{C['x']}")

    def warn(msg, fix=""):
        findings.append(("warn", msg, False))
        print(f"  {C['yel']}⚠️  {msg}{C['x']}")
        if fix:
            print(f"       {C['dim']}{fix}{C['x']}")

    # 1) Containers ---------------------------------------------------------
    state = running_containers()
    if not state:
        fail("Can't read `docker compose ps` — is Docker running / are you in the repo root?",
             "cd into banco-starter and run `docker compose up -d` first.")
    else:
        for name in EXPECTED_CONTAINERS:
            st = state.get(name, "")
            if "running" in st or "up" in st:
                ok(f"container '{name}' is running")
            else:
                fail(f"container '{name}' is not running (state: {st or 'absent'})",
                     f"docker compose up -d {name}   ·   then: docker compose logs {name}")

    # 2) App health ---------------------------------------------------------
    code, _ = http(f"http://localhost:{app_port}/health/healthz")
    if code == 200:
        ok(f"app answers /health/healthz on :{app_port}")
    else:
        fail(f"app health check failed on :{app_port} (got {code})",
             f"docker compose logs app   ·   check APP_HOST_PORT in .env")

    # 3) Keycloak realm live -----------------------------------------------
    code, _ = http(f"http://localhost:{kc_port}/realms/{realm}/.well-known/openid-configuration")
    if code == 200:
        ok(f"Keycloak realm '{realm}' is serving on :{kc_port}")
    else:
        fail(f"Keycloak realm '{realm}' not reachable on :{kc_port} (got {code})",
             "KC can take 1-2 min to import on a slow box — wait, then re-run. "
             "Persist? `docker compose logs keycloak`.")

    # 4) Login page renders -------------------------------------------------
    code, body = http(pos_url)
    if code == 200 and ("login" in body.lower() or "keycloak" in body.lower() or "pos" in body.lower()):
        ok("POS login page renders")
    elif code == 200:
        warn("POS page returned 200 but didn't look like the login screen", "eyeball it in a browser")
    else:
        fail(f"POS page {pos_url} failed (got {code})", "docker compose logs app")

    # 5) Catalog seeded -----------------------------------------------------
    prod = psql(env, "SELECT count(*) FROM products;")
    supp = psql(env, "SELECT count(*) FROM suppliers;")
    if prod is None or supp is None:
        fail("database not reachable (couldn't count products/suppliers)",
             "docker compose logs postgres")
    else:
        p, s = int(prod or 0), int(supp or 0)
        seed_demo = (env.get("HX_SEED_DEMO", "true").strip().lower() not in ("false", "0", "no"))
        if s >= 2:
            ok(f"suppliers seeded ({s})", critical=False)
        else:
            warn(f"only {s} supplier(s) — expected the 2 foundation sources (Tamar, FourTwenty)")
        if not seed_demo:
            ok(f"catalog empty by design (HX_SEED_DEMO=false) — {p} products", critical=False)
        elif p >= 6:
            ok(f"demo catalog seeded ({p} products, incl. the 6 Treats)", critical=False)
        else:
            warn(f"only {p} products with HX_SEED_DEMO=true — expected ≥6 (the Treats)",
                 "if this is a restored DB, ignore; else check `docker compose logs app`")

    # 6) B2 backups configured (info only — never prints the key) -----------
    b2_set = all(env.get(k) for k in ("B2_KEY_ID", "B2_APP_KEY", "B2_BUCKET"))
    if b2_set:
        ok("B2 backup vars are filled (run scripts/backup-to-b2.sh to prove write access)", critical=False)
    else:
        warn("B2 backup not configured yet (fine for now)",
             "before go-live: fill B2_* in .env — see onboarding/06-own-your-data-backups.md")

    # ---- Verdict ----------------------------------------------------------
    blockers = [f for f in findings if f[0] == "fail" and f[2]]
    warns = [f for f in findings if f[0] == "warn"]
    print()
    if blockers:
        print(f"{C['b']}{C['red']}❌ NOT READY — {len(blockers)} thing(s) to fix before testing.{C['x']}")
        print(f"   Start with the first ❌ above; re-run this when it's green.")
        return 1
    if warns:
        print(f"{C['b']}{C['yel']}🟡 UP, with {len(warns)} note(s) to glance at above.{C['x']}")
    else:
        print(f"{C['b']}{C['grn']}✅ ALL GREEN.{C['x']}")
    print(f"\n{C['b']}{C['grn']}👉 SAFE TO TEST — open {C['x']}{C['b']}{pos_url}{C['x']}{C['b']}{C['grn']} and log in (pam / pam).{C['x']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
