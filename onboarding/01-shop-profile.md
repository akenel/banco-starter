# 1 · Your shop profile

Banco needs to know who you are — it prints on receipts and shows around the app. Fill this in, then enter it
in the app's **Settings** page (in the POS, open the menu → Settings / Store).

## Fill this in

| Field | Your value | Notes |
|-------|-----------|-------|
| Shop name | ____________________ | Appears on receipts + the app header |
| Store number | ____________________ | e.g. `1` (you can have more than one store later) |
| Address line 1 | ____________________ | Street + number |
| Address line 2 | ____________________ | Postcode + city (or leave blank) |
| Country | ____________________ | Switzerland / Italy / Germany / … |
| VAT number | ____________________ | e.g. `CHE-123.456.789 MWST` (CH), `IT01234567890` (IT), `DE123456789` (DE) |
| Phone | ____________________ | Optional, prints on receipt |
| Currency | ____________________ | See [guide 2](02-settings-currency-vat.md) — must match your `.env` |
| Receipt header | ____________________ | e.g. "Thank you for shopping at <shop>!" |
| Receipt footer | ____________________ | e.g. a tagline, opening hours, or legal line |
| Opening hours | ____________________ | For your own reference / signage |

## Where these live

- **In the app:** most of the above are **store settings** you edit on the Settings page — no code, no restart.
  Change them any time; they take effect immediately and show on the next receipt.
- **In `.env`:** currency and VAT are *also* set in `.env` (guide 2) because the app uses them for tax maths.
  Keep the two in agreement (same currency in `.env` and in Settings).

## Do it

1. Start Banco and log in as a manager/admin.
2. Open the **Settings** page.
3. Enter every row above. Save.
4. Ring a test item and **print/preview a receipt** — check the name, address, VAT number, and footer all read
   correctly. Fix wording now, while it's easy.

> Tip: the VAT number is a legal requirement on receipts in most of Europe. Get it exactly right — copy-paste
> it from your registration document rather than typing it.
