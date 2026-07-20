# Onboarding a new shop — the Banco implementation kit

You've got Banco running (see the root [QUICKSTART.md](../QUICKSTART.md)). This folder takes you the rest of
the way: from a running demo to **your** shop — your name, your currency, your VAT, your staff, your catalog,
and your backups — ready to sell.

Work through it in order. Each guide is short, plain, and tells you exactly what to fill in. Print them, tick
them off, or just keep them open while you set up.

## The path (6 steps + a plan)

| # | File | What you do |
|---|------|-------------|
| — | [IMPLEMENTATION-ROADMAP.md](IMPLEMENTATION-ROADMAP.md) | **Read first.** The whole plan + a realistic schedule (about 2–4 weeks part-time). |
| 0 | [00-prerequisites.md](00-prerequisites.md) | **Do this before cloning.** Check the machine + install the tools (git, docker…). |
| 1 | [01-shop-profile.md](01-shop-profile.md) | Write down who you are: shop name, address, VAT number, hours. |
| 2 | [02-settings-currency-vat.md](02-settings-currency-vat.md) | Set your currency + VAT rates (Switzerland / Italy / Germany examples). |
| 3 | [03-users-and-roles.md](03-users-and-roles.md) | Decide who logs in, give them a role, set real passwords. |
| 4 | [04-master-passwords.worksheet.md](04-master-passwords.worksheet.md) | A **secure worksheet** for all your passwords + keys (store it in a password manager, never here). |
| 5 | [05-catalog-loading.md](05-catalog-loading.md) | Get your products in — by hand, by spreadsheet, by supplier feed, or by photo. |
| 6 | [06-own-your-data-backups.md](06-own-your-data-backups.md) | Set up **your own** encrypted backups (your Backblaze B2), and practice a restore. |
| 🩺 | **`python3 scripts/banco-doctor.py`** | Reads your live setup and tells you what's still unset (✅/⚠️/❌ + a readiness %). Run it often. |
| 🧠 | [ai-coach/](ai-coach/) | Let the AI you already have (Claude/ChatGPT/Ollama) coach you through what the doctor found — free help for rookies. |
| ✔ | [GO-LIVE-CHECKLIST.md](GO-LIVE-CHECKLIST.md) | The cutover tick-list — don't open the doors until every box is green. |
| 🧪 | [testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html](testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html) | Open in a browser: a click-through test that proves the whole thing works (records pass/fail, exports a report). |

## How to think about it

- **You own everything.** The code (this repo), the data (your database + your B2 backups), and the runbooks
  (these files). Nothing here needs the person who built it. That's the point.
- **Nothing you do here can hurt a live shop** — it all runs on your own machine in Docker until you decide to
  deploy it for real.
- **Two kinds of "settings":** things in the `.env` file (currency, VAT, passwords the app uses) and things you
  click in the app / Keycloak (staff logins, products). Each guide says which is which.
- **Go at your own pace.** A determined owner can do a basic setup in a weekend. A careful cutover with real
  catalog + staff training is 2–4 weeks part-time. The roadmap lays it out.

> Stuck on a word or a step? That's a bug in *these docs*, not in you. Note it on the testsheet (⚠ ISSUE) and
> it gets fixed. The goal is that anyone can do this.
