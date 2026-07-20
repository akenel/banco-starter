#!/usr/bin/env python3
# ============================================================================
# rotate-secret — the guided key-changer. Swap ONE secret in .env the safe way:
# see the old (masked) → type the new (hidden) → TEST it live → only then write.
# If the test fails, your .env is left untouched and the old key keeps working.
#
#   python3 scripts/rotate-secret.py            # pick from a menu
#   python3 scripts/rotate-secret.py b2         # go straight to the B2 keys
#   python3 scripts/rotate-secret.py llm-key
#
# It always: backs up .env → .env.bak first, preserves every comment, writes 0600,
# and never prints a secret back. Zero dependencies — plain Python 3 stdlib, so it
# runs on a bare machine (same as init-banco.py). The partner to the Settings →
# Backup cockpit: the cockpit shows a key is wired; this rotates it and proves the
# new one works before committing.
#
# Angel's flow, exactly: "put in the old… then the new. Check it. Yes. It works."
# ============================================================================
import base64
import json
import os
import secrets as _secrets
import shutil
import sys
import urllib.request
import urllib.error
from getpass import getpass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, ".env")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "cyan": "\033[36m", "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


# --- .env read/write (comment-preserving, same discipline as init-banco.py) ---
def parse_env(path):
    d = {}
    if not os.path.exists(path):
        return d
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip()
    return d


