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
