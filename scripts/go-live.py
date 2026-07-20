#!/usr/bin/env python3
# ============================================================================
# go-live — take Banco from your laptop to a real address on the internet.
#
#   python3 scripts/go-live.py
#
# Banco is an opinionated framework: it prescribes the whole go-live stack so you
# don't have to evaluate five vendors. The stack is —
#   • Hetzner  — your server (German cloud; ~€5/mo; your shop's data stays in the EU)
#   • Porkbun  — your domain + DNS (cheap, honest, free WHOIS privacy, a DNS panel
#                a human can read)
#   • Caddy    — automatic HTTPS (fetches + renews Let's Encrypt certs itself)
#   • Resend   — your email, for Keycloak password-resets + staff setup links
#   • B2       — your encrypted backups (guide 06)
# Every piece is something YOU own and can walk away with. No vendor owns you.
#
# This wizard asks the handful of things that are yours (your domain, your server's
# IP, your Resend key), then writes .env + generates ./Caddyfile and tells you the
# exact DNS records to create. Deploy with ./scripts/deploy-prod.sh (backup first,
# gate after). Zero dependencies — plain Python 3 stdlib.
# ============================================================================
import os
import re
import shutil
import sys
from getpass import getpass

# A valid DNS hostname: dot-separated labels, letters/digits/hyphens only, no spaces.
# Guards against voice/typo junk (e.g. "banco-auth.g. wolfhold.app") reaching Keycloak,
# which 500s on a hostname it can't parse into a URL.
_HOST_RE = re.compile(
    r"^(?=.{1,253}$)[a-z0-9](-?[a-z0-9])*(\.[a-z0-9](-?[a-z0-9])*)+$")


def valid_host(h):
    return bool(_HOST_RE.match((h or "").strip().lower()))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, ".env")
CADDYFILE = os.path.join(ROOT, "Caddyfile")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "cyan": "\033[36m", "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


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
    if not os.path.exists(ENV):
        print(f"{C['red']}❌ No .env — run scripts/init-banco.py first (set up the shop before going live).{C['x']}")
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


def ask(prompt, default=""):
    d = f" {C['dim']}[{default}]{C['x']}" if default else f" {C['dim']}[blank]{C['x']}"
    try:
        return input(f"  {prompt}{d}: ").strip() or default
    except EOFError:
        return default


def ask_secret(prompt, default=""):
    hint = " [keep current]" if default else ""
    try:
        return getpass(f"  {prompt}{hint} (hidden): ").strip() or default
    except EOFError:
        return default


def ask_host(prompt, default=""):
    """Like ask(), but only accepts a syntactically valid hostname (no spaces / junk)."""
    if default and not valid_host(default):
        default = ""   # never re-offer a polluted value
    while True:
        v = ask(prompt, default).strip().lower().rstrip(".").replace(" ", "")
        if not v:
            return ""
        if valid_host(v):
            return v
        print(f"  {C['yel']}✗ '{v}' isn't a valid hostname — letters, digits, dots and hyphens "
              f"only (e.g. banco.wolfhold.app). Try again.{C['x']}")
        default = ""


def header(t):
    print(f"\n{C['b']}{C['cyan']}── {t} ──{C['x']}")


