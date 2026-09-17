# 2 · Currency & VAT

This is the one that has to be exactly right — it's tax. Banco reads your currency and VAT rates from the
`.env` file. Set them for your country, then restart.

## Where to set them — the `.env` file

Open `.env` (the one you copied from `.env.example`) and set these lines:

```ini
POS_CURRENCY=CHF          # the currency code shown on prices + receipts
POS_LOCALE=de-CH          # number/date format (how 1'234.50 vs 1.234,50 is shown)
POS_VAT_RATE=8.1          # your STANDARD VAT rate, as a percent
POS_VAT_RATE_REDUCED=2.6  # your REDUCED rate (food/takeaway/essentials) — if you use one
POS_VAT_YEAR=2025         # the tax year these rates belong to
```

> ### ⏳ `POS_VAT_YEAR` is a date stamp on your own homework, and it goes stale on purpose
> It changes no maths — it is displayed, so a person can see **when these rates were last checked**
> (`VAT 8.1% (2025)`). Set it to the year you confirmed the rates with your tax authority, and
> re-check it every January. **If it reads a year that is not this one, that is the field doing its
> job**: nobody has verified the rates since then.
>
> *Noted 2026-09-17: the starter and the live Artemis shop both still read `2025`. The Swiss rates
> below are unchanged and correct — the shop bills and prints 8.1% today — so this is a stale
> stamp, not a wrong rate. Confirm and bump it.*

After changing `.env`, restart so it takes effect:

```bash
docker compose up -d
```

## Pick your country

These are the common rates — **confirm against your own tax authority**, rates change and yours may differ.

### 🇨🇭 Switzerland (the Banco default)
```ini
POS_CURRENCY=CHF
POS_LOCALE=de-CH        # or fr-CH / it-CH
POS_VAT_RATE=8.1        # standard (2025)
POS_VAT_RATE_REDUCED=2.6 # reduced: food, non-alcoholic drinks, books, medicine
POS_VAT_YEAR=2025
```
There's also a special lodging rate (3.8%) — only relevant if you rent rooms.

### 🇮🇹 Italy
```ini
POS_CURRENCY=EUR
POS_LOCALE=it-IT
POS_VAT_RATE=22         # standard (IVA)
POS_VAT_RATE_REDUCED=10 # common reduced (Italy also has 5% and 4% bands)
POS_VAT_YEAR=2025
```

### 🇩🇪 Germany
```ini
POS_CURRENCY=EUR
POS_LOCALE=de-DE
POS_VAT_RATE=19         # standard (MwSt)
POS_VAT_RATE_REDUCED=7  # reduced: food, books, etc.
POS_VAT_YEAR=2025
```

## Changing a rate later — what happens to sales already rung

**Nothing. And that is measured, not assumed.**

Every sale line stores **its own rate and its own VAT amount** at the moment it is sold, the
transaction stores its own `tax_amount`, and the reports **sum those stored figures** — they never
recompute tax from today's settings. Checked on the live Artemis shop 2026-09-17: **159 of 159 sale
lines carry a frozen rate**, so not one old receipt would reprint at a new percentage.

So a rate change is forward-only: **old sales keep their rate, new sales get the new one.**

> ### Where to change it — and the warning you will get
> The rate list lives on the **Settings → Tax** page (per shop, in the database). `.env` only supplies
> the *fallback* for a shop that has never opened that editor.
>
> **Since 2026-09-17, moving a rate asks first**, and shows you exactly what is moving:
>
> ```
> ⚠️ YOU ARE CHANGING A TAX RATE
>
>    A:  8.1%  →  8.5%
>
> Every sale already rung keeps the rate it was sold at — receipts and reports
> do not move. From the moment you save, NEW sales use the new rate.
>
> Do this at a clean boundary: close off the day, ideally the tax period, first.
> Not mid-afternoon with customers in the shop.
> ```
>
> Renaming a rate or reordering the list says nothing — that is not a tax event. Only a **number**
> moving asks. Angel's rule, and the reason the warning exists: *"don't do this in the middle of the
> day or willy-nilly changing VAT rates."*

## Standard vs reduced — which rate does a product get?

Each **product** carries a VAT category. Most goods use the **standard** rate. A few use the **reduced** rate
(typically food and non-alcoholic drinks). You set this per product when you load your catalog
([guide 5](05-catalog-loading.md)).

### Café / coffee corner (the dine-in vs takeaway split)
If you serve coffee or food, many countries tax it differently depending on whether it's **consumed on the
premises** (dine-in) or **taken away**. In Switzerland, for example, dine-in is the standard 8.1% and takeaway
is the reduced 2.6%. Banco can handle this split at checkout — set your two rates above and mark café items
accordingly. Confirm your country's rule with your tax advisor.

## Prove it before you rely on it
1. Restart, log in, ring **one standard-rate item** → check the tax line on the receipt matches your standard rate.
2. Ring **one reduced-rate item** (e.g. a bottle of water) → check it uses the reduced rate.
3. Check the **currency symbol/format** looks right for your locale.

> Getting VAT wrong is the kind of mistake that costs money at audit time. Do the three checks above with a real
> receipt, and have someone who knows your local tax rules glance at it once.
