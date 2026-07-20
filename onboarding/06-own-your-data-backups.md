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

## Step 3 · Make your first backup

```bash
./scripts/backup-to-b2.sh
```
This dumps the database, encrypts it, and uploads it. You should see `✅ Backup in B2: banco/banco_…sql.gz.gpg`.
Log into Backblaze and confirm the file is there.

## Step 4 · Make it automatic (nightly)

Schedule the backup so you never have to remember. On Linux/Mac, add a cron line (`crontab -e`):
```cron
0 3 * * *  cd /path/to/banco-starter && ./scripts/backup-to-b2.sh >> backup.log 2>&1
```
That runs it every night at 03:00. (On a server you keep on; a laptop that sleeps won't run it.)

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
