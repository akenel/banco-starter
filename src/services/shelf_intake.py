"""Shelf intake — turn a scanner gun's offline dump into a clean work list.

WHY THIS EXISTS. Angel's inversion, 2026-07-30, after a day capturing stock at the counter:
stop repairing a 5,178-row wholesale import and **let the shelf define the catalogue**. The
Inateck BCST-35 stores 3,000 codes offline (manual §4.6 "Inventurmodus"); you walk the shop
scanning at ~2 seconds a product, then dump the cache into a text box at a desk and do the
thinking afterwards, batched. See `onboarding/testsheets/Scanners/README.md` for the five
inventory barcodes, and `CATALOG-IDENTITY.md` for the thesis.

WHAT THE DUMP ACTUALLY LOOKS LIKE. The gun types its cache out as keystrokes — it is a
keyboard, not a file transfer. So this parser must survive:

  * whichever terminator the gun is set to (CR, LF, CRLF, TAB, or a bare space)
  * a browser that turns a fast keystroke burst into one run-on line
  * the operator's own stray keys, a half-typed code from a low battery, blank lines
  * the SAME product scanned twice — two facings on a shelf is normal, not an error

Nothing here rejects anything. Everything is classified and counted, and the operator decides.
A parser that silently drops a code is worse than useless: the shelf then looks finished when
it is not, which is the exact failure this whole workflow exists to prevent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Every char a gun or a keyboard can inject as a separator. Control chars are terminators,
# spaces happen when the gun is set to "space suffix", and a real barcode contains neither.
_SPLIT = re.compile(r"[\s\x00-\x20\x7f]+")

# What a scannable code can be made of. Deliberately WIDER than EAN-13: shops carry Code128
# SKUs (TAM-21796), ITF-14 cases, and the shop's own printed labels. Anything outside this
# is junk the operator typed by accident.
_CODE_OK = re.compile(r"^[A-Za-z0-9._/+-]{4,40}$")

# GS1 restricted-distribution / in-store ranges. A 13-digit code starting with 2 was assigned
# by *somebody's* back office, not by a manufacturer — ours, most likely (the 07-07 import
# minted 5,105 of them). It is a real code on our shelf but it exists on no packet anywhere,
# which is precisely the thing this workflow is here to replace.
_INTERNAL_13 = re.compile(r"^2\d{12}$")


def gtin_check_digit_ok(code: str) -> bool | None:
    """True/False for a GTIN-8/12/13/14, None when the code isn't a GTIN at all.

    None matters as much as False. A Code128 SKU has no check digit and asking about one is a
    category error — the caller must not paint `TAM-21796` as suspect just because it fails a
    test that never applied to it.
    """
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return None
    digits = [int(c) for c in code]
    body, check = digits[:-1], digits[-1]
    # Weight 3,1,3,1… reading RIGHT to LEFT from the digit before the check digit.
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


@dataclass
class ScannedCode:
    code: str
    count: int = 1               # how many times it appeared in the dump (two facings is normal)
    is_internal: bool = False    # GS1 2-prefix: assigned by a back office, on no packet
    checksum_ok: bool | None = None


@dataclass
class ParsedDump:
    codes: list[ScannedCode] = field(default_factory=list)
    total_tokens: int = 0        # everything the gun typed, including repeats
    junk: list[str] = field(default_factory=list)

    @property
    def unique(self) -> int:
        return len(self.codes)

    @property
    def repeats(self) -> int:
        return sum(c.count - 1 for c in self.codes)


def parse_dump(raw: str) -> ParsedDump:
    """Split a keystroke dump into unique codes, in the order they were first scanned.

    Order is preserved on purpose: it is the order you walked the shop, so the work list reads
    shelf by shelf instead of jumping around, and an operator can recognise where they were.
    """
    out = ParsedDump()
    seen: dict[str, ScannedCode] = {}
    for tok in _SPLIT.split(raw or ""):
        if not tok:
            continue
        out.total_tokens += 1
        if not _CODE_OK.match(tok):
            out.junk.append(tok)
            continue
        if tok in seen:
            seen[tok].count += 1
            continue
        entry = ScannedCode(
            code=tok,
            is_internal=bool(_INTERNAL_13.match(tok)),
            checksum_ok=gtin_check_digit_ok(tok),
        )
        seen[tok] = entry
        out.codes.append(entry)
    return out


def dump_warnings(parsed: ParsedDump, expected: int | None = None) -> list[str]:
    """Human-readable warnings about the dump ITSELF, before any catalogue work starts.

    The count check is the important one and it is why the workflow says to scan *Anzahl der
    gescannten Barcodes* first: a half-uploaded cache looks exactly like a finished shelf, and
    you only find out weeks later when a product nobody scanned turns out to be missing.
    """
    w: list[str] = []
    if expected is not None and expected != parsed.total_tokens:
        w.append(
            f"The gun reported {expected} stored codes but {parsed.total_tokens} arrived — "
            f"the upload is incomplete. Do NOT clear the cache; click into the box and "
            f"scan 'Daten hochladen' again."
        )
    if parsed.junk:
        shown = ", ".join(repr(j) for j in parsed.junk[:5])
        w.append(f"{len(parsed.junk)} token(s) were not code-shaped and were ignored: {shown}")
    bad = [c.code for c in parsed.codes if c.checksum_ok is False]
    if bad:
        w.append(
            f"{len(bad)} code(s) have a bad GTIN check digit — usually a misread, "
            f"occasionally a genuinely odd code: {', '.join(bad[:5])}"
        )
    return w
