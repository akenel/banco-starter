#!/usr/bin/env python3
"""prove-one-box-one-language.py — CAN A CASHIER READ THE WHOLE BOX?

Three times in two days a box on the till spoke two languages at once:

  2026-09-05  a receipt headed "Sabato" over an Italian body — the DATE was
              formatted for the reader, the day NAME for nobody.
  2026-09-05  the morning guard: "È corretto?" as a title, over an English
              sentence built server-side as an f-string.
  2026-09-06  the Shift Report: "Rapporto turno" as a heading, and directly
              under it "opened and closed by layla".

Every one of them was a TITLE with a key and a BODY without one, and none of
them was findable by comparing the four language files against each other — the
missing string was missing from all four equally, so key-parity said 100%.
LESSON #5: a harness that cannot fail the way production fails is not a harness.

So this asks the question a cashier asks, which is not "are the files in sync"
but "is there English on this screen that will never translate":

  1. every data-i18n / data-i18n-placeholder key in the POS templates exists in
     ALL FOUR languages (a key that resolves in en and not it renders English)
  2. every visible multi-word English text node in the POS templates is covered
     by a key — no bare sentences

(2) is the one that finds the bug. It is also the one that needs an allow-list,
because some text genuinely is not language: "CHF 0.05", "Banco", an emoji.
Anything allow-listed is listed HERE, in the open, with a reason.

  python3 scripts/prove-one-box-one-language.py

Angel, 2026-09-06.
"""
import json, re, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "src/static/pos/pos-i18n.js"
TPL  = ROOT / "src/templates/pos"

# Text that is not a sentence in any language. Each entry needs a reason.
ALLOW = {
    "HelixPOS", "Banco", "La Piazza",        # product names
    "CHF", "TWINT", "Twint", "EAN", "SKU",   # units and identifiers
    "Card / TWINT", "Card / Twint",
}
ALLOW_RE = [
    re.compile(r"^[\W\d\s]+$"),               # punctuation / digits / emoji only
    re.compile(r"^\{\{.*\}\}$"),              # a pure Jinja expression
    re.compile(r"^[A-Z_]{3,}$"),              # SCREAMING constants
]

def langs():
    """Ask NODE for the dictionaries rather than parsing JS by hand.

    The first version of this regex-stripped comments and json.loads()'d the
    result — and died on a `//` that lived INSIDE a string. Parsing a language
    file with a regex is how you get a fifth translation bug while fixing the
    fourth. The file is JavaScript; node already reads it every day in the
    browser; ask the thing that is right by construction.
    """
    shim = (
        "global.window = {};"
        f"require({str(I18N)!r});"
        "process.stdout.write(JSON.stringify(window.POS_STRINGS));"
    )
    out = subprocess.run(["node", "-e", shim], capture_output=True, text=True)
    if out.returncode != 0:
        print("could not read " + str(I18N) + " with node:\n" + out.stderr, file=sys.stderr)
        sys.exit(2)
    return json.loads(out.stdout)

def flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict): out.update(flat(v, key + "."))
        else: out[key] = v
    return out

def strip_comments(t):
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)

def strip_blocks(t):
    for tag in ("script", "style"):
        t = re.sub(rf"<{tag}\b.*?</{tag}>",
                   lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S | re.I)
    return t

VOID = {"area","base","br","col","embed","hr","img","input","link",
        "meta","param","source","track","wbr"}

