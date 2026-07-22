# Banco POS — starter

A production-grade point-of-sale you can **stand up yourself and own outright**.
FastAPI + Postgres + Keycloak, one `docker compose up`.

Banco runs a real Swiss head-shop today: barcode checkout, catalog + inventory,
supplier sourcing, a guest kiosk, snap-a-photo product creation, VAT-correct
receipts, daily close-out, and a full **who/when/what audit log** with one-click
revert. This starter is the same application, packaged so you can run it on your
own machine and restore your own data from your own backups.

## Why "own it"?

The usual fear with a small vendor is *"what if they vanish?"* Banco's answer is
ownership, not a promise:

- **The code is yours** — this repo stands the whole thing up.
- **The data is yours** — nightly encrypted backups live in *your* Backblaze B2
  bucket, and `scripts/restore-from-b2.sh` brings a shop back from zero with a key
  you hold.
- **The runbook is yours** — [`QUICKSTART.md`](QUICKSTART.md) is the whole recovery.

You can't clone SAP. You can clone this.

## Quickstart

```bash
python3 scripts/init-banco.py     # setup wizard — writes .env for you (or: cp .env.example .env)
./scripts/rebuild.sh              # build + start, stamped with the real commit (raw `docker compose up --build -d` also works)
./scripts/standup.sh              # audit log + a "✅ safe to test → go here" verdict
```

Then open **http://localhost:8000/pos** and log in as `pam` / `pam`.

Full walkthrough, demo logins, and the B2 restore path: **[QUICKSTART.md](QUICKSTART.md)**.

## Setting up a real shop?

The **[onboarding/](onboarding/)** kit takes you from this demo to *your* shop — currency, VAT, staff logins,
passwords, catalog, and your own backups — with an [implementation roadmap](onboarding/IMPLEMENTATION-ROADMAP.md),
a [go-live checklist](onboarding/GO-LIVE-CHECKLIST.md), and a click-through
[test runbook](onboarding/testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html). Start at
**[onboarding/README.md](onboarding/README.md)**.

## What's in the box

| Path | What |
|------|------|
| `compose.yml` | The minimal stack: postgres + keycloak + minio + app |
| `Dockerfile` / `entrypoint.sh` | The app image (FastAPI, Python 3.11) |
| `.env.example` | Every setting, with safe local defaults |
| `keycloak/import/` | The POS realm (clients, roles, demo users) — auto-imported |
| `scripts/init-banco.py` | Setup wizard — asks a few questions, writes your `.env` (secrets stay hidden) |
| `scripts/standup.sh` | Post-boot: install the audit log, then run the smoke test |
| `scripts/postboot-check.py` | Smoke test — "is it up & safe to test?" pokes the live stack, prints one verdict |
| `scripts/banco-doctor.py` | "What's left to set up?" — reads your live config, flags every default (✅/⚠️/❌) |
| `scripts/backup-to-b2.sh` | Own-your-data: make an encrypted backup → Backblaze B2 |
| `scripts/restore-from-b2.sh` | Own-your-data: restore a backup from Backblaze B2 |
| `onboarding/` | The new-shop implementation kit (roadmap, checklist, guides, testsheet) |
| `scripts/db/audit_log_setup.sql` | The universal change-log machine |
| `src/` | The application |

## Stack

FastAPI · SQLAlchemy (async, asyncpg) · Postgres 17 · Keycloak 24 (OIDC / RS256) ·
MinIO (S3-compatible) · Jinja2 + Alpine.js (vendored — no node build).

## License

Apache License 2.0 — see [LICENSE](LICENSE). Run it, modify it, self-host it,
redistribute it, freely. That's the whole point of "own it": no vendor can pull
the rug out from under your shop.

The **name** is the one thing reserved: "Banco" and "La Piazza" are trademarks of
Angelo Kenel (Apache-2.0 §6, see [NOTICE](NOTICE)). Build on the code all you
like — just don't ship your fork *as* "Banco" without asking. Bundled components
(Postgres, Keycloak, FastAPI, MinIO, Caddy, …) keep their own licenses.
