# 7 · Going live — your shop on the internet

> ⚠️ The localhost demo runs over plain **HTTP** on purpose — fine on your laptop, **not safe for a real shop**.
> Going live means a domain, HTTPS, and Keycloak in production mode. Banco makes this two commands instead of a
> day of sysadmin — but you still do the parts that are genuinely yours: buy a domain, rent a server, make a DNS
> record.

## The Banco stack (prescribed, not a menu)

Banco is an opinionated framework. Just as it prescribes **Postgres** and **Keycloak**, it prescribes the go-live
stack — so you don't burn a weekend comparing vendors. Each choice is deliberate, and each is something **you own
and can walk away with**:

| Piece | We use | Why this one |
|-------|--------|--------------|
| Server | **Hetzner** | German cloud, ~€5/mo for plenty. Your shop's data **stays in the EU** — a real GDPR answer for a Swiss/EU shop, not a US cloud. |
| Domain + DNS | **Porkbun** | Cheap, honest registrar. Free WHOIS privacy, and a DNS panel a normal person can actually read. |
| HTTPS | **Caddy** | Fetches and renews Let's Encrypt certificates **by itself**. Zero certificate wrangling. |
| Email | **Resend** | Keycloak password-resets + staff setup links. SMTP, an API key, done. |
| Backups | **Backblaze B2** | Your encrypted vault ([guide 6](06-own-your-data-backups.md)). |

Rough cost: **~€5–15/mo** (server) **+ ~€10/yr** (domain). Backups and email have free tiers that fit a shop.

## One shop, not three environments

You are running a till, not shipping software — so you run **one** production instance on `banco.yourdomain`.
That's it. (If you want a safe place to train staff or click around, add a second **sandbox** copy on
`sandbox-banco.yourdomain` — the wizard sets it up the same way. You do **not** need a "staging" environment; that's
a tool for people who ship code, and it lives on the developer's side, not in your shop.)

## Step 1 · Get the two things only you can get

1. **A server** — make a Hetzner Cloud account, create a **CX22** (2 vCPU / 4 GB, ~€5/mo), Ubuntu or Debian.
   Install Docker (see [guide 0](00-prerequisites.md)). Note its **public IP**.
2. **A domain** — register one at **Porkbun** (~€10/yr). You don't need to touch DNS yet — the wizard tells you
   exactly which record to make.

Clone Banco onto the server and set up the shop as usual: `python3 scripts/init-banco.py`.

## Step 2 · Run the go-live wizard

```bash
python3 scripts/go-live.py
```
It asks the handful of things that are yours — production or sandbox, your domain, your server's IP, your Resend
key — then **writes `.env` and generates `./Caddyfile`** for you, and prints your exact to-do list:

- **the two DNS A records** to create at Porkbun (`banco.yourdomain` and `banco-auth.yourdomain` → your server IP;
  or one wildcard `*.yourdomain`),
- **the firewall line** to lock the server to ports 22/80/443,
- **the Resend domain-verification** records (SPF/DKIM — they go in the same Porkbun DNS panel).

Make those DNS records now and give them a few minutes to propagate.

## Step 3 · Deploy

```bash
./scripts/deploy-prod.sh
```
This does it the safe way — the same discipline as the reference shop:

1. **Backup first** to your B2 (if it fails, the deploy stops — nothing changed).
2. **Build** (stamped with the real commit) and start the production stack: app + **Caddy** (HTTPS) + **Keycloak in
   production mode**.
3. **Teach Keycloak your domain** — adds `https://banco.yourdomain` to the login client automatically
   (`kc-set-redirect.py`). This is the historic #1 go-live snag ("Invalid redirect_uri"); Banco just handles it.
4. **Gate** — proves the app is actually serving *and* that the login screen's build stamp matches this commit, then
   checks that **HTTPS is live** on your public domain. It won't claim success on a restart that kept old code.

First HTTPS request can take ~1 minute while Caddy fetches the certificate. Then open `https://banco.yourdomain`,
log in, and you're a real shop on the internet.

> **Updating later:** `git pull` on the server, then `./scripts/deploy-prod.sh` again. Backup-first + gate every time.

## Step 4 · Lock-down checklist

- [ ] **Firewall**: only 22/80/443 open (`sudo ufw allow 22,80,443/tcp && sudo ufw enable`). Postgres/MinIO/Keycloak
      ports are **not** public — Caddy is the only door.
- [ ] **All default passwords changed** — `python3 scripts/banco-doctor.py` → **0 blockers**.
- [ ] **Backups ON and restored once** ([guide 6](06-own-your-data-backups.md)).
- [ ] **HTTPS everywhere** — the deploy's HTTPS gate is green.
- [ ] **Demo users removed** ([guide 3](03-users-and-roles.md)) — the `pam/pam` demo logins are for the laptop, not a
      real shop.
- [ ] **Email tested** — trigger a Keycloak password reset and confirm it arrives (Resend must show your domain
      **verified**).
- [ ] **Server updated** — automatic security updates on.

---

### The honest word
This is a real step up from "runs on my laptop." But the sysadmin parts that used to take a day — reverse proxy,
TLS, Keycloak prod mode, redirect URIs — Banco now does for you in `go-live.py` + `deploy-prod.sh`. What's left is
genuinely yours: a server, a domain, three DNS records. Do it once and it just runs — and every piece is yours to
keep.
