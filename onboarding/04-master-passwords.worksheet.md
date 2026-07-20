# 4 · Master passwords & keys — SECURE worksheet

> ⛔ **DO NOT type your real passwords into this file and commit it.** This repo may be public. Real secrets in
> git = a breach. This is a *checklist of what to record* — put the actual values in a **password manager**
> (KeePass, Bitwarden, 1Password) or a sealed offline note. If you must keep a filled copy on disk, save it
> **outside** this repo (or name it `*.local.md` — those are git-ignored here).

Banco has a handful of "master" secrets. Lose them and you can lose access to your own shop; leak them and
someone else gets in. Set strong values, and record where each one lives.

## The list to record (in your password manager)

### App & database (`.env` file)
- [ ] `SECRET_KEY` — the app's signing secret. Generate: `openssl rand -hex 32`.
- [ ] `POSTGRES_PASSWORD` — your database password.
- [ ] `MINIO_SECRET_KEY` — the image-store password.

### Login system (Keycloak)
- [ ] `HX_SUPER_PASSWORD` — the Keycloak **admin** password (also in `.env`; must match Keycloak).
- [ ] Each **staff login** password (pam→your-cashier, etc.) — or note "staff set their own".

### Backups & recovery (the ones you must never lose)
- [ ] **Backblaze B2 account** login.
- [ ] **B2 application key** (keyID + the secret) used to upload backups — *write* key.
- [ ] **B2 read-only key** (keyID + secret) used to *restore* — hand this to whoever might recover the shop.
- [ ] **Backup GPG passphrase** — the password your backups are encrypted with. **If you lose this, your
      backups are unreadable forever.** Store it in at least two safe places.

## How strong?
- Use a password manager to **generate** long random values (20+ characters) for the machine secrets.
- The **backup GPG passphrase** is the crown jewel — long, unique, and stored redundantly (password manager +
  a sealed offline copy). Test that you can actually decrypt a backup with it (see [guide 6](06-own-your-data-backups.md)).

## After you set them
1. Update the values in `.env` and in Keycloak.
2. `docker compose up -d` to apply.
3. Confirm you can still log in (app + Keycloak admin) with the new passwords.
4. Record every value in your password manager. Delete any temporary plaintext copies.

> The single worst day in a small shop's tech life is "we're locked out and the person who set it up is gone."
> This worksheet, filled into a password manager two people can reach, is how you never have that day.
