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
cp .env.example .env
docker compose up --build -d
./scripts/standup.sh
```

Then open **http://localhost:8000/pos** and log in as `pam` / `pam`.

Full walkthrough, demo logins, and the B2 restore path: **[QUICKSTART.md](QUICKSTART.md)**.

## What's in the box

| Path | What |
|------|------|
| `compose.yml` | The minimal stack: postgres + keycloak + minio + app |
| `Dockerfile` / `entrypoint.sh` | The app image (FastAPI, Python 3.11) |
| `.env.example` | Every setting, with safe local defaults |
| `keycloak/import/` | The POS realm (clients, roles, demo users) — auto-imported |
| `scripts/standup.sh` | Post-boot: install the audit log |
| `scripts/restore-from-b2.sh` | Own-your-data: restore a backup from Backblaze B2 |
| `scripts/db/audit_log_setup.sql` | The universal change-log machine |
| `src/` | The application |

## Stack

FastAPI · SQLAlchemy (async, asyncpg) · Postgres 17 · Keycloak 24 (OIDC / RS256) ·
MinIO (S3-compatible) · Jinja2 + Alpine.js (vendored — no node build).
