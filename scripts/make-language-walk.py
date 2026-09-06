#!/usr/bin/env python3
"""make-language-walk.py — ONE SHEET PER LANGUAGE, ONE CLICK PER SCREEN.

Angel, 2026-09-06: "i can take screen shots all day its fast … make an html page
with quick click hyper links for each card and the sub pages too … i would do
like an italian html then a separate for french and then de … some how have it
there could be a simple way we start the timer i take screenshot save them and
finish and press the stop timer."

All of that already exists in onboarding/testsheets/TEMPLATE.html — steps-as-data,
a per-step link, PASS/ISSUE/FAIL, notes, a timer that starts on the first mark and
freezes on the last, and a stamp on every step (now to the SECOND, so a run of 30
screenshots matches the steps by filename with no renaming). The standing rule in
CLAUDE.md is never to invent a second sheet format, so this generates FROM that
shell rather than beside it.

What it does that a hand-written sheet cannot:

  1. THE SCREEN LIST COMES FROM THE ROUTER. Every @html_router.get that returns a
     template becomes a step. A screen added next month appears in the sheet the
     next time this is run; a hand-typed list would quietly stop being the shop.
  2. EVERY LINK CARRIES ?lang=xx. base.html reads ?lang= first, ahead of stored
     preference, and persists it — so one tap sets the language AND navigates.
     Without that, checking 34 screens in 3 languages is 102 trips through a
     dropdown.
  3. EACH STEP SAYS WHAT IS STILL KNOWN-BROKEN ON THAT SCREEN, counted live by
     prove-one-box-one-language.py. So the sheet does not just ask "is this
     right?" — it asks Angel to CONFIRM OR DENY the instrument, which is the only
     thing that has ever caught what the instrument cannot see (a translation that
     exists and is wrong: `Sistemazione`, 2026-09-06).

    python3 scripts/make-language-walk.py            # it, fr, de
    python3 scripts/make-language-walk.py it         # just one

Angel, 2026-09-06.
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTER = ROOT / "src/routes/pos_router.py"
TEMPLATE = ROOT / "onboarding/testsheets/TEMPLATE.html"
OUT = ROOT / "onboarding/testsheets"
HOST = "https://banco.wolfhold.app"

# One neutral sentence, identical on every step. Says WHAT was looked at and claims
# NOTHING — no "looks wrong", no "some text is English". BL-019 proved a leading body
# is enough to make triage confirm a defect that is not there.
NEUTRAL_BODY = {
    "it": "Checking this screen in Italian.",
    "fr": "Checking this screen in French.",
    "de": "Checking this screen in German.",
}

LANGS = {
    # (English name, the language's own name). An earlier version also carried the
    # phrase for "every word" and dropped it into an English sentence, producing
    # "ogni parola on this screen is Italiano" — the exact one-box-two-languages
    # bug this whole walk exists to find, in the sheet that finds it.
    "it": ("Italian", "Italiano"),
    "fr": ("French", "Français"),
    "de": ("German", "Deutsch"),
}

# Who stands in front of it. This ordering IS the plan — the till first, the
# bench last, same as onboarding/the-language-audit.html.
GROUPS = [
    ("A", "The till — where the cashier stands", [
        "/pos", "/pos/scan", "/pos/checkout", "/pos/shift", "/pos/closeout",
        "/pos/my-day", "/pos/transactions", "/pos/customer-lookup",
        "/pos/held-orders", "/pos/dashboard",
    ]),
    ("B", "Felix's office — the owner, weekly", [
        "/pos/settings", "/pos/catalog", "/pos/audit", "/pos/join-card",
        "/pos/reports", "/pos/age-report", "/pos/reports/products",
        "/pos/suppliers", "/pos/reorder", "/pos/my-tickets",
    ]),
    ("C", "The bench — cataloguing, nobody sells with it", [
        "/pos/shelf-intake", "/pos/catalog-misses", "/pos/catalog-health",
        "/pos/cleanup", "/pos/receiving", "/pos/hardware", "/pos/labels/batch",
        "/pos/search", "/pos/kiosk", "/pos/products", "/pos/selftest",
        "/pos/hypercare", "/pos/kb-approvals", "/pos/admin",
    ]),
]

# A screen a cashier should never be sent to blind during trading.
CAREFUL = {
    "/pos/checkout": "Do NOT press a payment button. Look, screenshot, come back.",
    "/pos/closeout": "Look only. Do not file a close-out.",
    "/pos/shift":    "Look only. Do not open or close the drawer.",
}


def build_stamp():
    """b<commit-count> · <short sha> — the same pair the status bar shows.

    src/build_info.py builds the label as "b" + the git commit count, and the
    deploy prints "commit 5e15e56 (b704)". Angel's FIRST report on 2026-09-06
    came back reading "build undefined", because the shell takes it from
    meta['Build'] and this generator never set one. A sheet with no build stamp
    is a sheet whose marks are about an unknown build — which is the whole point
    of the step 0.1 the shell prepends.
    """
    def git(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True,
                                  cwd=ROOT).stdout.strip()
        except Exception:
            return ""
    n, sha = git("rev-list", "--count", "HEAD"), git("rev-parse", "--short", "HEAD")
    return f"b{n} · {sha}" if n and sha else (sha or "unknown")


def routes():
    """Every page route, straight from the router — never a typed list."""
    src = ROUTER.read_text(encoding="utf-8")
    out, seen = [], set()
    for blk in re.split(r"(?=@html_router\.get\()", src):
        m = re.match(r'@html_router\.get\(\s*"([^"]+)"', blk)
        if not m or "{" in m.group(1):
            continue
        t = re.search(r'TemplateResponse\(\s*"(pos/[^"]+\.html)"', blk)
        if not t or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        out.append((m.group(1), t.group(1).split("/")[1]))
    return dict(out)


def findings():
    """Live counts per template, from the harness. Never hand-copied."""
    r = subprocess.run([sys.executable, str(ROOT / "scripts/prove-one-box-one-language.py")],
                       capture_output=True, text=True, cwd=ROOT)
    per = defaultdict(lambda: defaultdict(int))
    kind = None
    for line in r.stdout.splitlines():
        if line.startswith("❌") or line.startswith("⚠️") or line.startswith("✅"):
            low = line.lower()
            kind = ("bare" if "bare english string" in low else
                    "ph" if "placeholder(s) with no key" in low else
                    "xtext" if "x-text" in low else
                    "script" if "<script>" in low else
                    "tip" if "title/aria" in low else None)
            continue
        if kind and line.startswith("   ") and ".html" in line:
            per[line.split(":")[0].strip()][kind] += 1
    return per


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


PHASE0 = [
    ("P1", "Tap the link, let the page settle, then tap the <b>💬 button</b> in the bottom bar. "
           "Type the title from the chip below, add a line only if something looks wrong, "
           "and <b>Send</b>.",
           "A <b>ticket number</b> comes back — <code>BL-###</code> — and the panel already had a "
           "<b>thumbnail of this screen</b> in it before you typed anything.",
           "Two checks in one tap. No thumbnail means triage is reading nothing, because the "
           "screenshot IS what the vision model gets. And the number is the unit of work from "
           "here on."),
    ("P2", "Open <b>My tickets</b> and look at the one you just filed. Find the smallest grey "
           "text in the attached shot and try to read it.",
           "It is there, with your title, and <b>you can read the small text</b>.",
           "The capture went to 1600px / q0.85 in b704 for exactly this — at the old 1100 / 0.7 a "
           "tablet screen was halved before being JPEG'd. If it is mush, say so and we raise it "
           "again, because reading 12px Italian is the entire job."),
    ("P3", "Tell the copilot the ticket number and let triage run on that ONE ticket.",
           "Either a clean rewritten ticket with a type, a severity and a confidence — <b>or a "
           "clearly-marked fallback</b> saying no brain was reachable. And whatever it says about "
           "the screenshot describes <b>the screen you were actually on</b>.",
           "This is the step the whole plan turns on. If BH_OLLAMA_KEY is not set on prod, triage "
           "degrades GRACEFULLY and returns boilerplate — which from a distance looks like it "
           "worked. And a brain that hallucinates a screen will hallucinate a fix. Better to learn "
           "both on ticket one than on ticket ninety."),
]


def build(lang, only=None, phase0=False):
    name, native = LANGS[lang]
    pages, found = routes(), findings()
    listed = {p for _, _, ps in GROUPS for p in ps}
    extra = [p for p in pages if p not in listed]

    sections = []
    # Two routes can render the SAME template (/pos/products -> scan.html,
    # /pos/admin -> dashboard.html). Both are real screens and worth a look, but
    # the second one cannot show new English — so say so, rather than have Angel
    # spend a step discovering it. Costs nothing; saves a shot and the doubt.
    seen_tpl = {}
    for gid, gtitle, paths in GROUPS + ([("D", "Anything the groups above missed", extra)] if extra else []):
        steps = []
        for i, path in enumerate(sorted(set(paths) & set(pages)), 1):
            tpl = pages[path]
            f = found.get(tpl, {})
            n_bare, n_ph = f.get("bare", 0), f.get("ph", 0)
            n_x, n_s = f.get("xtext", 0), f.get("script", 0)
            known = n_bare + n_ph + n_x + n_s

            label = path.replace("/pos/", "").replace("/pos", "sign-in").replace("/", " · ") or "sign-in"
            do = (f'Tap the link. When the page has settled, tap <b>💬</b> in the bottom bar, '
                  f'paste the two lines below, and <b>Send</b>. Nothing else — do not add your own '
                  f'wording.')
            if path in CAREFUL:
                do += f' <b>{CAREFUL[path]}</b>'
            twin = seen_tpl.get(tpl)
            seen_tpl.setdefault(tpl, f'{gid}{i}')

            if twin:
                expect = (f'<b>Same screen as step {twin}</b> — a different door into '
                          f'<code>{tpl}</code>. Glance at it; if it looks like {twin} did, '
                          f'mark it and move on. No second screenshot needed.')
                why = (f'Two routes, one template. Worth one look in case the door changes '
                       f'what it shows, worth no more than that.')
            elif known == 0:
                expect = (f'<b>Every word on this screen is {name} ({native}).</b> '
                          f'Mark <b>ISSUE</b> the moment you see one English word — '
                          f'the check says there are none, so anything you find is a hole in it.')
                why = (f'<code>{tpl}</code> reports CLEAN. That is a claim by a script that has '
                       f'been wrong six times; your eyes are the only thing that has ever caught '
                       f'a translation that EXISTS and is wrong.')
            else:
                bits = []
                if n_bare: bits.append(f'{n_bare} untranslated')
                if n_ph:   bits.append(f'{n_ph} in a placeholder box')
                if n_x:    bits.append(f'{n_x} built in code')
                if n_s:    bits.append(f'{n_s} in a script')
                expect = (f'<b>Expect English here — about {known} strings</b> '
                          f'({" · ".join(bits)}). Screenshot it and mark <b>ISSUE</b>. '
                          f'Mark <b>FAIL</b> only if the screen is broken, not merely English.')
                why = (f'<code>{tpl}</code> is not fixed yet. The shot is the before-picture, '
                       f'and it tells us whether {known} is anywhere near the truth.')

            steps.append({
                "id": f"{gid}{i}",
                "do": do,
                "expect": expect,
                "why": why,
                "link": {"href": f"{HOST}{path}?lang={lang}", "text": f"{path}  ?lang={lang}  ↗"},
                # Tap to copy, paste into the 💬 title box. A fixed shape means 34
                # tickets can be grouped, sorted and closed as a batch instead of
                # read one at a time.
                # THE BODY IS THE SAME ON EVERY STEP, DELIBERATELY. It is the control.
                # With one wording across ten screens the only thing that varies is the
                # SCREEN, so any difference in what triage says is caused by the screen
                # and nothing else. It also tests the one property BL-019 nearly failed:
                # given identical input text, does it still tell a clean screen from a
                # broken one? A body that changes per screen would hand it the answer —
                # which is exactly how BL-019 got a confident phantom out of "checking
                # this screen for language problems".
                "ticket": {"title": f"{lang.upper()} {gid}{i} · {label}",
                           "body": NEUTRAL_BODY[lang]},
            })
        if steps:
            sections.append({"id": gid, "title": gtitle,
                             "time": f"~{max(1, round(len(steps) * 0.75))} min", "steps": steps})

    if only:
        sections = [x for x in sections if x["id"] in only]

    # Phase 0 rides in front, as its own section, ONCE — it proves the loop before
    # 34 tickets are fired at a system that has never seen more than a handful.
    if phase0 and sections:
        first = sections[0]["steps"][0]["link"]["href"]
        # P1 lands on the same screen as A1 but is a DIFFERENT ticket — it is the
        # smoke test, not the language check. Same title on both would give two
        # tickets nobody can tell apart.
        sections.insert(0, {
            "id": "P", "title": "Phase 0 — prove the loop on ONE page first", "time": "~5 min",
            "steps": [{"id": pid, "do": do, "expect": exp, "why": why,
                       **({"link": {"text": "Open the first screen  ↗", "href": first},
                           "ticket": {"title": f"{lang.upper()} P1 · smoke",
                                      "body": "Phase 0 — checking the feedback loop."}}
                          if pid == "P1" else {})}
                      for pid, do, exp, why in PHASE0]})

    total = sum(len(s["steps"]) for s in sections)
    # A cut sheet gets its OWN key and its own name. Two sheets sharing a key means
    # a tester's marks from one reappear on the other's steps — the template's own
    # header says to bump the version when the steps change, and a section filter
    # changes the steps.
    scope = ("-" + "".join(sorted(only)).lower()) if only else ""
    which = (f"section {'+'.join(sorted(only))}" if only else "every screen")
    sheet = {
        "key": f"banco-language-walk-{lang}{scope}{'-p0' if phase0 else ''}-v2",
        "eyebrow": f"Banco POS · language walk · {lang.upper()}",
        "title": (f"{name}: {which}" if only else f"Every screen in {name}"),
        "standfirst": (
            f"One tap per screen, each link already carrying <code>?lang={lang}</code> so you never "
            f"touch the language dropdown. Open it, screenshot it, mark it, next. "
            f"<b>The timer starts on your first mark and freezes on your last</b>, and every step "
            f"stamps the time to the second — so the screenshots in your Pictures folder line up "
            f"with the steps that produced them without renaming a thing. "
            + (f"<b>Phase 0 first — six checks on ONE page</b>, before 34 tickets are fired at a "
               f"system that has never seen more than a handful. Then " if phase0 else "<b>")
            + f"{total - (6 if phase0 else 0)} screens{'' if phase0 else '.</b>'}"
            + (", one ticket each.</b>" if phase0 else "")),
        "meta": [["Shop", "banco.wolfhold.app", f"{HOST}/pos?lang={lang}"],
                 ["Build", build_stamp()],
                 ["Language", f"{name} ({native})"],
                 ["Log in as", "felix for B and C · pam or layla for A"],
                 ["Counts from", "scripts/prove-one-box-one-language.py"],
                 ["Budget", f"~{max(1, round(total * 0.75))} min"]],
        "safety": {
            "title": "Look. Do not sell.",
            "body": ("This walk touches Checkout, Cash Box and Close-out. <b>Press no payment "
                     "button and file no close-out.</b> A completed transaction is a line in the "
                     "Kassenbuch and cannot be taken back out. Everything here is a screenshot, "
                     "nothing here is a sale."),
        },
        "setup": {"needs": [f"the language showing <b>{lang.upper()}</b> in the top bar after the first link",
                            "screenshots saving somewhere you can find them",
                            "the same build on screen as the one you are testing"]},
        "sections": sections,
    }

    shell = TEMPLATE.read_text(encoding="utf-8")
    a = shell.index("const SHEET = {")
    b = shell.index("\n};</script>", a) + len("\n};")
    body = "const SHEET = " + json.dumps(sheet, ensure_ascii=False, indent=2) + ";"
    out = OUT / f"2026-09-06-language-walk-{lang}{scope}.html"
    out.write_text(shell[:a] + body + shell[b:], encoding="utf-8")
    return out, total


if __name__ == "__main__":
    args = sys.argv[1:]
    only = None
    phase0 = "--phase0" in args
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    want = [a for a in args if a in LANGS] or list(LANGS)
    for lang in want:
        if lang not in LANGS:
            print(f"unknown language {lang!r} — one of {', '.join(LANGS)}", file=sys.stderr)
            raise SystemExit(2)
        path, n = build(lang, only=only, phase0=phase0)
        print(f"✅ {path.relative_to(ROOT)}  —  {n} screens, every link carrying ?lang={lang}")
    print("\nOpen one in the browser, work top to bottom, then Copy report at the end.")
