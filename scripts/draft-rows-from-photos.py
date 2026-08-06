#!/usr/bin/env python3
"""Draft catalogue rows from the shelf-wall photos — no lookup, no AI, no invented facts.

2026-08-06. Angel's verdict after 35 minutes of testing: the AI lookup route does not work for
grinders, and it will not work for bongs either. A grinder has no identity in the world — no
brand, no EAN (0% of 179 bongs and 4% of 203 grinders carry a real one), and anybody can make
one. The "match" a lookup finds on Etsy is a different object that merely looks similar.

So this script does the opposite of a lookup. Every field below was read off the photograph by
eye and written by hand. Nothing was fetched, matched or guessed.

THREE RULES IT WILL NOT BREAK

  1. NO INVENTED BARCODE. `barcode` stays empty. 2026-07-30: minting 2xxx codes for 5,103
     products made the whole catalogue unscannable. These items genuinely have no code, so the
     field stays blank and the first real scan binds it — or Felix never puts one on, which is
     his stated preference and works fine, because the article number already finds them
     (full 5-digit SKU → exactly one product, 300 times out of 300).

  2. NO INVENTED PRICE. `price` is the house "I don't know yet" sentinel. Several photos DO show
     a hand-written sticker (25.- on bongs, 10.- on the wooden grinders, 1.- on the bowls) and
     those are the shop's own prices — but a price read off a picture is exactly what was ripped
     out of the vision path this evening, and it is not going in through the back door here.
     Angel prices them with the product in his hand.

  3. CREATED INACTIVE. 110 rows are already active with no real price (32 at 999.99, 74 at
     99.00, 4 at zero) and every one of them is scannable at the till. A draft nobody has priced
     must not be sellable. Inactive rows still own their barcode and still appear in catalogue
     search (BL-33), so they are findable and editable — just not ringable.

Run with --write to apply; default is a dry run that prints exactly what it would do.
Every row it creates is listed with its SKU so the whole batch can be undone.
"""
import argparse
import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, "/app")

from src.db.database import AsyncSessionLocal  # noqa: E402

# name, category, description, source photo, and the ILIKE probes that must ALL come back empty.
# The probes are the duplicate guard: 203 grinder rows already exist and most of them are
# Tamar's wholesale list, not Felix's shelf. Creating a twin is worse than creating nothing.
DRAFTS = [
    dict(
        name="Bong Glas \"micro\" Bubble Base klein",
        category="Bongs",
        description=(
            "Kleine Glasbong mit Kugelbasis, Marke \"micro\" auf dem Glas aufgedruckt. "
            "Gerader Schliff-Chillum, mehrere Farben im Regal. Preis am Regal ausgezeichnet."
        ),
        photo="bongs-glass/bong-glass-micro-bubble-base-group-w16.jpg",
        absent_if=["%micro%bong%", "%bong%micro%", "%bong%micro"],
    ),
    dict(
        name="Grinder Greengo Metall 2-teilig",
        category="Grinders",
        description=(
            "Zweiteiliger Metallgrinder, Deckel mit rundem Greengo-Sichtfenster "
            "(\"100% natural\", www.greengo.nl). Geriffelter Rand. "
            "Achtung: Greengo im Katalog sind bisher nur Papers, nicht dieser Grinder."
        ),
        photo="grinders-metal/grinder-greengo-metal-2part-branded-w37.jpg",
        absent_if=["%greengo%grinder%", "%grinder%greengo%", "%greengo%mühle%"],
    ),
    dict(
        name="Grinder Kunststoff Kugel schwarz Hanfblatt",
        category="Grinders",
        description=(
            "Kugelförmiger Grinder aus schwarzem Kunststoff, zweiteilig, "
            "mit grünem Hanfblatt-Aufdruck."
        ),
        photo="grinders-plastic/grinder-plastic-ball-black-cannabis-leaf-w42.jpg",
        absent_if=["%grinder%kugel%", "%kugel%grinder%", "%grinder%ball%", "%ball%grinder%"],
    ),
    dict(
        name="Grinder Kunststoff schwarz Spinne 3-teilig",
        category="Grinders",
        description=(
            "Dreiteiliger Grinder aus schwarzem Kunststoff mit weissem Spinnen-Logo "
            "auf dem gewölbten Deckel. Rautenförmige Mahlzähne."
        ),
        photo="grinders-plastic/grinder-plastic-black-spider-disassembled-w38.jpg",
        absent_if=["%grinder%spinne%", "%spinne%grinder%", "%grinder%spider%", "%spider%grinder%"],
    ),
    dict(
        name="Kräutermühle im Karton 1x",
        category="Grinders",
        description=(
            "Grinder in mehrsprachiger Verkaufsverpackung "
            "(de: Kräutermühle / en: Herb Mill / fr: Moulin à Herbes), Inhalt 1 Stück. "
            "DIESER hat als einziger eine Packung — Karton scannen, dann bindet sich die echte EAN."
        ),
        photo="grinders-plastic/grinder-boxed-kraeutermuehle-herb-mill-w43.jpg",
        absent_if=["%kräutermühle%", "%krautermuhle%", "%herb mill%", "%herbmill%"],
    ),
    dict(
        name="Täschli Luzern bestickt",
        category="Storage & Stash",
        description=(
            "Kleines besticktes Täschli mit Reissverschluss, Ornamentmuster in Gold/Rot/Schwarz, "
            "Schriftzug \"LUZERN\" eingewebt. Souvenir-Artikel."
        ),
        photo="textiles/pouch-taeschli-luzern-embroidered-29chf-w21.jpg",
        absent_if=["%täschli%luzern%", "%luzern%täschli%", "%taschli%luzern%"],
    ),
    dict(
        name="Hanf Täschli unbedruckt",
        category="Storage & Stash",
        description=(
            "Täschli aus Hanfgewebe, ohne Aufdruck und ohne Marke, mehrere Farben. "
            "Kein Hersteller und kein Code am Artikel — Name und Preis kommen vom Laden."
        ),
        photo="textiles/pouch-hemp-assorted-unbranded-w20.jpg",
        absent_if=["%hanf%täschli%", "%hanf%tasche%", "%hemp%pouch%", "%hanfbeutel%"],
    ),
]

