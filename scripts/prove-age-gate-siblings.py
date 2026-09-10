#!/usr/bin/env python3
"""Proof that the 18+ gate is decided by CLASS, not by a word that happened to be in the title.

    python3 scripts/prove-age-gate-siblings.py                    # the pinned corpus (no DB)
    python3 scripts/prove-age-gate-siblings.py catalogue.csv      # + a whole-catalogue sweep

WHY THIS EXISTS. On 2026-09-10 Angel looked at a shelf and saw three Cyclones cones asking for
ID beside two that did not. The catalogue was then counted, and the split was never about what
the product IS:

    Cyclones Blunt Hemp Blue - Blueberry 2 Stk.    gated   -- the title says "Blunt"
    Cyclones Hemp - Original 2Stk.                 OPEN    -- same shelf, same cone, same age

and, in the other family, a cosmetics keyword was un-gating hashish:

    Tamar "Haschnamal" Black Afghan CREAM Haschisch 5g   OPEN, filed under Creams & Topicals

`_CBD_OPEN` carries `creme|cream` for the CBD cosmetic. "Cream" is also a hashish grade.

WHAT NO EXISTING TEST COULD SEE. Every unit test here feeds the classifier a title and asserts
the answer for THAT title. Nothing compared a product to its SIBLINGS -- and the bug is only
visible as a disagreement between two rows on one shelf. So this proof asserts two properties
that are about the shelf rather than the row:

    A. the known field-found leaks gate, and the measured accessories do NOT
    B. (with a CSV) no product moves 18+ -> open, ever, on any classifier change

PROPERTY B IS THE ONE THAT MATTERS. It is a ratchet: the gate may widen, never narrow, without
a human saying so out loud. Add a row to WIDENS_ARE_EXPECTED only with a reason.

THE MEASUREMENT DISCIPLINE THIS ENCODES. Two candidate signals were thrown away on the day this
was written, and they are pinned below as NOT_A_SIGNAL so nobody re-adds them: `weed` matched 17
open products in the live shop -- an ashtray, a retro sign, three grinders, a joint box, two
carbon filters that only matched because "S-weed-z" contains it -- and `kush` matched a board
game, two rolling trays and a grinder card. Words that ride on ARTWORK are not signals. LESSON #2.
"""
import csv
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.services.catalog_taxonomy import classify  # noqa: E402

# ── A. the shelf, as it actually reads ───────────────────────────────────────────────────
# Every title below is REAL and was copied out of the live shop on 2026-09-10, not invented.

MUST_GATE = [
    # -- the Cyclones shelf: 16 gated / 3 open, split by whether the flavour said "Blunt" ----
    ("Cyclones Hemp - Original 2Stk.",                      "Angel found this one at the counter"),
    ("Blue Cyclone Hemp Cones",                             "its sibling, same cone, brand singular"),
    ("Cycle Cones Mean Green",                              "same cone again, brand spelled 'Cycle'"),
    # -- hashish un-gated by a COSMETICS keyword ---------------------------------------------
    ('Tamar "Haschnamal" Black Afghan Cream Haschisch 5g',  "'Cream' is a hash grade, not a lotion"),
    ("Hash Gang Manali Cream 4.20gr.",                      "filed under Creams & Topicals"),
    ("Greenfire Black Cream Haschisch 9g",                  "filed under Creams & Topicals"),
    ("SWEED Hashtronaut, Bubble Cream Hashish 4g",          "Bubble Cream -- hash"),
    ("Cannabees CBD Hash Creamy 5g",                        "'Creamy' contains 'cream'"),
    # -- flower whose title never prints the letters CBD --------------------------------------
    ("Cannabees - Blueberry Muffin Blüten",                 "hand-captured, no supplier tags"),
    ("Cannabees - Orangeice Blüten 4gr",                    "hand-captured, no supplier tags"),
    ("BudBouncy Indoor Blüten - Northern Light 3g",         "found by the sweep, not by eye"),
    ("BudBouncy Indoor Blüten - V1 3g",                     "found by the sweep, not by eye"),
    ("Kleine Blüten 5g CHEESE Rot - Einzeln",               "found by the sweep, not by eye"),
    ("Kleine Blüten 5g HARLEQUIN Grün - Einzeln",           "found by the sweep, not by eye"),
]

