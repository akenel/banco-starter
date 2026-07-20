# 7 · Going to production — domain, HTTPS & locking it down

> ⚠️ **Read this before you put Banco on the internet.** The localhost demo runs over **plain HTTP** on purpose —
> that's fine on your own laptop, but it is **not safe for a real shop**. A public POS needs a domain, HTTPS
> (encryption), and Keycloak running in **production mode**. This is real system-administration work — it's the
> point where many shops bring in an IT person for a day. That's normal and worth it.

This guide is the **shape** of a secure production deployment — the decisions and the moving parts — not a
one-command turnkey (your domain, server, and DNS are yours to wire). The reference production shop runs exactly
this pattern.

## What you'll need (the shopping list)

| Thing | What / where | Rough cost |
|-------|--------------|-----------|
| A **server** | A small VPS with a public IP (Hetzner, DigitalOcean, …), 4 GB+ RAM, Linux | ~€5–15/mo |
| A **domain** | From a registrar — **Porkbun**, Namecheap, Cloudflare… | ~€10/yr |
| A **Backblaze B2** account | Your backup vault ([guide 6](06-own-your-data-backups.md)) | free tier is plenty |
| ~**a day** + maybe IT help | DNS + HTTPS + Keycloak prod config is fiddly the first time | — |

## Step 1 · Pick your domains (the sandbox → staging → prod pattern)

Don't run one environment. Run **three**, so you can test safely before touching the real till:

```
sandbox.yourshop.com   ← play area — break things here
staging.yourshop.com   ← final rehearsal — mirrors prod
yourshop.com           ← the real shop (or pos.yourshop.com)
```
At your registrar (Porkbun etc.), point each name's **DNS A record** at your server's public IP. (Start with just
prod if you like; add sandbox/staging when you're ready to iterate safely.)

## Step 2 · Put a reverse proxy in front (this is where HTTPS comes from)

Banco itself speaks HTTP. A **reverse proxy** sits in front, terminates HTTPS, and gets free certificates from
**Let's Encrypt** automatically. **Caddy** is the easiest — it does HTTPS with zero certificate wrangling. A
minimal `Caddyfile`:

```caddy
yourshop.com {
    reverse_proxy localhost:8000        # the Banco app
}
auth.yourshop.com {
    reverse_proxy localhost:8080        # Keycloak
}
```
Point Banco (`APP_HOST_PORT=8000`) and Keycloak (`KC_HOST_PORT=8080`) at localhost only, and let Caddy face the
world on 80/443. Caddy fetches + renews the Let's Encrypt certs for you. (Traefik or nginx + certbot also work —
Caddy is just the least painful.)

## Step 3 · Bolt Keycloak down (production mode)

The demo runs Keycloak in `start-dev` (insecure, HTTP). In production it must run in **production mode** behind
your HTTPS proxy. The key changes to the keycloak service:

- Command: **`start`** (not `start-dev`) `--optimized`
- `KC_HOSTNAME=https://auth.yourshop.com` — its real public address
- `KC_PROXY_HEADERS=xforwarded` and `KC_HTTP_ENABLED=true` — it trusts the proxy for TLS termination
- Strong `KEYCLOAK_ADMIN_PASSWORD` (never the demo default)

Then, in the realm, **update the redirect URIs** on the `helix_pos_web` client from `localhost:8000` to your real
domain (`https://yourshop.com/pos/callback`, plus `https://yourshop.com/*`). Log into the Keycloak admin console →
realm `kc-pos-realm-dev` → Clients → `helix_pos_web` → add your production URLs. **Login will fail until these
match your real domain** — it's the #1 production snag.

## Step 4 · Point Banco at the real URLs (`.env`)

```ini
FASTAPI_BASE_URL=https://yourshop.com
POS_KC_PUBLIC_URL=https://auth.yourshop.com   # the browser-facing Keycloak address
KEYCLOAK_SERVER_URL=http://keycloak:8080      # in-network (server-to-server) stays internal
```
The split matters: browsers use the **public HTTPS** Keycloak address; the app talks to Keycloak **inside** the
Docker network. Get `POS_KC_PUBLIC_URL` right or the login button sends people to the wrong place.

## Step 5 · Production security checklist

- [ ] **HTTPS everywhere** — no plain-HTTP access to the app or Keycloak from outside.
- [ ] **All default passwords changed** — run `python3 scripts/banco-doctor.py`, get **0 blockers**.
- [ ] **Keycloak in `start` (production) mode**, not `start-dev`.
- [ ] **Realm redirect URIs** updated to your real domain.
- [ ] **Firewall**: only 80/443 (and SSH) open to the world; Postgres/MinIO/Keycloak ports **not** public.
- [ ] **Backups ON and restored once** ([guide 6](06-own-your-data-backups.md)) — to your own B2.
- [ ] **Demo users disabled** ([guide 3](03-users-and-roles.md)).
- [ ] **The server itself** kept updated (`apt upgrade`), automatic security updates on.

---

### The honest word
This step is a real jump from "runs on my laptop" to "a secure service on the internet." If DNS, reverse
proxies, and TLS aren't your world, **this is the right place to pay someone for a day** — and then you own it.
Everything above is standard, well-trodden infrastructure; none of it is Banco-specific magic. Get it right once
and it just runs.