SENTINEL_PRICE = "999.99"   # the house "no price yet" marker already used by 32 rows
PHOTO_ROOT = "onboarding/testsheets/grinders/2026-08-06-shelf-wall/"


async def main(write: bool) -> int:
    created, skipped = [], []
    async with AsyncSessionLocal() as db:
        # Seed the counter ONCE and increment locally. Querying max() per row looked fine in
        # write mode (each insert commits, so max advances) but printed the SAME sku seven times
        # in the dry run — the preview would not have matched what got written. UNIQUE(sku)
        # is still the real backstop if two people run this at once.
        next_n = (await db.execute(text("""
            SELECT coalesce(max(substring(sku from 'ITEM-([0-9]+)')::int), 0) + 1
            FROM products WHERE sku ~ '^ITEM-[0-9]+$'
        """))).scalar()

        for d in DRAFTS:
            clashes = []
            for pat in d["absent_if"]:
                rows = (await db.execute(text(
                    "SELECT name, category, price FROM products WHERE name ILIKE :p LIMIT 3"
                ), {"p": pat})).fetchall()
                clashes += [(r.name, r.category, r.price) for r in rows]
            if clashes:
                skipped.append((d["name"], clashes))
                continue

            sku = f"ITEM-{next_n:04d}"
            next_n += 1

            desc = d["description"] + f"\n\nFoto: {PHOTO_ROOT}{d['photo']}"
            if write:
                # Every NOT NULL column that has no DB default must be named here. The first
                # attempt supplied only the eight fields this task cared about and died on
                # `is_age_restricted` — the 2026-08-03 lesson, from the other side: a partial
                # row is not a smaller row, it is an invalid one. The three flags are set to
                # what all 651 existing Grinders / Bongs / Storage & Stash rows already carry
                # (f / f / f), so this batch is classified like its neighbours rather than by me.
                await db.execute(text("""
                    INSERT INTO products (id, sku, name, category, description, price,
                                          barcode, is_active, stock_quantity,
                                          is_age_restricted, vending_compatible, sync_override,
                                          created_at, updated_at)
                    VALUES (gen_random_uuid(), :sku, :name, :cat, :desc, :price,
                            NULL, false, 1,
                            false, false, false,
                            now(), now())
                """), {"sku": sku, "name": d["name"], "cat": d["category"],
                       "desc": desc, "price": SENTINEL_PRICE})
                await db.commit()
            created.append((sku, d["name"], d["category"], d["photo"]))

    mode = "CREATED" if write else "WOULD CREATE (dry run)"
    print(f"\n=== {mode}: {len(created)} ===")
    for sku, name, cat, photo in created:
        print(f"  {sku}  {name}")
        print(f"           [{cat}]  price {SENTINEL_PRICE} (no price yet)  barcode EMPTY  INACTIVE")
        print(f"           photo: {photo}")
    print(f"\n=== SKIPPED — a row already exists: {len(skipped)} ===")
    for name, clashes in skipped:
        print(f"  {name}")
        for c in clashes[:3]:
            print(f"      already there: {c[0][:56]}  [{c[1]}]  {c[2]}")
    if created and write:
        print("\n  To undo the whole batch:")
        print("    DELETE FROM products WHERE sku IN ("
              + ", ".join(f"'{s}'" for s, *_ in created) + ");")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply; default is a dry run")
    a = ap.parse_args()
    raise SystemExit(asyncio.run(main(a.write)))
