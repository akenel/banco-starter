# 3 · Users & roles

Every person who uses Banco logs in with their own account. What they're allowed to do is decided by their
**role**. Logins live in **Keycloak** (the login system that came with Banco).

## The five roles

| Role | Who | Can do |
|------|-----|--------|
| `pos-cashier` | Front-line staff | Ring sales, take payment, basic returns |
| `pos-manager` | Shift lead / owner | Everything a cashier can, plus reports, the audit log, catalog edits, close-out |
| `pos-auditor` | Bookkeeper / accountant | Read reports + the audit log (who changed what) |
| `pos-developer` | Technical helper | Deeper tools for troubleshooting |
| `pos-admin` | Owner | Full control |

Give people the **least** they need. Most staff are `pos-cashier`. You (the owner) are `pos-admin` or
`pos-manager`.

## Where you manage logins — the Keycloak admin console

1. Open **http://localhost:8080** in your browser.
2. Log in as the admin — username `admin`, password = the `HX_SUPER_PASSWORD` value from your `.env`.
3. Top-left, switch the realm from **master** to **`kc-pos-realm-dev`** (that's Banco's realm).

## Add a real staff member

1. Left menu → **Users** → **Add user**.
2. Fill **Username** (e.g. `maria`), and their email/first/last name. Click **Create**.
3. Open the **Credentials** tab → **Set password**. Type a password, turn **Temporary** OFF (so they aren't
   forced to change it on first login — or leave it ON if you want them to pick their own). Save.
4. Open the **Role mapping** tab → **Assign role** → pick their `pos-…` role (e.g. `pos-cashier`). Assign.
5. Done — they can now log in at `http://localhost:8000/pos` with that username + password.

## Turn OFF the demo users (before go-live)

Banco ships with demo logins so you can try it: **pam, ralph, michael, felix** (password = the username). Before
you open for real, in Keycloak → **Users**, for each demo user either:
- **Disable** them (Details tab → toggle **Enabled** off), or
- **Change their password** to something only you know.

Leaving `pam`/`pam` active on a real shop is like leaving the back door unlocked.

## Also change the master/admin passwords

The starter ships with simple default passwords so it runs out of the box. Before go-live, change:
- The **Keycloak admin** password (`HX_SUPER_PASSWORD` in `.env`, and the matching admin in Keycloak).
- The **database** password (`POSTGRES_PASSWORD`) and **app secret** (`SECRET_KEY`) in `.env`.

Record every new value in your [password worksheet](04-master-passwords.worksheet.md). Then restart:
`docker compose up -d`.

> Rule of thumb: one person = one login. Never share a single account between cashiers — the audit log is only
> useful if it can tell you *who* did something.
