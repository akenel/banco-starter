#!/usr/bin/env python3
"""Every input a person can type into, keyed on THE WORDS ON THE SCREEN.

WHY THIS EXISTS. On 2026-09-01 the on-screen keypad was wired to the wrong two
fields and an hour went on four wrong theories. The cause was an indexing
mismatch: I searched the CODE for a create form and found `lazyName`; Angel uses
the SCREEN and had been saying "Item name" since his first message — which is a
different form, `otfName`, forty lines away. `otfName` and `lazyName` are
indistinguishable to a grep. "Item name" and "Product name" are not.

So this report leads with the label a human reads, and only then the variable.
When Angel names a field, finding it becomes a lookup instead of a judgement.

Read-only. Prints a table and writes docs/keypad-inventory.md.

    python3 scripts/keypad-inventory.py
    python3 scripts/keypad-inventory.py --cashier   # only the till path
"""
import re, sys, pathlib, html as _html

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL  = ROOT / "src" / "templates" / "pos"

# The screens a cashier actually reaches — the bottom nav, the POS home, and the
# places those lead. Everything else is a manager/admin screen and waits.
CASHIER = {
    "scan.html", "checkout.html", "customer_lookup.html", "shelf_intake.html",
    "kiosk.html", "login.html", "my_day.html", "closeout.html", "shift.html",
    "held_orders.html", "search.html", "dashboard.html", "join_card.html",
}

# Input TYPES that are never a keypad's business — the browser or the OS owns them.
NEVER_TYPE = {"hidden", "checkbox", "radio", "file", "date", "time", "datetime-local",
              "month", "week", "color", "range", "submit", "button", "image", "reset"}

# ── DO NOT TOUCH ──────────────────────────────────────────────────────────────
# The scanner gun types into these AS A HARDWARE KEYBOARD. Wiring a pad here does
# not break the gun, but it throws a keyboard over half the screen on every scan,
# and shelf-intake deliberately accepts BOTH a scan and typing (Angel, 2026-09-01).
# A do-not-touch list has to be written before a to-do list.
SCANNER = re.compile(r"barcode|scan|sku|\bean\b|\bcode\b|gtin|upc", re.I)

# Fields that want DIGITS, split two ways because they are not the same keypad:
# a quantity has no decimal point and money does. First draft of this matched
# "gram", which classified INSTAGRAM and TELEGRAM as money — the exact shape of
# mistake this report exists to catch, caught by its own first run.
WHOLE = re.compile(r"qty|quantit|\bcount\b|footfall|\bstock\b|min_qty|"
                   r"pack_qty|\bunits?\b|people|persons", re.I)
MONEY = re.compile(r"price|\bcost\b|amount|\btotal\b|discount|percent|\bpct\b|"
                   r"\bcash\b|float|tendered|change|\bchf\b|\bsum\b|paid", re.I)

TAG   = re.compile(r"<(input|textarea)\b[^>]*>", re.I | re.S)
ATTR  = re.compile(r'([a-zA-Z_@:.\-\[\]]+)\s*=\s*"([^"]*)"')
LABEL = re.compile(r"<label\b[^>]*>(.*?)</label>", re.I | re.S)
STRIP = re.compile(r"<[^>]+>")


def text_of(chunk: str) -> str:
    return " ".join(_html.unescape(STRIP.sub(" ", chunk)).split())


def label_for(lines, idx):
    """The words a person reads. Nearest <label> above, else the placeholder."""
    window = "\n".join(lines[max(0, idx - 8): idx + 1])
    found = LABEL.findall(window)
    if found:
        t = text_of(found[-1]).replace("*", "").strip()
        if t:
            return t[:44]
    return ""


