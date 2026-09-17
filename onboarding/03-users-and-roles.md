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

---

## ❗ "Why can't we just have one login for everybody?"

**Because it is the one decision you cannot undo later, and it quietly cancels most of what a
till is for.** This question comes up in every shop, it is a completely reasonable thing to
ask, and it deserves a real answer rather than "security says no".

**First, the objection is about the wrong thing.** One login per person is not more complicated to
*use* — it is the same screen and the same two boxes. The only extra work is creating the account,
which is about five minutes in Keycloak, once, per person. That is the whole cost.

Here is what it buys, in the order it will actually matter to you:

| # | With one shared login | With a login each |
|---|---|---|
| 1 | The drawer is CHF 40 short and **nobody is short** — "the shop" is. | The shift belongs to a person, who usually remembers what happened. |
| 2 | A cashier set a price at the till (see [`11-cashier-shift.md`](11-cashier-shift.md) C3b) and you cannot ask her what she was looking at. | The row carries **who typed it**, so you ask one person one question. |
| 3 | **The 18+ record names the shop, not a person.** | It names the person who looked at the ID. |
| 4 | "Refunds are manager-only" means nothing — everyone holds the manager login. | The control is real. |
| 5 | You can never dial permissions **down** later. | Start everyone as manager, narrow it when the catalogue settles. |
| 6 | Someone leaves and the password must change **for everybody** — so in practice it never changes. | Disable one account. Thirty seconds. |
| 7 | The audit log still records every action, and every row says the same name. | It answers *who*, which is the only question you ask it. |
| 8 | Any dispute ends in "wasn't me", and everyone is telling the truth. | The question is settled without anyone being accused. |
| 9 | You cannot see who is struggling and needs ten minutes of training. | You can, and quietly. |
| 10 | Two people on one account can overwrite each other's shift mid-close. | One shift, one owner. |

**Number 3 is the one that is not about convenience.** In a shop that sells age-restricted stock,
the record of who checked an ID is a compliance record, and Banco keeps it append-only on purpose.
"Someone signed in on the shop account" is not an answer to give a Treuhänder or an inspector.

**Where the objection is RIGHT.** Sharing is genuinely faster when two people swap mid-sale. The
answer to that is the shift handover, not a shared password — and if logging in is slow enough to
be annoying, say so, because that is a fixable problem and a shared account is not a fix for it.

> **The rule: one person = one login, and nobody lends theirs.** If you lend your login, every sale,
> every refund and every ID check made on it is *yours* — that is not a threat, it is simply how
> the record reads afterwards.
