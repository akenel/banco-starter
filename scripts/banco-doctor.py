#!/usr/bin/env python3
# ============================================================================
# banco-doctor — "what's left to set up?" for a new shop.
#
# Reads your LIVE install (the .env file + the running database) and compares
# it to "not-configured-yet". It can't be fooled the way an AI guess can —
# it reads the actual values. Run it any time; run it before go-live.
#
#   python3 scripts/banco-doctor.py            # the checklist (✅ ⚠️ ❌)
#   python3 scripts/banco-doctor.py --dump     # a SAFE snapshot to paste into
#                                              #   your own AI (no secrets shown)
#   python3 scripts/banco-doctor.py --explain  # let your Ollama Turbo coach you
#
# Zero dependencies — plain Python 3 standard library. Runs on a bare machine.
# Facts come from here; warmth (plain-language coaching) comes from the AI layer.
# ============================================================================
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")

# ---- the shipped defaults we flag as "still not yours" ---------------------
STARTER_SECRET_HINTS = ("changeme", "smoketest", "not-a-real-secret", "clone-proof")
DEFAULT_PW = "banco_local_dev"
DEFAULTS = {
    "POS_CURRENCY": "CHF",
    "POS_VAT_RATE": "8.1",
    "POS_VAT_RATE_REDUCED": "2.6",
}

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}

SEV = {"fail": ("❌", "red"), "warn": ("⚠️ ", "yel"), "ok": ("✅", "grn"), "info": ("ℹ️ ", "dim")}
RANK = {"fail": 0, "warn": 1, "info": 2, "ok": 3}


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


def is_starter_secret(val):
    if not val:
        return True
    return any(h in val.lower() for h in STARTER_SECRET_HINTS) or val == DEFAULT_PW