def classify(attrs, label, model):
    t = (attrs.get("type") or "text").lower()
    hay = " ".join([label, model, attrs.get("placeholder", ""),
                    attrs.get("data-i18n-placeholder", ""), attrs.get("name", "")])

    if t in NEVER_TYPE:
        return None, f"skip — type={t}"
    if SCANNER.search(hay):
        return "DO NOT TOUCH", "scanner gun types here"
    if t == "password":
        return "text", "password — decide deliberately"
    # The x-model is the MORE SPECIFIC signal and must beat the label when they
    # disagree — "Quantity price breaks" holds a unit_price, and "Cost / unit
    # (CHF)" is money despite the word "unit". Read the variable first, the
    # words second; both, before the bare type.
    for source in (model, hay):
        if MONEY.search(source):
            return "decimal", ""
        if WHOLE.search(source):
            return "numeric", "whole numbers — no decimal point"

    im = (attrs.get("inputmode") or "").lower()
    if im == "numeric":
        return "numeric", ""
    if im == "decimal":
        return "decimal", ""
    if t == "number":
        # Digits are asked for and no word says why. This is where a wrong guess
        # would be invisible, so it gets a human, not a heuristic.
        return "decimal", "type=number, nothing says money — CHECK"
    return "text", ""


def main():
    only_cashier = "--cashier" in sys.argv
    rows, files = [], sorted(TPL.glob("*.html"))

    for f in files:
        if only_cashier and f.name not in CASHIER:
            continue
        src = f.read_text(encoding="utf-8")
        lines = src.splitlines()
        for m in TAG.finditer(src):
            line_no = src[:m.start()].count("\n")
            attrs = dict(ATTR.findall(m.group(0)))
            model = attrs.get("x-model") or attrs.get("x-model.number") or ""
            for k in list(attrs):
                if k.startswith("x-model"):
                    model = attrs[k]
            label = label_for(lines, line_no)
            want, note = classify(attrs, label, model)
            if want is None:
                continue
            rows.append({
                "file": f.name, "line": line_no + 1, "label": label or "—",
                "model": model or "—", "type": (attrs.get("type") or "text"),
                "has": attrs.get("data-keypad", ""), "want": want, "note": note,
            })

    todo = [r for r in rows if r["want"] != "DO NOT TOUCH" and not r["has"]]
    done = [r for r in rows if r["has"]]
    skip = [r for r in rows if r["want"] == "DO NOT TOUCH"]
    wrong = [r for r in done if r["has"] != r["want"]]

    scope = "cashier path" if only_cashier else "all POS screens"
    print(f"\n  {len(rows)} typable inputs across {len({r['file'] for r in rows})} "
          f"templates  ({scope})")
    print(f"  ✅ wired {len(done)}   ▶️ to wire {len(todo)}   "
          f"⛔ do not touch {len(skip)}   ⚠️ wrong kind {len(wrong)}\n")

    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], []).append(r)

    out = ["# Keypad inventory", "",
           f"*Generated by `scripts/keypad-inventory.py` — {scope}. "
           "Keyed on the label a person reads, because that is the index Angel uses "
           "and searching the code instead is what wired the wrong field on 2026-09-01.*",
           "", f"**{len(rows)} typable inputs** · ✅ wired {len(done)} · "
           f"▶️ to wire {len(todo)} · ⛔ do not touch {len(skip)} · "
           f"⚠️ wrong kind {len(wrong)}", ""]

    for fname in sorted(by_file, key=lambda n: (n not in CASHIER, n)):
        rs = by_file[fname]
        tag = "" if fname in CASHIER else "  *(not on the cashier path)*"
        out += [f"## `{fname}`{tag}", "",
                "| line | what it says on screen | x-model | type | now | should be |",
                "|---|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: r["line"]):
            state = ("✅ " + r["has"]) if r["has"] else ("⛔" if r["want"] == "DO NOT TOUCH" else "—")
            flag = " ⚠️" if (r["has"] and r["has"] != r["want"]) else ""
            note = f" · {r['note']}" if r["note"] else ""
            out.append(f"| {r['line']} | **{r['label']}** | `{r['model']}` | "
                       f"`{r['type']}` | {state} | {r['want']}{flag}{note} |")
        out.append("")

        print(f"  ── {fname}")
        for r in sorted(rs, key=lambda r: r["line"]):
            state = ("✅" + r["has"]) if r["has"] else ("⛔" if r["want"] == "DO NOT TOUCH" else "  ")
            print(f"     {r['line']:>5}  {state:<10} {r['label'][:34]:<34} "
                  f"{r['model'][:20]:<20} -> {r['want']}")
        print()

    dest = ROOT / "docs" / "keypad-inventory.md"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"  written: {dest.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