def main():
    print(f"\n{C['b']}🚀 Banco go-live{C['x']}")
    print(f"{C['dim']}Take the shop from localhost to a real HTTPS address. The Banco stack is "
          f"prescribed:\n  Hetzner (server) · Porkbun (domain) · Caddy (HTTPS) · Resend (email) · B2 (backups).{C['x']}")

    if not os.path.exists(ENV):
        print(f"{C['red']}❌ No .env yet — run `python3 scripts/init-banco.py` first.{C['x']}")
        return 1
    cur = parse_env(ENV)

    # --- environment (drives the subdomain prefix) -------------------------
    header("Which environment?")
    print(f"  {C['cyan']}1{C['x']}) production  {C['dim']}— the real shop → prefix 'banco.'{C['x']}")
    print(f"  {C['cyan']}2{C['x']}) sandbox     {C['dim']}— a public demo/training copy → prefix 'sandbox-banco.'{C['x']}")
    envc = ask("pick", "1")
    is_sandbox = envc.strip() in ("2", "sandbox", "sbx")
    banco_env = "sandbox" if is_sandbox else "production"
    prefix = "sandbox-banco" if is_sandbox else "banco"

    # --- domain + derived hostnames ----------------------------------------
    header("Your domain (from Porkbun)")
    print(f"  {C['dim']}The base domain you registered — Banco puts the shop on a subdomain of it.{C['x']}")
    # try to infer the base domain from an existing APP_PUBLIC_HOST
    base_default = ""
    prev = cur.get("APP_PUBLIC_HOST", "")
    if prev and "." in prev:
        base_default = prev.split(".", 1)[1]
    base = ask_host("Base domain (e.g. wolfhold.app)", base_default)
    if not base:
        print(f"  {C['yel']}A valid domain is required to go live. Register one at porkbun.com first, then re-run.{C['x']}")
        return 0

    app_host = ask_host("Shop address", f"{prefix}.{base}")
    kc_host = ask_host("Keycloak (login) address", f"{prefix}-auth.{base}")
    if not (app_host and kc_host):
        print(f"  {C['yel']}Both addresses are required. Re-run when you're ready.{C['x']}")
        return 0

    # --- server + contact ---------------------------------------------------
    header("Your server (from Hetzner)")
    server_ip = ask("Server public IP (Hetzner shows it on the console)", cur.get("_SERVER_IP", ""))
    acme_email = ask("Contact email for Let's Encrypt (cert-renewal warnings)",
                     cur.get("ACME_EMAIL", "") or f"admin@{base}")

    # --- Resend email -------------------------------------------------------
    header("Email — Resend (resend.com)")
    print(f"  {C['dim']}Keycloak sends password-resets + staff setup links through Resend. Create an API\n"
          f"  key at resend.com and verify your sending domain (it gives you DNS records to add at\n"
          f"  Porkbun — same place as the A records below). Skippable now; needed for password resets.{C['x']}")
    smtp_key = ""
    if ask("Configure Resend now? (y/N)", "n").lower() in ("y", "yes"):
        smtp_key = ask_secret("Resend API key (re_…)", cur.get("SMTP_PASSWORD", ""))
        smtp_from = ask("From address (a verified Resend domain)",
                        cur.get("SMTP_FROM", "") or f"noreply@{base}")
    else:
        smtp_from = cur.get("SMTP_FROM", "")
        print(f"  {C['dim']}skipped — re-run go-live.py later to wire email.{C['x']}")

    # --- write .env ---------------------------------------------------------
    ov = {
        "BANCO_ENV": banco_env,
        "APP_PUBLIC_HOST": app_host,
        "KC_PUBLIC_HOST": kc_host,
        "POS_KC_PUBLIC_URL": f"https://{kc_host}",
        "ACME_EMAIL": acme_email,
        "SMTP_HOST": "smtp.resend.com",
        "SMTP_PORT": cur.get("SMTP_PORT", "587") or "587",
        "SMTP_USER": "resend",
        "SMTP_FROM": smtp_from,
        "SMTP_FROM_NAME": cur.get("SMTP_FROM_NAME", "Banco") or "Banco",
    }
    if smtp_key:
        ov["SMTP_PASSWORD"] = smtp_key
    if not write_env(ov):
        return 1

    # --- generate ./Caddyfile ----------------------------------------------
    caddy = (
        "# Generated by scripts/go-live.py — automatic HTTPS via Let's Encrypt.\n"
        "{\n"
        f"\temail {acme_email}\n"
        "}\n\n"
        f"# The shop — what customers and staff open.\n"
        f"{app_host} {{\n"
        "\treverse_proxy app:8000\n"
        "}\n\n"
        f"# Keycloak — login + password-reset links.\n"
        f"{kc_host} {{\n"
        "\treverse_proxy keycloak:8080\n"
        "}\n"
    )
    if os.path.exists(CADDYFILE):
        shutil.copy2(CADDYFILE, CADDYFILE + ".bak")
    with open(CADDYFILE, "w", encoding="utf-8") as f:
        f.write(caddy)

    # --- summary + the human to-do list ------------------------------------
    ip = server_ip or "<your server IP>"
    print(f"\n{C['b']}{C['grn']}✅ Wrote .env + ./Caddyfile{C['x']}  {C['dim']}({banco_env}){C['x']}")
    print(f"  shop:  {C['b']}https://{app_host}{C['x']}")
    print(f"  login: {C['b']}https://{kc_host}{C['x']}")
    print(f"  email: {'Resend ✓' if (smtp_key or cur.get('SMTP_PASSWORD')) else C['yel']+'not wired (password resets off)'+C['x']}")

    print(f"\n{C['b']}Now do these — the parts only you can do:{C['x']}")
    print(f"\n  {C['cyan']}1. DNS — at Porkbun, create two A records:{C['x']}")
    print(f"       {C['b']}{app_host}{C['x']:<4}  A   {ip}")
    print(f"       {C['b']}{kc_host}{C['x']:<4}  A   {ip}")
    print(f"       {C['dim']}(or a single wildcard  *.{base}  A  {ip}  covers both.){C['x']}")
    print(f"\n  {C['cyan']}2. Firewall — on the Hetzner server, allow only 22, 80, 443:{C['x']}")
    print(f"       {C['dim']}sudo ufw allow 22,80,443/tcp && sudo ufw enable{C['x']}")
    print(f"       {C['dim']}(keeps the raw app/DB ports off the public internet — Caddy is the only door.){C['x']}")
    if smtp_key:
        print(f"\n  {C['cyan']}3. Resend — verify your domain{C['x']} {C['dim']}at resend.com → Domains → add {base},{C['x']}")
        print(f"       {C['dim']}then paste the SPF/DKIM records it shows into Porkbun (same DNS panel).{C['x']}")
    print(f"\n  {C['cyan']}{'4' if smtp_key else '3'}. Deploy:{C['x']}")
    print(f"       {C['b']}./scripts/deploy-prod.sh{C['x']}   {C['dim']}# backup first → build → verify it's live{C['x']}")
    print(f"\n  {C['dim']}First HTTPS hit can take ~1 min while Caddy fetches the certificate. Give DNS a few{C['x']}")
    print(f"  {C['dim']}minutes to propagate before you deploy, or the cert request will fail and retry.{C['x']}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C['yel']}cancelled — no changes written.{C['x']}")
        sys.exit(130)