class BareText(HTMLParser):
    """Find text a cashier can read that NO ancestor has marked translatable.

    The first version asked only about the tag immediately before the text and
    reported 409 bare strings — including three fragments of ONE fully
    translated sentence, because it contained a <b>. A string wrapped in inline
    markup is the NORMAL case for a warning, so the harness was loudest exactly
    where the code was healthiest. Ancestry is the question, not adjacency.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []        # (tag, covered_by_i18n)
        self.hits = []
        self.skip = 0          # inside <script>/<style>

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.skip += 1
        if tag in VOID: return
        a = dict(attrs)
        covered = any(k.startswith("data-i18n") for k in a) or "x-text" in a
        self.stack.append((tag, covered or self.covered))

    def handle_startendtag(self, tag, attrs): pass

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip: self.skip -= 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    @property
    def covered(self):
        return self.stack[-1][1] if self.stack else False

    def handle_data(self, data):
        if self.skip or self.covered: return
        s = data.strip()
        if len(s) < 4 or s in ALLOW: return
        if any(r.match(s) for r in ALLOW_RE): return
        if "{{" in s or "{%" in s: return
        if not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", s): return
        self.hits.append((self.getpos()[0], " ".join(s.split())[:78]))


def main():
    L = langs()
    codes = sorted(L.keys())
    tables = {c: flat(L[c]) for c in codes}
    print(f"languages: {', '.join(codes)}")
    print(f"keys:      " + " · ".join(f"{c} {len(tables[c])}" for c in codes))
    print()

    bad_keys, bare = [], []
    files = sorted(TPL.glob("*.html"))

    for f in files:
        raw = f.read_text(encoding="utf-8")
        text = strip_blocks(strip_comments(raw))

        # (1) every key used resolves in every language
        for m in re.finditer(r'data-i18n(?:-placeholder|-title|-aria)?="([^"]+)"', text):
            key = m.group(1)
            missing = [c for c in codes if key not in tables[c]]
            if missing:
                ln = text.count("\n", 0, m.start()) + 1
                bad_keys.append((f.name, ln, key, missing))

        # (2) every multi-word text node is covered by SOME ancestor
        bt = BareText()
        bt.feed(strip_comments(raw))
        for ln, snippet in bt.hits:
            bare.append((f.name, ln, snippet))

    # (3) a key can be PRESENT in every language and still be English. On
    # 2026-09-06 Angel photographed the whole 18+ Age Gate screen in English on
    # an Italian till: 27 `agerep.*` keys whose Italian and French values are the
    # English string, byte for byte. Key-parity said 100% and every check this
    # repo had was green. This is the one his EYES found and no instrument did.
    english = {}
    en = tables["en"]
    for c in codes:
        if c == "en": continue
        same = [k for k, v in tables[c].items()
                if k in en and str(v).strip() == str(en[k]).strip()
                and re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", str(en[k]))]
        if same: english[c] = same

    # (4) strings hard-coded in <script> blocks never reach t() at all. The date
    # range buttons on Transaction History ("Today · Last 7 days · Last 2 weeks ·
    # This month") are JS literals, which is why check (2) — which skips <script>
    # by design — reported ONE bare string for a screen with five English labels.
    # Conservative on purpose: a label-shaped key with a multi-word value. A floor.
    UIKEY = (r"(label|title|text|message|msg|name|placeholder|hint|caption"
             r"|tooltip|desc|description|reason|status|heading)")
    in_script = []
    for f in files:
        src = strip_comments(f.read_text(encoding="utf-8"))
        for blk in re.finditer(r"<script\b[^>]*>(.*?)</script>", src, re.S | re.I):
            base = src.count("\n", 0, blk.start(1))
            body = blk.group(1)
            for m in re.finditer(UIKEY + r"\s*:\s*(['\"])(.*?)\2", body):
                v = m.group(3)
                if not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", v): continue
                if v.startswith(("http", "/", "#", ".")) or "${" in v: continue
                in_script.append((f.name, base + body.count("\n", 0, m.start()) + 1, v[:70]))

    if bad_keys:
        print(f"❌ {len(bad_keys)} key(s) that do not resolve in every language")
        for fn, ln, key, miss in bad_keys:
            print(f"   {fn}:{ln}  {key}  missing in {','.join(miss)}")
        print()
    else:
        print("✅ every data-i18n key in the POS templates resolves in all four languages")

    if bare:
        print(f"❌ {len(bare)} bare English string(s) — these render English on an Italian till")
        for fn, ln, s in bare:
            print(f"   {fn}:{ln}  {s}")
    else:
        print("✅ no bare multi-word English left in the POS templates")

    if english:
        n = len(set(k for v in english.values() for k in v))
        print(f"❌ {n} key(s) present in every language whose value IS the English string")
        for c in sorted(english):
            ns = {}
            for k in english[c]: ns[k.split(".")[0]] = ns.get(k.split(".")[0], 0) + 1
            top = " · ".join(f"{a} {b}" for a, b in sorted(ns.items(), key=lambda x: -x[1]))
            print(f"   {c}: {len(english[c])}  ({top})")
    else:
        print("✅ no key is quietly still English in another language")

    if in_script:
        print(f"❌ {len(in_script)} English UI string(s) hard-coded in <script> — never reach t()")
        for fn, ln, v in in_script: print(f"   {fn}:{ln}  {v}")
    else:
        print("✅ no English UI strings hard-coded in <script> blocks")

    print()
    print(f"{len(files)} templates read.")
    print("NOT CHECKED HERE: whether a translation that IS different from English is")
    print("any GOOD. Nobody who speaks French or Italian has read these strings.")
    return 1 if (bad_keys or bare or english or in_script) else 0

if __name__ == "__main__":
    sys.exit(main())
