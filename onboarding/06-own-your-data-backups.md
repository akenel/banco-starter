# 6 · Own your data — backups & restore

This is the most important guide in the kit. A shop with backups can survive almost anything — a crashed disk,
a bad edit, a stolen laptop. A shop without them is one bad day from starting over. Do this **before** go-live.

The idea: every night, Banco makes an **encrypted** copy of your database and uploads it to **your own**
Backblaze B2 storage bucket. If disaster strikes, you pull it back with a key you hold. You own the data end to
end — nobody else can read it (it's encrypted) and nobody else can lose it for you.

## Step 1 · Get your own B2 storage (15 min, ~free)

1. Make a **Backblaze B2** account at backblaze.com (the first 10 GB are free — backups are small).
2. Create a **bucket** (e.g. `myshop-banco-backups`). Set it **Private**.
3. Turn on **Object Lock / immutability** if offered — it stops backups being deleted or altered (ransomware
   protection).
4. Create **two application keys**:
   - a **write** key (capability `writeFiles`) — the shop uses this to upload nightly backups;
   - a **read-only** key (`listFiles` + `readFiles`) — for restoring. Give this one to whoever might recover
     the shop (your IT person). Keeping them separate means the shop machine can't delete its own backups.
5. Record all of it in your [password worksheet](04-master-passwords.worksheet.md).

## Step 2 · Point Banco at it (`.env`)

Fill the B2 section of `.env`:
```ini
B2_KEY_ID=<your write keyID>
B2_APP_KEY=<your write key secret>
B2_BUCKET=myshop-banco-backups
BACKUP_GPG_PASSPHRASE=<a strong passphrase you invent — the encryption password>
```
> The **GPG passphrase** is what encrypts your backups. Pick a strong one and store it in **two** safe places.
> Lose it and the backups are unreadable — even to you. It is the single most important secret you have.

> 💡 Easiest way to fill all of this: run `python3 scripts/init-banco.py` (the setup wizard) and answer its
> **B2** section — it writes these into `.env` for you, with the secrets typed hidden. Re-run it any time to
> rotate a key (it keeps your other values as defaults).

## Step 2b · Install the `b2` tool

The backup script talks to Backblaze through the **`b2`** command-line tool — it's the only extra thing you
install for backups (that's the `⚠️ b2: MISSING` note preflight shows until you do this). Install it once:

```bash
sudo apt install -y pipx && pipx install b2 && pipx ensurepath
```
Then open a **new terminal** (so the updated PATH takes effect) and check it:
```bash
b2 version
```
> On Debian 12+/Ubuntu 24+ you **must** use `pipx`, not `pip install b2` — the system Python is locked (PEP-668),
> so a plain `pip install` is refused. On macOS: `brew install b2-tools`.

### Rotating a key later (leaked, expired, or just housekeeping)
If you ever need to swap a key — you pasted it somewhere by accident, it expired, or you're doing routine
rotation — use the guided rotator instead of hand-editing `.env`:
```bash
python3 scripts/rotate-secret.py b2      # or: llm-key, gpg-passphrase, app-secret, admin-password, db-password
```
It shows the old key masked, takes the new one hidden, **tests it against the live service before writing**, and
backs up your `.env` first. If the new key doesn't verify, nothing changes and your old key keeps working. After a
B2 rotation, **delete the old key in Backblaze** — creating a new key does not disable the old one.

## Step 3 · Make your first backup

```bash
./scripts/backup-to-b2.sh
```
This dumps the database, encrypts it, and uploads it. You should see `✅ Backup in B2: banco/banco_…sql.gz.gpg`.
Log into Backblaze and confirm the file is there.

## Step 4 · Make it automatic (nightly)

Schedule the backup so you never have to remember — one command, idempotent:
```bash
./scripts/install-backup-cron.sh        # 03:00 every night (or pass an hour: … 4)
```
It installs the cron job with the right absolute paths, replaces its own line if you run it
again (never duplicates), and leaves your other cron jobs alone. Check it with `crontab -l`.
(Runs on a server you keep on; a laptop that sleeps won't fire it.)

**Arm the dead-man's switch.** A cron job fails silently — you won't notice until you need a
backup that isn't there. So point it at a monitor: create a check at **healthchecks.io** (one
per shop/box), put its **ping URL** in `.env` as `HEALTHCHECK_PING_URL=https://hc-ping.com/<id>`,
and set the check's schedule to daily. `backup-to-b2.sh` pings it on every success — miss a night
and healthchecks emails you. Make sure the check has a notification set, or it's watching in silence.

## Step 4b · Retention — because nothing here ever deletes anything

**Neither script prunes.** Every nightly backup is kept for ever, and that is a deliberate default
(deleting backups automatically is how people lose the one they needed) — but it means the bucket
grows in a straight line and the free tier has an end.

**Measured on the live Artemis shop, 2026-09-17:**

| | |
|---|---|
| in the bucket | **613 files · 4.23 GB**, oldest 2026-07-20, nothing ever removed |
| of which media | 51 archives · **2.80 GB** — the photo volume, ~105 MB *every night* |
| of which database | 562 dumps · 1.43 GB — ~9 MB a night, cheap |
| growth | **~114 MB/night ≈ 3.4 GB/month** |
| free tier | 10 GB |

So the cap lands somewhere around **early November**. And this is not a prediction — **it has already
happened once**: `ERROR: Cannot upload or copy files, storage cap exceeded`, eight times, on
**2026-08-10**. Every run since has succeeded, so it was dealt with; nothing stops it recurring.

### ✅ Decided and applied, 2026-09-17 — the policy in three lines

Angel: *"let's not just back up to eternity and then we have something blow up… let's stick to
industry best practices, for example, and something that's practical."* So:

| | |
|---|---|
| **Dailies** — database + logins, 03:00 | kept **90 days**, then deleted by a **B2 lifecycle rule** on the `banco/` prefix |
| **Media** — the photo volume | **weekly, Sundays 03:15** (was nightly). ~7× less growth, and nothing real is lost: photos added on Tuesday are in Sunday's archive and MinIO still holds the originals |
| **Monthly** — one night, on the 1st at 04:00 | copied to `archive/monthly/`, where **no lifecycle rule matches it**. Kept for ever. ~9 MB a month |

That last row is the one nobody asks for and everybody eventually needs. A 90-day rule answers
*"the disk died last night."* It does not answer *"something was quietly wrong in March."* The
monthly archive is an ordinary **grandfather-father-son** rotation and costs about 100 MB a year.

```bash
./scripts/install-backup-cron.sh      # installs ALL THREE, idempotently
crontab -l                            # and shows you what it did
```

The monthly copy is **server-side** — B2 duplicates the object itself, so nothing is downloaded,
nothing is re-encrypted, and the archived file is byte-identical to the backup that verified itself
that night.

> **Setting the rule deleted nothing on the day.** The oldest file in the bucket was 59 days old, so
> a 90-day rule had nothing to act on — the first expiry is a month away. If you want a different
> window, change it before then and no history is lost.

**If you would rather just pay:** B2 is ~$6/TB/month, so this shop is cents either way. Both are
fine. What is not fine is finding out on the morning an upload stops.

> ⚠️ **The dead-man's switch is what makes this survivable.** `backup-to-b2.sh` pings healthchecks.io
> **only on success**, so a cap-exceeded night sends no ping and you get an email. If you have not
> set `HEALTHCHECK_PING_URL`, a full bucket is completely silent — you find out when you need a
> backup that was never made. Step 4 covers it; do not skip it.

## Step 5 · PRACTICE a restore — the part everyone skips

**A backup you've never restored is not a backup — it's a hope.** Prove it works:

```bash
docker compose stop app
./scripts/restore-from-b2.sh      # pulls the newest backup, decrypts, reloads it
docker compose up -d app
```
Open the till and confirm your data is there. Do this once now, and again any time something big changes.

### Want the full "disaster" rehearsal?
Open [testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html](testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html) — section 6
walks you through restoring a real backup and watching the data come back, with pass/fail boxes.

## The ownership promise, in one line
**Repo + your B2 bucket + your keys + your passphrase = you can rebuild your shop from scratch, on any computer,
without anyone's help.** That's what you can't buy from a big vendor. Guard the passphrase, practice the restore,
and you're genuinely self-insured.
