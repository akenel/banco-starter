# 5 · Loading your catalog

Your catalog is your products: name, price, VAT category, barcode, and whether it's age-restricted. You don't
need everything on day one — **your top 50 sellers get you open**, and you fill in the long tail over the first
weeks. Banco gives you a few ways to add products; use whichever fits.

## First: clear the demo catalog

The starter seeds a demo shop ("Artemis") so you can try it. For your real shop, start empty: set
`HX_SEED_DEMO=false` in `.env` and do a clean start (`docker compose down -v` then `up -d`). Now the catalog is
yours to fill — staff logins and settings still work.

## Way 1 · Add a product by hand (simplest)
In the POS, open **Products → Add**. Enter:
- **Name** and **price**
- **VAT category** — standard or reduced ([guide 2](02-settings-currency-vat.md))
- **Barcode** (scan it or type it) — so it rings up by scan later
- **Age-restricted?** — flag tobacco / alcohol / 18+ items so the till prompts at checkout
- **Category** (e.g. Papers, Grinders, Drinks) — for tidy menus and reports

Good for a small shop or filling gaps. Do your top sellers first.

## Way 2 · Snap a photo (fastest for new items)
If you set up the optional AI brain (`BH_OLLAMA_KEY` in `.env`), Banco can **read a photo of a product** and
pre-fill the name, a description, and a suggested category — you just check it and set the price. Great for
adding new stock quickly without typing. No AI key? This just falls back to manual entry.

## Way 3 · Capture on the first sale (barcode-first)
You don't have to pre-load everything. When a cashier scans a barcode Banco doesn't know yet, it can **create
the product on the spot** (name + price) and remember it — so the catalog builds itself as you sell. The first
sale of each item is where it gets captured. Good for shops with a huge, messy product range.

## Way 4 · Bulk import (bigger catalogs)
If your products already live in a spreadsheet or a supplier's price list, a bulk import saves a lot of typing.
This is the "advanced" path — line up your columns (name, price, barcode, VAT, category) and import in one go.
Ask for the import guide when you're ready, or start with Ways 1–3 and grow.

## Whichever way — get these right per product
- **Price** (obviously).
- **VAT category** — standard vs reduced. Wrong VAT = wrong tax collected.
- **Age flag** — tobacco / alcohol / 18+ must be flagged so the till can prompt.
- **Barcode** — so scanning works at the till.

## Prove it
1. Add (or capture) a handful of real products.
2. On the till, **scan** one → the right product + price comes up.
3. Ring a sale → the **VAT** on the receipt is correct for that product.
4. Try an **age-restricted** item → the till prompts as expected.

> Don't chase a "perfect" catalog before opening. A clean top-50 with correct prices and VAT beats a giant list
> full of guesses. You can enrich and tidy every day the shop is open — that's normal.
