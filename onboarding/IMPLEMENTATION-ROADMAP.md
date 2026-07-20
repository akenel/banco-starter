# Implementation roadmap — from box to open till

This is the whole journey, in phases, with a realistic schedule. You don't have to do it all at once — but do
it **in order**, because each phase builds on the last. Times assume one motivated person working part-time; a
focused weekend gets you a basic working shop, a careful real cutover is 2–4 weeks.

```
  PHASE 0        PHASE 1        PHASE 2        PHASE 3        PHASE 4        PHASE 5
  Discovery  →   Install    →   Configure  →   Load       →   Train      →   Go-Live   →   Hypercare
  (decide)       (stand up)     (make it       catalog        staff          (cutover)     (first 2 wks)
                                 yours)
```

## Schedule at a glance

| Phase | What | Effort | Who |
|-------|------|--------|-----|
| 0 · Discovery | Decide currency, VAT, roles, product list, hardware | ½–1 day | Owner |
| 0.5 · Prerequisites | Check the machine + install tools (git, docker…) — [guide 0](00-prerequisites.md) | 1 hr – ½ day | Owner / IT |
| 1 · Install | `docker compose up` — a running demo | 1–2 hrs | Owner / IT |
| 2 · Configure | Shop profile, currency, VAT, users + passwords | ½–1 day | Owner |
| 3 · Load catalog | Get real products + prices in | 1 day – 1 wk | Owner |
| 4 · Train | Walk staff through selling, returns, close-out | ½ day | Owner + staff |
| 5 · Go-Live | Backups on, final checks, open the doors | ½ day | Owner |
| 6 · Hypercare | Watch closely, fix small things, daily backup check | ~2 wks | Owner |

---

## Phase 0 · Discovery — decide before you build (½–1 day)

Answer these on paper first; the rest goes faster.

- **Country & currency?** Switzerland (CHF), Italy/Germany (EUR)? → drives VAT + locale ([guide 2](02-settings-currency-vat.md)).
- **VAT rates?** Standard + reduced for your country. Do you serve food/coffee (dine-in vs takeaway split)?
- **Who works the till?** List the people and what each is allowed to do → roles ([guide 3](03-users-and-roles.md)).
- **What do you sell?** Rough product count, and where the list lives today (a spreadsheet? a supplier? nothing yet?) → ([guide 5](05-catalog-loading.md)).
- **Age-restricted items?** Tobacco, alcohol, 18+ — Banco can flag these at checkout.
- **Hardware?** Barcode scanner, receipt printer, card/TWINT terminal — nice to have, not required to start.

## Phase 0.5 · Prerequisites — the tools (1 hr – ½ day)

**The step everyone forgets.** A fresh machine usually doesn't have Docker, git, or curl. Do
[guide 0](00-prerequisites.md) first: check the machine can handle it, then install the tools. A real field test
on a clean Debian laptop found `docker`, `git`, `curl` all missing (and had to install them) — that's normal,
and it's why "just run docker compose up" isn't step one on a new box.

## Phase 1 · Install — get it running (1–2 hrs, once the tools are in)

Follow the root [QUICKSTART.md](../QUICKSTART.md): `python3 scripts/init-banco.py` (the setup wizard — writes
your `.env`; or `cp .env.example .env` by hand) → `docker compose up --build -d` → `./scripts/standup.sh`.
Standup ends with the smoke test (`scripts/postboot-check.py`) printing a **✅ safe-to-test → go here** verdict.
Log in at `http://localhost:8000/pos` as `pam`/`pam`. **You now have a working demo shop.** Prove it end-to-end
with the [testsheet](testsheets/OWN-YOUR-BANCO-E2E-TESTSHEET.html).

## Phase 2 · Configure — make it yours (½–1 day)

1. [Shop profile](01-shop-profile.md) — name, address, VAT number, receipt footer.
2. [Currency & VAT](02-settings-currency-vat.md) — set the `.env` values for your country.
3. [Users & roles](03-users-and-roles.md) — create your real staff logins, set real passwords.
4. [Master-passwords worksheet](04-master-passwords.worksheet.md) — record every password/key in your password manager.
5. Restart (`docker compose up -d`) so the new settings take effect, and log in as **yourself**, not the demo user.

## Phase 3 · Load catalog — your products (1 day – 1 week)

[Guide 5](05-catalog-loading.md). Start small — your top 50 sellers get you selling. Add the long tail over the
first weeks. Set prices, VAT category, and age flags as you go.

## Phase 4 · Train — the people (½ day)

Sit each cashier at the till. Have them: ring a sale, take cash, give change, do a return, and run the daily
close-out. Show the manager the reports + the 🕵️ audit log. Ten real practice sales beats an hour of talking.

## Phase 5 · Go-Live — open the doors (½ day)

**Do not skip the [GO-LIVE-CHECKLIST.md](GO-LIVE-CHECKLIST.md).** The big ones: backups are ON and a restore
has been practiced ([guide 6](06-own-your-data-backups.md)); the demo data is cleared; real staff can log in;
currency + VAT are correct on a real receipt; you've done a full test sale with the real catalog.

## Phase 6 · Hypercare — the first two weeks (~2 wks)

The shop is open — now watch it closely. Each day: glance at the sales report, confirm last night's backup
ran, and jot anything odd. Small fixes are normal in week one. After two clean weeks, you're just… running a
shop. That's success.

---

### The one rule for a calm go-live
**Backups first, catalog second, everything else third.** A shop with backups and a thin catalog can open and
grow. A shop with a perfect catalog and no backups is one bad day from disaster. Do [guide 6](06-own-your-data-backups.md)
early, not last.
