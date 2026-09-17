# Onboarding a new shop — the Banco implementation kit

You've got Banco running (see the root [QUICKSTART.md](../QUICKSTART.md)). This folder takes you the rest of
the way: from a running demo to **your** shop — your name, your currency, your VAT, your staff, your catalog,
and your backups — ready to sell.

Work through it in order. Each guide is short, plain, and tells you exactly what to fill in. Print them, tick
them off, or just keep them open while you set up.

## The path — 0-7 get you open, 8-21 are the shop's real life

*Guides 0-7 are the setup, in order. Everything from 8 on is written from a real
counter and can be read when you need it — but **11, 14 and 21 are not optional if
somebody other than you is going to stand at the till.***

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
| 7 | [07-going-to-production.md](07-going-to-production.md) | **Beyond the laptop:** a real domain, HTTPS/Let's Encrypt, and locking Keycloak down for a public shop. |
| 8 | [08-label-printer.md](08-label-printer.md) | *Optional.* A label printer on the counter: shelf labels, QR + barcode, and the five faults that all look like broken hardware. |
| 9 | [09-shelf-intake.md](09-shelf-intake.md) | *Optional, and the fast way.* Walk the shop with a scanner gun, then build the catalogue at a desk in batches — with the barcode that is really on the packet. |
| 10 | [10-devices-and-roles.md](10-devices-and-roles.md) | *Optional.* Which device does what — till vs back office vs phone — and why **setup is not selling**. Written from a real kit test. |
| 11 | [11-cashier-shift.md](11-cashier-shift.md) | **The cashier's day** — open, sell, the exceptions that actually happen, close. Read this before training anybody. |
| 12 | [12-the-cash-box.md](12-the-cash-box.md) | The drawer: float, pay-in, pay-out, counting down, and what to do when it does not balance. |
| 13 | [13-tablet-x1-debian.md](13-tablet-x1-debian.md) | The counter tablet, end to end: build sheet, the on-screen keypad, the window, the folio, power, the camera. |
| 14 | [14-when-it-goes-down.md](14-when-it-goes-down.md) | **Pin this by the till.** The degradation ladder — what still works at each rung and the one action. |
| 15 | [15-the-doorway-script.md](15-the-doorway-script.md) | Fifteen minutes with a busy owner who is holding stock. |
| 16 | [16-bom-artemis-luzern.md](16-bom-artemis-luzern.md) | The bill of materials for one real shop — what was bought and what it cost. |
| 17 | [17-what-changed-since-july-30.md](17-what-changed-since-july-30.md) | A dated changelog for the owner, in plain words. |
| 18 | [18-training-manual.md](18-training-manual.md) | Training a cashier: roles, the day, what to do when. |
| 19 | [19-what-actually-sells.md](19-what-actually-sells.md) | What a real headshop actually moves — read before deciding what to stock in the catalogue first. |
| 20 | [20-no-barcode-items.md](20-no-barcode-items.md) | Unbranded and handmade stock: when to mint a code, and when never to. |
| 21 | [21-supported-hardware.md](21-supported-hardware.md) | **What Banco runs on, and what it does not.** The reference kit, and what qualifying a new device costs. |
| 🩺 | **`python3 scripts/banco-doctor.py`** | Reads your live setup and tells you what's still unset (✅/⚠️/❌ + a readiness %). Run it often. |
| 🧠 | [ai-coach/](ai-coach/) | Let the AI you already have (Claude/ChatGPT/Ollama) coach you through what the doctor found — free help for rookies. |
| ✔ | [GO-LIVE-CHECKLIST.md](GO-LIVE-CHECKLIST.md) | The cutover tick-list — don't open the doors until every box is green. |
| 📱 | **`<your Banco address>/static/tablet-check.html`** | Open it **on each till / tablet / phone**: does that device's browser meet Banco's floor (Chrome 84+)? Measured, no login, copyable report. Served by the app, because the device you're checking never has the repo on it. |
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
