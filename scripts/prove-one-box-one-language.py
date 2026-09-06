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
    "worldline", "Visa", "Twint", "Instagram", "Telegram", "Facebook",  # brand names
    "BL-000",                                 # a placeholder ticket ref, replaced at runtime
    "AXIUM DX8000",                           # a card terminal's model name
    # Example SEARCH TERMS for the supplier catalogue. The feed is German, so these
    # are the words that actually find things — identical in all four languages on
    # purpose, exactly as the hint above the box says ("try the trade word").
    "rasta · kawumm · black leaf · grinder…",
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

def strip_js_comments(t):
    """Blank out // line comments and /* */ blocks, leaving line numbers intact.

    Added because check (8) matched the sentence in ITS OWN documentation that
    quotes the bug it looks for. `://` is spared so URLs survive.
    """
    t = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
    return re.sub(r"(?m)^(\s*)//[^\n]*", r"\1", t)


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
        self.stack = []        # (tag, covered_by_i18n, exempt)
        self.hits = []
        self.xtext = []
        self.skip = 0          # inside <script>/<style>

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.skip += 1
        a0 = dict(attrs)
        # English written INSIDE an x-text expression. Collected HERE rather than
        # by a separate regex pass, because the exemption that covers it is on an
        # ANCESTOR — the sandbox overlay wraps the whole terminal, and a scan that
        # only reads the element's own tag cannot see that. Same mistake as the
        # 409, one check along.
        expr = a0.get("x-text") or a0.get("x-html")
        if expr and not (self.covered_exempt or "data-i18n-exempt" in a0):
            for lit in re.finditer(r"'([^']{3,})'", expr):
                v = lit.group(1)
                if re.search(r"[)+]\s*$|^\s*[+(]", v) or any(c in v for c in "+()"): continue
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.\-]*", v): continue
                if v.startswith(("http", "/", "#", ".")) or v in ALLOW: continue
                if not re.search(r"[A-Za-z]{2,}", v): continue
                self.xtext.append((self.getpos()[0], v[:60]))
        if tag in VOID: return
        a = a0
        # data-i18n-exempt="why" marks a subtree that must NOT be translated, and
        # says why in the attribute itself. Three real cases on 2026-09-06: the
        # worldline_sim SANDBOX (never renders in a shop), the Italian legal
        # disclaimer on the receipt (translating it would break it), and the
        # tenant's own store name. A skip-list hidden in this file would have
        # hidden the reason too, and the reason is the whole point — see LESSON
        # #10, which is how both of those were misdiagnosed in the first place.
        covered = (any(k.startswith("data-i18n") for k in a) or "x-text" in a
                   or "data-i18n-exempt" in a)
        self.stack.append((tag, covered or self.covered,
                           ("data-i18n-exempt" in a) or self.covered_exempt))

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

    @property
    def covered_exempt(self):
        return self.stack[-1][2] if self.stack else False

    def handle_data(self, data):
        if self.skip or self.covered: return
        s = data.strip()
        if len(s) < 4 or s in ALLOW: return
        if any(r.match(s) for r in ALLOW_RE): return
        if "{{" in s or "{%" in s: return
        # A SENTENCE IS NOT THE ONLY THING A CASHIER READS. Until 2026-09-06 this
        # required two Latin words, so `Cancel`, `Saving…`, `buy`, `Price (CHF)`
        # and `Barcode` were invisible — 118 of them, 15 on the scan screen alone,
        # including the Cancel on the manager price panel. The third time this
        # instrument has undercounted the thing it was written to find. A label is
        # a string; length is not the test.
        if not re.search(r"[A-Za-z]{2,}", s): return
        if not re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", s):
            # single label: must look like a word, not a code or a fragment
            # strip leading/trailing symbols and emoji first — "🔔 Notifications"
            # and "Diagnostics ↗" are labels, and testing the raw string rejected
            # both because it does not start with a letter.
            core = re.sub(r"^[^A-Za-z]+|[^A-Za-z'’!?.)…%]+$", "", s)
            if not re.fullmatch(r"[A-Za-z][A-Za-z'’\-…!?:%()&. ]{1,28}", core): return
        self.hits.append((self.getpos()[0], " ".join(s.split())[:78]))


