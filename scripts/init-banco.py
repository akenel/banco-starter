#!/usr/bin/env python3
# ============================================================================
# init-banco — the setup wizard. Clone → run this → answer a few questions →
# it writes your .env for you. No hand-editing, no guessing which of 40 vars
# matter. The friendly front door.
#
#   python3 scripts/init-banco.py
#
# What it does:
#   • asks the handful of things that are actually YOURS (shop name, currency,
#     VAT, admin password) with sensible defaults — press Enter to accept
#   • optional, skippable sections: bring-your-own-brain (an LLM for smart
#     lookups) and Backblaze B2 backups
#   • auto-generates the app signing secret
#   • takes secrets via a hidden prompt (never echoed, never printed back)
#   • writes .env (perms 0600), preserving every comment from .env.example,
#     backing up any existing .env first
#   • points you at the next command
#
# Re-runnable: if a .env already exists, its current values become the defaults,
# so this edits rather than wipes. Zero dependencies — plain Python 3 stdlib, so
# it runs on a bare machine before you've installed anything else.
# ============================================================================
import os
import secrets
import shutil
import sys
from getpass import getpass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE = os.path.join(ROOT, ".env.example")
ENV = os.path.join(ROOT, ".env")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "cyan": "\033[36m", "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def parse_env(path):
    """KEY=value dict from a .env-style file (comments/blanks ignored)."""
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


def ask(prompt, default=""):
    d = f" {C['dim']}[{default}]{C['x']}" if default else f" {C['dim']}[blank]{C['x']}"
    try:
        val = input(f"  {prompt}{d}: ").strip()
    except EOFError:
        val = ""
    return val or default


def ask_secret(prompt, default=""):
    """Hidden input. Empty keeps the current/default value (shown masked)."""
    hint = " [keep current]" if default else " [blank]"
    try:
        val = getpass(f"  {prompt}{hint} (typing hidden): ").strip()
    except EOFError:
        val = ""
    return val or default


def ask_yn(prompt, default=False):
    d = "Y/n" if default else "y/N"
    try:
        val = input(f"  {prompt} [{d}]: ").strip().lower()
    except EOFError:
        val = ""
    if not val:
        return default
    return val in ("y", "yes")


def header(title):
    print(f"\n{C['b']}{C['cyan']}── {title} ──{C['x']}")