MUST_STAY_OPEN = [
    # -- the OBJECT is not the substance ------------------------------------------------------
    ("Blech-Dose Click-Clack Haschisch",             "a tin with a word on the lid"),
    ("Black Leaf Ersatz- Nadel für Hasch Pfeife",    "a replacement needle"),
    ("Metalldöschen KS Slim mit Haschreibe",         "a tin with a grater"),
    ("Paperhash Regular 100x 14x6cm",                "PAPER BAGS -- and \\bhash\\b must not match it"),
    ("Hausgemachtes Haschisch von Andi Haller",      "a BOOK, CHF 14.90, caught by the byline rule"),
    # -- artwork is not a signal (the two rejected candidates) --------------------------------
    ("Rolling Tray \"O.G. Kush\" 270x160mm",         "a tray"),
    ("Brett-Spiel Mad Kush 2in1",                    "a board game"),
    ("Grinder Card - Booba Kush Bud",                "a grinder card"),
    ("Aschenbecher Ashtray Weed 130mm",              "an ashtray"),
    ("Grinder Alu CNC 2teilig Weed 50mm",            "a grinder"),
    ("Blechschild Weed Chocolate Retro 30 x 20cm",   "a tin sign"),
    ("Aktivkohlefilter Medusa x 187 Sweedz 6mm 50stk GZUZ", "matched only because S-weed-z contains it"),
    # -- empty cones and papers stay open (the first cut of this fix broke exactly this) -------
    ("RAW Organic Hemp Cones - leere Cones mit Filter KS 1", "LEERE = empty. Paper, not a blunt."),
    ("G-Rollz Prerolled OG Kush  2 Stk.",            "empty flavoured cones"),
    # -- the open CBD forms -------------------------------------------------------------------
    ("SWEED MCT Öl 10ml, CBD 10% / THC <0.9% 10ml",  "oil"),
    ("Qualicann Cannalotion 200ml",                  "a lotion -- 'cream' must still work HERE"),
    ("CBD OIL Ointment",                             "an ointment"),
    # -- the negative guards must survive all of the above ------------------------------------
    ("Schnupftabak Ozona Snuffy White Tabakfrei",    "tobacco-FREE"),
    ("ELFBAR - ELFA PRO - Prefilled Pod (2 x 2ml) 0mg Cola", "0mg"),
    ("Tabakersatz Real Leaf Mango Kush 20gr",        "herbal tobacco substitute"),
    ("Black Leaf Recycle Bubbler 205mm schwarz",     "'Recycle' must never match \\bcycle\\b"),
    ("Blaze Recycler für Öl \"Perkolator\" 290mm",   "nor 'Recycler'"),
]

# Words measured against the live shop on 2026-09-10 and REJECTED. If one of these ever becomes
# a gate signal on its own, this proof fails and the count in the failure tells you why.
NOT_A_SIGNAL = {
    "weed": 17,   # open matches in the live shop, every one an accessory or merch
    "kush": 9,    # ditto -- trays, a grinder, a grinder card, a board game, two Tabakersatz
}

WIDENS_ARE_EXPECTED = set()   # titles allowed to move 18+ -> open. Empty, and it should stay empty.


def _p(ok, label, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (("  -- " + detail) if detail else ""))
    return ok


def property_a():
    print("A. the field-found leaks gate, and the measured accessories do not")
    ok = True
    for title, why in MUST_GATE:
        _, cls, age = classify(title)
        ok &= _p(age, "gated: " + title[:56], why if age else "STILL OPEN as " + cls)
    for title, why in MUST_STAY_OPEN:
        _, cls, age = classify(title)
        ok &= _p(not age, "open : " + title[:56], why if not age else "OVER-GATED as " + cls)
    return ok


def property_b(csv_path):
    """The ratchet: against the previous committed classifier, nothing may lose its gate."""
    print("\nB. whole-catalogue A/B against the last commit -- the gate may widen, never narrow")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        try:
            fh.write(subprocess.run(
                ["git", "show", "HEAD:src/services/catalog_taxonomy.py"],
                capture_output=True, text=True, check=True).stdout)
        except subprocess.CalledProcessError:
            return _p(False, "could not read the committed classifier from git")
        old_path = fh.name
    spec = importlib.util.spec_from_file_location("old_taxonomy", old_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)

    csv.field_size_limit(10 ** 7)
    rows = [r for r in csv.reader(open(csv_path, encoding="utf-8")) if len(r) >= 6]
    if not rows:
        return _p(False, "the catalogue export is empty", csv_path)

    widened, narrowed, drifted = [], [], []
    for r in rows:
        name, desc = r[1], (None if r[5] == "-" else r[5])
        _, oc, oa = old.classify(name, None, None, desc)
        _, nc, na = classify(name, None, None, desc)
        if na and not oa:
            widened.append((name, oc, nc))
        elif oa and not na and name not in WIDENS_ARE_EXPECTED:
            narrowed.append((name, oc, nc))
        elif oc != nc:
            drifted.append((name, oc, nc))

    ok = _p(not narrowed, "no product lost its 18+ gate", "%d products swept" % len(rows))
    for n, o, c in narrowed[:20]:
        print("          LOST GATE  %-52s %s -> %s" % (n[:52], o, c))
    ok &= _p(not drifted, "no product changed CLASS while keeping its gate",
             "a cbd_hemp -> tobacco_nicotine move silently drops the thc_report duty")
    for n, o, c in drifted[:20]:
        print("          DRIFTED    %-52s %s -> %s" % (n[:52], o, c))
    print("\n  %d products newly gated by this change:" % len(widened))
    for n, o, c in sorted(widened, key=lambda x: x[0]):
        print("     %-54s %-9s -> %s" % (n[:54], o, c))
    return ok


def property_c():
    """Artwork words must not gate on their own. Pinned so they cannot quietly come back."""
    print("\nC. the rejected signals stay rejected")
    ok = True
    for word, n_open in sorted(NOT_A_SIGNAL.items()):
        title = "Rolling Tray %s Design 270x160mm" % word.upper()
        _, cls, age = classify(title)
        ok &= _p(not age, "'%s' alone does not gate" % word,
                 "%d open products in the live shop carried it" % n_open)
    return ok


def main():
    print(__doc__.split("\n")[0] + "\n")
    ok = property_a()
    ok &= property_c()
    if len(sys.argv) > 1:
        ok &= property_b(sys.argv[1])
    else:
        print("\nB. skipped -- pass a catalogue CSV to sweep the whole shop")
    print("\n" + ("ALL PROPERTIES HOLD" if ok else "*** FAILED ***"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