def write_env(updates):
    """Apply {KEY: value} to .env, preserving comments + all other lines. Backs up first."""
    if not os.path.exists(ENV):
        print(f"{C['red']}❌ No .env found — run scripts/init-banco.py first.{C['x']}")
        return False
    out, seen = [], set()
    for line in open(ENV, encoding="utf-8"):
        raw = line.rstrip("\n")
        if raw and not raw.lstrip().startswith("#") and "=" in raw:
            key = raw.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(raw)
    # a key not already present in .env (e.g. a never-set var) gets appended
    for key, val in updates.items():
        if key not in seen:
            out.append(f"{key}={val}")
    shutil.copy2(ENV, ENV + ".bak")
    with open(ENV, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    try:
        os.chmod(ENV, 0o600)
    except OSError:
        pass
    return True


def mask(s, keep=4):
    if not s:
        return f"{C['dim']}(not set){C['x']}"
    if len(s) <= keep:
        return "•" * len(s)
    return "•" * min(len(s) - keep, 12) + s[-keep:]


def ask_new_secret(label):
    """Hidden input, entered twice to confirm. Blank first entry = cancel this field."""
    while True:
        v1 = getpass(f"  new {label} (typing hidden, blank = cancel): ").strip()
        if not v1:
            return None
        v2 = getpass(f"  re-enter {label} to confirm: ").strip()
        if v1 == v2:
            return v1
        print(f"  {C['yel']}✗ didn't match — try again.{C['x']}")


def ask_new_plain(label, default=""):
    d = f" {C['dim']}[{mask(default) if default else 'blank'}]{C['x']}"
    v = input(f"  new {label}{d}: ").strip()
    return v or default


# --- live tests (stdlib urllib) ---------------------------------------------
def _http(method, url, headers=None, data=None, timeout=15):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # DNS, TLS, timeout…
        return None, str(e).encode()


def test_b2(vals):
    """Authorize to B2 with the NEW key and list the bucket → proves it works."""
    kid, app = vals.get("B2_KEY_ID", ""), vals.get("B2_APP_KEY", "")
    bucket = vals.get("B2_BUCKET", "") or parse_env(ENV).get("B2_BUCKET", "")
    if not (kid and app):
        return False, "need both B2_KEY_ID and B2_APP_KEY to test"
    basic = base64.b64encode(f"{kid}:{app}".encode()).decode()
    st, body = _http("GET", "https://api.backblazeb2.com/b2api/v3/b2_authorize_account",
                     {"Authorization": f"Basic {basic}"})
    if st != 200:
        return False, "B2 rejected the key (bad B2_KEY_ID / B2_APP_KEY)"
    auth = json.loads(body)
    storage = (auth.get("apiInfo") or {}).get("storageApi") or {}
    api_url, token = storage.get("apiUrl"), auth.get("authorizationToken")
    bucket_id, account_id = storage.get("bucketId"), auth.get("accountId")
    if not (api_url and token):
        return False, "B2 authorized but returned no API URL"
    hdr = {"Authorization": token, "Content-Type": "application/json"}
    if not bucket_id and bucket:
        st, body = _http("POST", f"{api_url}/b2api/v3/b2_list_buckets", hdr,
                         json.dumps({"accountId": account_id, "bucketName": bucket}).encode())
        if st == 200:
            bs = json.loads(body).get("buckets") or []
            bucket_id = bs[0].get("bucketId") if bs else None
    if not bucket_id:
        return True, "authorized ✓ (couldn't resolve the bucket to count backups, but the key is valid)"
    st, body = _http("POST", f"{api_url}/b2api/v3/b2_list_file_names", hdr,
                     json.dumps({"bucketId": bucket_id, "prefix": "banco/", "maxFileCount": 100}).encode())
    if st != 200:
        return True, "authorized ✓ (key valid; it can't list files — fine for a write-only backup key)"
    n = len([f for f in (json.loads(body).get("files") or []) if not f.get("fileName", "").endswith("/")])
    return True, f"authorized ✓ and listed {n} backup(s) in '{bucket}'"


def test_llm(vals):
    """Ping the Ollama/Turbo endpoint with the NEW key (GET /api/tags) → proves it works."""
    key = vals.get("BH_OLLAMA_KEY", "")
    base = (parse_env(ENV).get("OLLAMA_TURBO_URL") or "https://ollama.com").rstrip("/")
    if not key:
        return False, "no key entered"
    st, body = _http("GET", f"{base}/api/tags", {"Authorization": f"Bearer {key}"})
    if st == 200:
        try:
            n = len(json.loads(body).get("models") or [])
            return True, f"connected ✓ ({base} sees {n} model(s))"
        except Exception:
            return True, f"connected ✓ ({base})"
    if st in (401, 403):
        return False, f"{base} rejected the key ({st})"
    if st is None:
        return False, f"couldn't reach {base} ({body.decode(errors='replace')[:60]})"
    return True, f"key accepted but {base}/api/tags returned {st} — likely fine; verify with a real lookup"


# --- the registry of rotatable secrets --------------------------------------
# Each: id, title, fields [(KEY, label, secret?)], optional live test, and the
# honest post-rotation note (the seal-inspection lesson: warn about every way a
# .env change can silently NOT take effect).
SECRETS = [
    {
        "id": "b2", "title": "Backblaze B2 backup keys",
        "fields": [("B2_KEY_ID", "B2 key ID", False), ("B2_APP_KEY", "B2 application key", True)],
        "test": test_b2,
        "note": ("Once the test passes, DELETE the old key in Backblaze — creating a new key does "
                 "NOT disable the old one. Restart the app (docker compose up -d app) so the Backup "
                 "cockpit reads the new key; the host backup scripts read .env fresh each run."),
    },
    {
        "id": "llm-key", "title": "Bring-your-own-brain LLM key (BH_OLLAMA_KEY)",
        "fields": [("BH_OLLAMA_KEY", "Ollama/Turbo API key", True)],
        "test": test_llm,
        "note": "Restart the app (docker compose up -d app) so smart lookups pick up the new key.",
    },
    {
        "id": "gpg-passphrase", "title": "Backup encryption passphrase (BACKUP_GPG_PASSPHRASE)",
        "fields": [("BACKUP_GPG_PASSPHRASE", "backup encryption passphrase", True)],
        "test": None,
        "note": (C["yel"] + "⚠ THE MASTER KEY. Backups made with the OLD passphrase can ONLY be "
                 "restored with the OLD passphrase — keep it safe until every old backup has aged "
                 "out of your bucket. New backups use the new passphrase. Store the new one in a "
                 "password manager, off this machine." + C["x"]),
    },
    {
        "id": "app-secret", "title": "App signing secret (SECRET_KEY)",
        "fields": [("SECRET_KEY", "app signing secret", True)],
        "test": None, "generate": lambda: _secrets.token_hex(32),
        "note": "Restart the app. Existing signed sessions become invalid — everyone logs in again.",
    },
    {
        "id": "admin-password", "title": "Admin password (HX_SUPER_PASSWORD + KEYCLOAK_ADMIN_PASSWORD)",
        "fields": [("HX_SUPER_PASSWORD", "admin password", True)],
        "mirror": {"KEYCLOAK_ADMIN_PASSWORD": "HX_SUPER_PASSWORD"},  # both must match
        "test": None,
        "note": (C["yel"] + "⚠ This sets the admin password for a FRESH stack. If Keycloak is already "
                 "running, changing .env does NOT change the existing admin login — also change it in "
                 "Keycloak itself (or reset the realm). Both env vars are kept in sync automatically." + C["x"]),
    },
    {
        "id": "db-password", "title": "Database password (POSTGRES_PASSWORD)",
        "fields": [("POSTGRES_PASSWORD", "postgres password", True)],
        "test": None,
        "note": (C["red"] + "⚠ ADVANCED. Postgres bakes its password at first init. On an already-created "
                 "database, this .env change will NOT match the real password and the app + Keycloak will "
                 "fail to connect. Only rotate this alongside an actual DB change (ALTER USER … PASSWORD) "
                 "or a fresh data volume. If unsure, cancel." + C["x"]),
    },
]
BY_ID = {s["id"]: s for s in SECRETS}


def pick_secret():
    print(f"\n{C['b']}Which secret do you want to rotate?{C['x']}")
    for i, s in enumerate(SECRETS, 1):
        print(f"  {C['cyan']}{i}{C['x']}) {s['title']}  {C['dim']}({s['id']}){C['x']}")
    print(f"  {C['dim']}q) cancel{C['x']}")
    while True:
        c = input("  pick a number: ").strip().lower()
        if c in ("q", "", "quit", "exit"):
            return None
        if c.isdigit() and 1 <= int(c) <= len(SECRETS):
            return SECRETS[int(c) - 1]
        if c in BY_ID:
            return BY_ID[c]
        print(f"  {C['yel']}?  enter 1–{len(SECRETS)} or q.{C['x']}")


def main():
    print(f"\n{C['b']}🔑 Banco secret rotation{C['x']}")
    print(f"{C['dim']}See the old (masked) → type the new (hidden) → test it → only then write .env.{C['x']}")

    if not os.path.exists(ENV):
        print(f"{C['red']}❌ No .env found — run scripts/init-banco.py first.{C['x']}")
        return 1

    sec = BY_ID.get(sys.argv[1].strip().lower()) if len(sys.argv) > 1 else pick_secret()
    if len(sys.argv) > 1 and not sec:
        print(f"{C['red']}Unknown secret '{sys.argv[1]}'. Options: {', '.join(BY_ID)}{C['x']}")
        return 2
    if not sec:
        print(f"{C['yel']}cancelled — nothing changed.{C['x']}")
        return 0

    cur = parse_env(ENV)
    print(f"\n{C['b']}{C['cyan']}── Rotating: {sec['title']} ──{C['x']}")
    print(f"{C['dim']}{sec['note']}{C['x']}")

    # 1) collect the new value(s)
    new = {}
    for key, label, is_secret in sec["fields"]:
        print(f"  {C['dim']}current {key}: {mask(cur.get(key, ''))}{C['x']}")
        if is_secret and sec.get("generate"):
            if input(f"  generate a strong {label} automatically? [Y/n]: ").strip().lower() in ("", "y", "yes"):
                new[key] = sec["generate"]()
                print(f"  {C['grn']}✓ generated{C['x']}")
                continue
        val = ask_new_secret(label) if is_secret else ask_new_plain(label, cur.get(key, ""))
        if not val:
            print(f"  {C['yel']}blank — cancelled, nothing changed.{C['x']}")
            return 0
        new[key] = val

    # mirror any linked keys (admin password → both env vars)
    for mkey, src in (sec.get("mirror") or {}).items():
        if src in new:
            new[mkey] = new[src]

    # 2) TEST the new value live, if we can
    if sec.get("test"):
        print(f"\n  {C['dim']}testing the new key against the live service…{C['x']}")
        ok, msg = sec["test"](new)
        if ok:
            print(f"  {C['grn']}✅ {msg}{C['x']}")
        else:
            print(f"  {C['red']}❌ {msg}{C['x']}")
            ans = input(f"  {C['yel']}The new key did NOT verify. Write it anyway? [y/N]: {C['x']}").strip().lower()
            if ans not in ("y", "yes"):
                print(f"  {C['grn']}Good call — .env left untouched, your old key still works.{C['x']}")
                return 0
    else:
        print(f"  {C['dim']}(no automatic test for this secret — see the note above){C['x']}")

    # 3) write .env (backup first)
    if not write_env(new):
        return 1
    print(f"\n{C['b']}{C['grn']}✅ Updated .env{C['x']}  {C['dim']}(backed up → .env.bak, perms 0600){C['x']}")
    print(f"  rotated: {C['b']}{', '.join(new)}{C['x']}")
    print(f"\n{C['b']}Remember:{C['x']} {sec['note']}")
    print(f"\n{C['dim']}Verify the shop after a restart:  ./scripts/postboot-check.py{C['x']}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C['yel']}cancelled — no changes written.{C['x']}")
        sys.exit(130)