def build_findings(env):
    """Return a list of dicts: {sev, section, title, detail, fix}."""
    F = []

    def add(sev, section, title, detail="", fix=""):
        F.append({"sev": sev, "section": section, "title": title, "detail": detail, "fix": fix})

    db_reachable = psql(env, "SELECT 1") == "1"

    # ---- 🛟 Safety net: backups ------------------------------------------
    b2_set = all(env.get(k) for k in ("B2_KEY_ID", "B2_APP_KEY", "B2_BUCKET"))
    if b2_set:
        add("ok", "Safety net", "Backup storage (B2) is configured")
    else:
        add("fail", "Safety net", "Backups are NOT configured",
            "No Backblaze B2 key/bucket in .env — a shop with no backups is one bad day from disaster.",
            "Follow onboarding/06-own-your-data-backups.md, then run ./scripts/backup-to-b2.sh")
    if env.get("BACKUP_GPG_PASSPHRASE"):
        add("ok", "Safety net", "Backup encryption passphrase is set")
    else:
        add("fail", "Safety net", "No backup encryption passphrase",
            "BACKUP_GPG_PASSPHRASE is empty — backups can't be encrypted/restored.",
            "Set a strong BACKUP_GPG_PASSPHRASE in .env and store it in two safe places.")

    # ---- 🔐 Passwords / secrets ------------------------------------------
    for key, sev, label in (
        ("SECRET_KEY", "fail", "app signing key"),
        ("POSTGRES_PASSWORD", "fail", "database password"),
        ("HX_SUPER_PASSWORD", "fail", "Keycloak admin password"),
        ("MINIO_SECRET_KEY", "warn", "image-store password"),
    ):
        if is_starter_secret(env.get(key)):
            tip = " (generate one: `openssl rand -hex 32`)" if key == "SECRET_KEY" else ""
            add(sev, "Passwords", f"The {label} is still a starter default",
                f"{key} hasn't been changed from the value the starter ships with.",
                f"Set a strong {key} in .env{tip}, then docker compose up -d")
        else:
            add("ok", "Passwords", f"The {label} has been changed")

    # ---- 🏪 Money: currency + VAT ----------------------------------------
    cur = env.get("POS_CURRENCY", "")
    if cur == DEFAULTS["POS_CURRENCY"]:
        add("warn", "Money", "Currency is still the default (CHF)",
            "Confirm CHF is right for your country — otherwise set POS_CURRENCY (EUR, …).",
            "Set POS_CURRENCY + POS_LOCALE in .env — see onboarding/02-settings-currency-vat.md")
    elif not cur:
        add("warn", "Money", "No currency set", fix="Set POS_CURRENCY in .env")
    else:
        add("ok", "Money", f"Currency set to {cur}")

    vat = env.get("POS_VAT_RATE", "")
    if vat == DEFAULTS["POS_VAT_RATE"]:
        add("warn", "Money", "VAT rate is still the default Swiss 8.1%",
            "Confirm 8.1% is correct for your country (IT 22, DE 19, …).",
            "Set POS_VAT_RATE + POS_VAT_RATE_REDUCED in .env — onboarding/02-settings-currency-vat.md")
    elif not vat:
        add("warn", "Money", "No VAT rate set", fix="Set POS_VAT_RATE in .env")
    else:
        add("ok", "Money", f"VAT standard rate set to {vat}%")

    # ---- 📦 Catalog + demo seed ------------------------------------------
    if str(env.get("HX_SEED_DEMO", "true")).lower() not in ("false", "0", "no"):
        add("warn", "Catalog", "Demo catalog seeding is still ON",
            "HX_SEED_DEMO isn't false — you'll keep getting the demo 'Artemis' products.",
            "Set HX_SEED_DEMO=false, then docker compose down -v && up -d for a clean shop.")

    if db_reachable:
        store = psql(env, "SELECT store_name FROM store_settings LIMIT 1") or ""
        if store:
            if store.strip().lower().startswith("artemis"):
                add("warn", "Identity", f"Shop name is still the demo ('{store.strip()}')",
                    fix="Set your real shop name on the Settings page — onboarding/01-shop-profile.md")
            else:
                add("ok", "Identity", f"Shop name set to '{store.strip()}'")
        vatno = psql(env, "SELECT coalesce(vat_number,'') FROM store_settings LIMIT 1") or ""
        if (not vatno) or "XXX" in vatno.upper():
            add("fail", "Identity", "VAT number is a placeholder",
                f"store_settings.vat_number = '{vatno}' — receipts need your real VAT number.",
                "Enter your VAT number on the Settings page.")
        else:
            add("ok", "Identity", "VAT number is set")

        pcount = psql(env, "SELECT count(*) FROM products")
        try:
            n = int(pcount)
            if n == 0:
                add("warn", "Catalog", "The catalog is empty",
                    fix="Add your products — onboarding/05-catalog-loading.md")
            else:
                add("info", "Catalog", f"{n} products in the catalog")
        except (TypeError, ValueError):
            pass

        audit = psql(env, "SELECT to_regclass('public.audit_log') IS NOT NULL")
        if audit == "t":
            add("ok", "Change-log", "Audit log (who/when/what) is installed")
        else:
            add("warn", "Change-log", "Audit log not installed",
                fix="Run ./scripts/standup.sh")
    else:
        add("info", "Database", "Couldn't read the database — is Banco running?",
            "Only the .env checks ran. Start it (docker compose up -d) for the full picture.")

    return F


def summarize(F):
    n = {"fail": 0, "warn": 0, "ok": 0, "info": 0}
    for f in F:
        n[f["sev"]] += 1
    total = n["fail"] + n["warn"] + n["ok"]
    ready = round(100 * n["ok"] / total) if total else 0
    return n, ready