def main():
    L = langs()
    codes = sorted(L.keys())
    tables = {c: flat(L[c]) for c in codes}
    print(f"languages: {', '.join(codes)}")
    print(f"keys:      " + " · ".join(f"{c} {len(tables[c])}" for c in codes))
    print()

    bad_keys, bare, in_xtext = [], [], []
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
        for ln, v in bt.xtext:
            in_xtext.append((f.name, ln, v))

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
                and str(en[k]).strip() not in ALLOW
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
                if v in ALLOW: continue
                in_script.append((f.name, base + body.count("\n", 0, m.start()) + 1, v[:70]))

    # (5) collected by BareText above, which knows about ancestors.

    # (6) A placeholder is text the cashier reads, and it lives in an ATTRIBUTE —
    # so checks (1) and (2) both miss it: (1) only validates placeholders that
    # already HAVE a key, and (2) only reads text nodes. The feedback panel's
    # "Short title (what's up?)" and "Details — what happened…" sat in English in
    # all four languages the whole time. Same for title= and aria-label=.
    bare_attr = []
    for f in files:
        src = strip_comments(strip_blocks(f.read_text(encoding="utf-8")))
        for m in re.finditer(r"<[^>]+>", src):
            tag = m.group(0)
            for attr, i18n in (("placeholder", "data-i18n-placeholder"),
                               ("title", "data-i18n-title"),
                               ("aria-label", "data-i18n-aria")):
                # `:placeholder` / `x-bind:placeholder` hold an EXPRESSION, not a
                # literal — they are check (5)'s business, not this one's.
                am = re.search(r'(?<![-\w:])%s="([^"]{3,})"' % attr, tag)
                if not am or i18n in tag: continue
                v = am.group(1)
                if v in ALLOW or ":" in v[:6] or "{{" in v: continue
                if "data-i18n-exempt" in tag: continue
                if not re.search(r"[A-Za-z]{2,}", v): continue
                bare_attr.append((f.name, src.count("\n", 0, m.start()) + 1, attr, v[:56]))

    # (7) A t('some.key') CALL whose key does not exist. This is the worst of the
    # lot and it was invisible until 2026-09-06: t() returns the RAW KEY on a miss,
    # so the cashier reads "held.toast_load" as a toast. Ten of these existed, and
    # nine were written as t('k') || 'English fallback' — which is DEAD CODE,
    # because the raw key t() hands back is a non-empty string and therefore
    # truthy, so `||` never fires. A fallback that cannot run is worse than none:
    # it is a guard that looks like it works (LESSON #12).
    bad_calls = []
    for f in files:
        src = strip_comments(f.read_text(encoding="utf-8"))
        for m in re.finditer(r"t\(\s*'([A-Za-z_]+\.[A-Za-z0-9_]+)'\s*\)", src):
            key = m.group(1)
            missing = [c for c in codes if key not in tables[c]]
            if missing:
                bad_calls.append((f.name, src.count("\n", 0, m.start()) + 1, key, missing))

    # (8) A LOCAL VARIABLE NAMED `t`. In this app `t` is the global translator
    # (window.t = t, base.html). A `var t = ...` is function-scoped, so it shadows
    # the translator for the WHOLE function including any catch handler, and every
    # t() call in it throws "t is not a function".
    #
    # That shipped in b704: `var t = j.today` in the Shop Pulse loader, three t()
    # calls below it, and the catch handler that was supposed to report the failure
    # threw too. It was found by the AI triage brain reading a console breadcrumb
    # off Angel's own feedback ticket BL-016 — not by any check in this repo.
    #
    # The rule is blunt on purpose: never name a local `t` here. A `let` inside a
    # narrow block is harmless, and it is still not worth the shape.
    # PRECISE, or it will not be read. A first version flagged every local `t` and
    # reported 16 — fifteen of them harmless `const t` in narrow scopes, and one of
    # them THIS COMMENT, because strip_comments() removes HTML comments and not JS
    # ones. A check that cries wolf fifteen times stops being read, which is how
    # the real one hides. So: a `var t` is always reported (function-scoped, so it
    # shadows the whole function including catch handlers), and a `let`/`const t`
    # only when a t() call actually follows it inside the same brace block.
    shadowed = []
    for f in files:
        src = strip_js_comments(strip_comments(f.read_text(encoding="utf-8")))
        for m in re.finditer(r"\b(var|let|const)\s+t\s*=", src):
            kind = m.group(1)
            # the block this declaration lives in, by brace matching
            depth, i, end = 0, m.end(), len(src)
            while i < len(src):
                if src[i] == "{": depth += 1
                elif src[i] == "}":
                    if depth == 0: end = i; break
                    depth -= 1
                i += 1
            block = src[m.end():end]
            risky = kind == "var" or re.search(r"(?<![\w.$])t\s*\(", block)
            if risky:
                shadowed.append((f.name, src.count("\n", 0, m.start()) + 1,
                                 src[m.start():m.start() + 46].split("\n")[0], kind))

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

    if in_xtext:
        print(f"❌ {len(in_xtext)} English literal(s) inside x-text expressions (a FLOOR)")
        for fn, ln, v in in_xtext[:40]: print(f"   {fn}:{ln}  {v!r}")
        if len(in_xtext) > 40: print(f"   … and {len(in_xtext)-40} more")
    else:
        print("✅ no English written inside an x-text expression")

    # A PLACEHOLDER IS READ; A TITLE IS NOT — not on this shop's machine. `title`
    # renders as a hover tooltip and the till is a touchscreen with no pointer, so
    # those strings are invisible there however wrong they are. Reported, never
    # failed on. `aria-label` is the same: real, but not on the glass.
    ph = [h for h in bare_attr if h[2] == "placeholder"]
    other = [h for h in bare_attr if h[2] != "placeholder"]
    if ph:
        print(f"❌ {len(ph)} English placeholder(s) with no key — these ARE on the glass")
        for fn, ln, a, v in ph[:30]: print(f"   {fn}:{ln}  {v!r}")
        if len(ph) > 30: print(f"   … and {len(ph)-30} more")
    else:
        print("✅ every placeholder the cashier reads has a key")
    if other:
        print(f"⚠️  {len(other)} title/aria-label attribute(s) in English — NOT a failure: a")
        print("    title is a hover tooltip and the till is a touchscreen with no pointer.")

    if bad_calls:
        print(f"❌ {len(bad_calls)} t() call(s) whose key does not exist — these print the RAW KEY")
        for fn, ln, k, miss in bad_calls:
            print(f"   {fn}:{ln}  t('{k}')  missing in {','.join(miss)}")
    else:
        print("✅ every t() call in the templates resolves in all four languages")

    if shadowed:
        print(f"❌ {len(shadowed)} local variable(s) named `t` — they shadow the translator")
        for fn, ln, txt, kind in shadowed:
            why = "var is function-scoped" if kind == "var" else "a t() call follows it"
            print(f"   {fn}:{ln}  {txt}   ({why})")
    else:
        print("✅ no local variable shadows the global t() translator")

    print()
    print(f"{len(files)} templates read.")
    print("NOT CHECKED HERE: whether a translation that IS different from English is")
    print("any GOOD. Nobody who speaks French or Italian has read these strings.")
    return 1 if (bad_keys or bare or english or in_script or in_xtext or ph or bad_calls or shadowed) else 0

if __name__ == "__main__":
    sys.exit(main())
