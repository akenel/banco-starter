# Own Your Banco — Quickstart

Stand up a complete Banco POS on one machine, then (optionally) restore your own
shop's data from a Backblaze B2 backup. This is the whole point of Banco being
yours: with this repo, a backup key, and the steps below, **anyone competent can
bring the shop back from zero** — no vendor required.

Everything runs in Docker. You need:

- **Docker** + **Docker Compose** (Docker Desktop, or Docker Engine + the compose plugin)
- ~2 GB free disk, ports `8000` (POS), `8080` (Keycloak), `9000/9001` (MinIO), `5432` (Postgres) free
- That's it. No Python, Node, or database tooling on the host.

---

## 1. Configure

**Easiest — the setup wizard.** It asks a few questions (shop name, currency, VAT, admin password, and
optionally your LLM and Backblaze B2 keys), keeps secrets hidden as you type, and writes `.env` for you:

```bash
python3 scripts/init-banco.py
```

Press Enter to accept each default; skip the optional sections. Re-run it any time to change settings.

**Or by hand** (no Python needed — the app itself runs entirely in Docker):

```bash
cp .env.example .env
```

> ⚠️ **Either way, do this FIRST — before `docker compose up`.** There is no `.env` until you create it, and
> the app won't start without one. It's the #1 skipped step.

The defaults in `.env.example` stand up a working local stack as-is. For a laptop
demo you can leave them. **Before exposing anything to a network** (a real shop on the internet), you must change
every `🔒 CHANGE` value AND put it behind HTTPS — see **[onboarding/07-going-to-production.md](onboarding/07-going-to-production.md)**.
The localhost demo runs over plain HTTP on purpose; that is **not** safe for a public shop.

## 2. Start

```bash
docker compose up --build -d
```

First run builds the app image and pulls Postgres, Keycloak, and MinIO (a few
minutes). Keycloak auto-imports the POS realm from `keycloak/import/` on first boot.
Watch it come up:

```bash
docker compose ps           # all should become healthy
docker compose logs -f app  # look for "HelixNet Core READY to serve requests"
```

## 3. Install the audit log

```bash
./scripts/standup.sh
```

This waits for the app, then installs the who/when/what change-log (triggers +
`audit_log` table). The app's own schema auto-creates on first boot — this just
adds the audit machine.

## 4. Open it

| What | URL |
|------|-----|
| **POS** | http://localhost:8000/pos |
| Audit cockpit | http://localhost:8000/pos/audit |
| System / health | http://localhost:8000/system |
| Keycloak admin | http://localhost:8080  (admin / your `HX_SUPER_PASSWORD`) |
| MinIO console | http://localhost:9001 |

### Demo logins (from the imported realm)

| User | Password | Role |
|------|----------|------|
| `pam` | `pam` | cashier |
| `ralph` | `ralph` | manager |
| `michael` | `michael` | developer |
| `felix` | `felix` | admin (all roles) |

> These are **local demo** credentials baked into `keycloak/import/realm-export.json`.
> For any real use, change them in Keycloak (or edit the realm export before first boot).

---

## Own your data — restore a real backup from B2

Banco's nightly backups are `pg_dump → gzip → GPG AES256`, pushed to **your** B2
bucket. To bring a real shop up from a backup on a clean machine:

1. Put your **read-only** B2 key + the backup passphrase in `.env` (the `B2_*` and
   `BACKUP_GPG_PASSPHRASE` section). Use a read-only key — never a write or master key.
2. Bring up infra only, restore, then start the app onto the restored data:

```bash
docker compose up -d postgres keycloak minio   # infra, not the app yet
./scripts/restore-from-b2.sh                    # newest backup (or pass a filename)
docker compose up -d app                        # app boots onto your real data
./scripts/standup.sh                            # (re)apply the audit machine
```

`restore-from-b2.sh` downloads the newest `*.sql.gz.gpg` from your bucket, recreates
a clean database, and pipes `gpg --decrypt | gunzip | psql` into it — the same chain
documented in the DR brief. You need the `b2` CLI (`pip install b2`) and `gpg` on the
host for this step.

---

## BYO-brain (optional LLM)

Snap-fill (photo → product), catalog enrichment, and share teasers use an LLM. Leave
`BH_OLLAMA_KEY`/`OLLAMA_*` blank and those features degrade gracefully — **the POS,
checkout, and reports are unaffected**. To enable them, set your Ollama Turbo key
(`BH_OLLAMA_KEY`) or point `OLLAMA_URL` at a local Ollama.

---

## Stop / reset

```bash
docker compose down                 # stop, keep data
docker compose down -v              # stop AND wipe all data volumes (fresh start)
```

## Troubleshooting

- **Login redirects to a wrong Keycloak host** — make sure `POS_KC_PUBLIC_URL` in
  `.env` is `http://localhost:8080` (the browser-facing KC origin for a local stand-up).
- **App unhealthy / DB errors on first boot** — Postgres may still be initializing;
  the app retries. Check `docker compose logs postgres` then `docker compose logs app`.
- **Keycloak didn't import the realm** — the import runs only on a *fresh* Keycloak
  volume. `docker compose down -v` then `up` to re-import.
- **Empty catalog** — set `HX_SEED_DEMO=true` for a demo catalog, or restore a backup.