def cmd_report(F):
    n, ready = summarize(F)
    print(f"\n{C['b']}🩺 Banco Doctor — how ready is this shop?{C['x']}\n")
    order = sorted(range(len(F)), key=lambda i: (F[i]["section"], RANK[F[i]["sev"]]))
    section = None
    for i in order:
        f = F[i]
        if f["section"] != section:
            section = f["section"]
            print(f"{C['b']}{section}{C['x']}")
        icon, col = SEV[f["sev"]]
        print(f"  {icon} {C[col]}{f['title']}{C['x']}")
        if f["sev"] in ("fail", "warn"):
            if f["detail"]:
                print(f"       {C['dim']}{f['detail']}{C['x']}")
            if f["fix"]:
                print(f"       {C['grn']}→ {f['fix']}{C['x']}")
    print(f"\n{C['b']}Score:{C['x']} {C['grn']}✅ {n['ok']} done{C['x']} · "
          f"{C['yel']}⚠️  {n['warn']} to confirm{C['x']} · {C['red']}❌ {n['fail']} blockers{C['x']}")
    bar = "█" * (ready // 5) + "░" * (20 - ready // 5)
    print(f"{C['b']}Ready:{C['x']} {bar} {ready}%")
    if n["fail"]:
        print(f"\n{C['red']}Not go-live yet — clear the ❌ blockers first.{C['x']}")
    elif n["warn"]:
        print(f"\n{C['yel']}Close — confirm the ⚠️  items and you're ready.{C['x']}")
    else:
        print(f"\n{C['grn']}🎉 Everything the doctor can see is set. Run the go-live checklist to be sure.{C['x']}")
    print(f"\n{C['dim']}Tip: `--dump` gives a safe snapshot to paste into any AI (Claude/ChatGPT/Ollama) for coaching.{C['x']}")


def cmd_dump(F):
    """A SAFE, secret-free snapshot to paste into the rookie's own AI."""
    n, ready = summarize(F)
    lines = ["BANCO SETUP SNAPSHOT (safe to share — no passwords/keys included)",
             f"readiness: {ready}%  |  done {n['ok']}  confirm {n['warn']}  blockers {n['fail']}", ""]
    for f in F:
        lines.append(f"[{f['sev'].upper()}] {f['section']}: {f['title']}"
                     + (f" — {f['detail']}" if f['detail'] else ""))
    print("\n".join(lines))


COACH_SYSTEM = (
    "You are the Banco Setup Coach. Banco is a small-shop point-of-sale the owner runs and OWNS. "
    "Below is a factual snapshot of what's still unset on their install (produced by a checker that reads "
    "the real config — trust it as ground truth; do not contradict it or claim things are fine that it marks "
    "as blockers). Coach the owner in plain, warm, non-technical language: what to fix FIRST (blockers/❌ "
    "before ⚠️), why it matters for a real shop, and the single next action. Be concise and encouraging. "
    "The most important thing is always backups (own-your-data) and correct VAT."
)


def cmd_explain(env, F):
    dump_lines = []
    for f in F:
        dump_lines.append(f"[{f['sev'].upper()}] {f['section']}: {f['title']}"
                          + (f" — {f['detail']}" if f['detail'] else ""))
    snapshot = "\n".join(dump_lines)
    url = (env.get("OLLAMA_TURBO_URL") or "").rstrip("/")
    key = env.get("BH_OLLAMA_KEY") or ""
    model = env.get("OLLAMA_MODEL") or "gpt-oss:120b"
    if not (url and key):
        print("No Ollama Turbo configured (OLLAMA_TURBO_URL + BH_OLLAMA_KEY in .env).")
        print("Use `--dump` and paste the snapshot into any AI you have — see onboarding/ai-coach/.")
        return
    import urllib.request
    endpoint = url + "/v1/chat/completions" if not url.endswith("/chat/completions") else url
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": COACH_SYSTEM},
        {"role": "user", "content": "Here is my Banco setup snapshot:\n\n" + snapshot},
    ]}).encode()
    req = urllib.request.Request(endpoint, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        msg = data["choices"][0]["message"]["content"]
        print("\n🧠 Your AI coach says:\n")
        print(msg.strip())
    except Exception as e:
        print(f"Couldn't reach your Ollama Turbo ({e}).")
        print("Use `--dump` and paste into any AI you have — see onboarding/ai-coach/.")


def main():
    ap = argparse.ArgumentParser(description="banco-doctor — what's left to set up?")
    ap.add_argument("--dump", action="store_true", help="print a safe, secret-free snapshot for your own AI")
    ap.add_argument("--explain", action="store_true", help="let your configured Ollama Turbo coach you")
    args = ap.parse_args()

    env = read_env(ENV_PATH)
    if not env:
        print("No .env found. Run `cp .env.example .env` first (from the repo root).")
        sys.exit(1)
    F = build_findings(env)

    if args.dump:
        cmd_dump(F)
    elif args.explain:
        cmd_explain(env, F)
    else:
        cmd_report(F)

    if not (args.dump or args.explain):
        n, _ = summarize(F)
        sys.exit(1 if n["fail"] else 0)


if __name__ == "__main__":
    main()