def main():
    if not os.path.exists(EXAMPLE):
        print(f"{C['red']}❌ .env.example not found — run this from the banco-starter repo.{C['x']}")
        return 1

    print(f"\n{C['b']}🐺 Banco setup wizard{C['x']}")
    print(f"{C['dim']}Press Enter to accept the [default]. Optional sections can be skipped.{C['x']}")

    cur = parse_env(ENV)   # existing .env values become the defaults on a re-run
    if cur:
        print(f"{C['yel']}An existing .env was found — its values are the defaults below "
              f"(this edits, doesn't wipe).{C['x']}")

    ov = {}   # KEY -> value overrides to write

    # --- Shop identity + money ---------------------------------------------
    header("Your shop")
    ov["PROJECT_NAME"] = ask("Shop name", cur.get("PROJECT_NAME", "Banco POS"))
    ov["POS_CURRENCY"] = ask("Currency (CHF/EUR/USD…)", cur.get("POS_CURRENCY", "CHF"))
    ov["POS_LOCALE"] = ask("Locale (de-CH/it-IT/en-GB…)", cur.get("POS_LOCALE", "de-CH"))
    ov["POS_VAT_RATE"] = ask("Standard VAT rate %", cur.get("POS_VAT_RATE", "8.1"))
    ov["POS_VAT_RATE_REDUCED"] = ask("Reduced VAT rate %", cur.get("POS_VAT_RATE_REDUCED", "2.6"))
    seed = ask_yn("Load the demo catalog + staff for first boot?",
                  cur.get("HX_SEED_DEMO", "true").lower() not in ("false", "0", "no"))
    ov["HX_SEED_DEMO"] = "true" if seed else "false"

    # --- Security ----------------------------------------------------------
    header("Security")
    # App signing secret: keep an already-set real one, else generate.
    existing_secret = cur.get("SECRET_KEY", "")
    if existing_secret and "changeme" not in existing_secret:
        ov["SECRET_KEY"] = existing_secret
        print(f"  {C['grn']}✓ keeping your existing app signing secret{C['x']}")
    else:
        ov["SECRET_KEY"] = secrets.token_hex(32)
        print(f"  {C['grn']}✓ generated a fresh app signing secret (SECRET_KEY){C['x']}")

    print(f"  {C['dim']}Admin password logs into Keycloak + the app's admin. Blank keeps the "
          f"local-dev default — fine for a laptop, CHANGE before you expose it.{C['x']}")
    admin_pw = ask_secret("Admin password", cur.get("HX_SUPER_PASSWORD", ""))
    if admin_pw:
        # HX_SUPER_PASSWORD and KEYCLOAK_ADMIN_PASSWORD MUST match (compose + KC).
        ov["HX_SUPER_PASSWORD"] = admin_pw
        ov["KEYCLOAK_ADMIN_PASSWORD"] = admin_pw
    ov["HX_SUPER_EMAIL"] = ask("Admin email", cur.get("HX_SUPER_EMAIL", "admin@example.com"))

    # --- BYO-brain (optional) ----------------------------------------------
    header("Bring your own brain (optional LLM — highly recommended)")
    print(f"  {C['dim']}An LLM powers smart lookups: snap-a-photo→product, description enrich, "
          f"teasers. POS works fine without it. Easiest is your own Ollama Turbo account.{C['x']}")
    if ask_yn("Configure an LLM now?", bool(cur.get("BH_OLLAMA_KEY"))):
        ov["OLLAMA_TURBO_URL"] = ask("Ollama Turbo URL (blank = use a local Ollama)",
                                     cur.get("OLLAMA_TURBO_URL", ""))
        ov["BH_OLLAMA_KEY"] = ask_secret("Ollama Turbo API key", cur.get("BH_OLLAMA_KEY", ""))
        local = ask("Local Ollama URL (fallback)", cur.get("OLLAMA_URL", "http://ollama:11434"))
        ov["OLLAMA_URL"] = local
    else:
        print(f"  {C['dim']}skipped — AI features stay off; add keys later by re-running this.{C['x']}")

    # --- B2 backups (optional) ---------------------------------------------
    header("Off-site backups — Backblaze B2 (optional, recommended before go-live)")
    print(f"  {C['dim']}Encrypted nightly backups to YOUR bucket = you own your data. "
          f"Skippable now; needed before real go-live. See onboarding/06.{C['x']}")
    if ask_yn("Set up B2 backups now?", bool(cur.get("B2_KEY_ID"))):
        ov["B2_KEY_ID"] = ask("B2 key ID", cur.get("B2_KEY_ID", ""))
        ov["B2_APP_KEY"] = ask_secret("B2 application key", cur.get("B2_APP_KEY", ""))
        ov["B2_BUCKET"] = ask("B2 bucket name", cur.get("B2_BUCKET", ""))
        ov["B2_BUCKET_ID"] = ask("B2 bucket ID", cur.get("B2_BUCKET_ID", ""))
        ov["BACKUP_GPG_PASSPHRASE"] = ask_secret("Backup encryption passphrase",
                                                 cur.get("BACKUP_GPG_PASSPHRASE", ""))
    else:
        print(f"  {C['dim']}skipped — run this again when you're ready to wire backups.{C['x']}")

    # --- Write .env, preserving .env.example's comments --------------------
    out = []
    seen = set()
    for line in open(EXAMPLE, encoding="utf-8"):
        raw = line.rstrip("\n")
        if raw and not raw.lstrip().startswith("#") and "=" in raw:
            key = raw.split("=", 1)[0].strip()
            if key in ov:
                out.append(f"{key}={ov[key]}")
                seen.add(key)
                continue
            # not prompted: carry over an existing .env value if present, else example's
            if key in cur:
                out.append(f"{key}={cur[key]}")
                continue
        out.append(raw)

    if os.path.exists(ENV):
        shutil.copy2(ENV, ENV + ".bak")
        print(f"\n{C['dim']}(backed up your previous .env → .env.bak){C['x']}")

    with open(ENV, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    try:
        os.chmod(ENV, 0o600)   # holds secrets — owner-only
    except OSError:
        pass

    # --- Summary (no secrets) ----------------------------------------------
    print(f"\n{C['b']}{C['grn']}✅ Wrote .env{C['x']}  {C['dim']}(perms 0600, owner-only){C['x']}")
    print(f"  shop: {C['b']}{ov['PROJECT_NAME']}{C['x']}  ·  {ov['POS_CURRENCY']}  ·  "
          f"VAT {ov['POS_VAT_RATE']}/{ov['POS_VAT_RATE_REDUCED']}%  ·  demo={ov['HX_SEED_DEMO']}")
    print(f"  admin pw: {'set ✓' if admin_pw else C['yel']+'local-dev default ⚠ change before exposing'+C['x']}"
          f"   ·   LLM: {'configured ✓' if ov.get('BH_OLLAMA_KEY') else 'off'}"
          f"   ·   B2: {'configured ✓' if ov.get('B2_KEY_ID') else 'not yet'}")

    print(f"\n{C['b']}Next:{C['x']}")
    print(f"  1. {C['cyan']}./scripts/preflight.sh{C['x']}          {C['dim']}# machine has what it needs?{C['x']}")
    print(f"  2. {C['cyan']}docker compose up -d --build{C['x']}   {C['dim']}# stand up the stack{C['x']}")
    print(f"  3. {C['cyan']}./scripts/standup.sh{C['x']}            {C['dim']}# audit log + the ✅ safe-to-test verdict{C['x']}")
    print(f"  {C['dim']}Re-run this wizard any time to change settings; run banco-doctor.py before go-live.{C['x']}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C['yel']}cancelled — no changes written.{C['x']}")
        sys.exit(130)
