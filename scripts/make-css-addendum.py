#!/usr/bin/env python3
"""
Generate src/static/pos/tailwind-addendum.css — the utilities our templates ask for
that the vendored tailwind.css does not contain.

WHY THIS EXISTS. src/static/pos/tailwind.css is a pre-built, frozen file (12 July, 92KB).
There is no config, no build step and no safelist — that is the deliberate "no node build
in this repo" call. So a class written in a template that is not already in that file does
NOTHING, silently, with the markup reading as if it works. On 2026-09-04 a census found
131 of them: centring that did not centre (left-1/2, -translate-x-1/2), four z-index
utilities that never applied, kiosk modal scrims that did not darken, ~15 guest-facing text
colours, and the UAT login gradient — which is why Felix's tablet showed the shop's own
name in white on near-white for two days.

WHY AN ADDENDUM AND NOT A REBUILT tailwind.css. Regenerating the whole file would need a
different Tailwind version and a different reset, and would move every screen at once —
2026-09-03 already moved 157 elements and that was enough for one week. This file adds only
what is missing, so the blast radius is exactly the classes that previously did nothing.

WHERE THE VALUES COME FROM. Derived from tailwind.css ITSELF wherever a sibling shade
already ships (126 colours do) — same build, same numbers, no memory involved. The handful
that appear nowhere in the file come from the table below and are checked for monotonicity
against the shades the file does carry, so a wrong digit shows up as a palette that goes
light-dark-light instead of quietly being wrong.

Run:  python3 scripts/make-css-addendum.py
Then: NODE_PATH=… node scripts/prove-classes-exist.js
"""
import re, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS  = os.path.join(ROOT, 'src/static/pos/tailwind.css')
OUT  = os.path.join(ROOT, 'src/static/pos/tailwind-addendum.css')
TPL  = os.path.join(ROOT, 'src/templates/pos')

# Shades that appear nowhere in the vendored file. Tailwind v3 defaults.
TABLE = {
    'rose-200': (254, 205, 211), 'rose-500': (244, 63, 94),
    'rose-700': (190, 18, 60),   'rose-800': (159, 18, 57),
    'emerald-950': (2, 44, 34),  'indigo-300': (165, 180, 252),
    'teal-50': (240, 253, 250),  'teal-100': (204, 251, 241),
    'teal-300': (94, 234, 212),  'teal-500': (20, 184, 166),
    'red-900': (127, 29, 29),    'cyan-50': (236, 254, 255),
    'cyan-700': (14, 116, 144),  'cyan-900': (22, 78, 99),
    'rose-50': (255, 241, 242),  'slate-50': (248, 250, 252),
    'white': (255, 255, 255),    'black': (0, 0, 0),
}

def harvest(css):
    pal = {}
    for m in re.finditer(
        r'\.(?:bg|text|border|from|via|to|ring|divide|placeholder|accent)-([a-z]+)-(\d{2,3})'
        r'(?:\\/\d+)?\s*\{([^}]*)\}', css):
        name, shade, body = m.groups()
        h = re.search(r'#([0-9a-fA-F]{6})', body)
        r = re.search(r'rgb\((\d+)\s+(\d+)\s+(\d+)', body)
        if h:
            v = tuple(int(h.group(1)[i:i+2], 16) for i in (0, 2, 4))
        elif r:
            v = tuple(int(x) for x in r.groups())
        else:
            continue
        pal.setdefault(f'{name}-{shade}', v)
    return pal

def check_monotonic(pal):
    """A palette gets darker as the number rises. A typed-in hex that breaks that is a
    typo, and this is the cheapest way to catch one without a second source."""
    bad = []
    by_name = {}
    for k, v in list(pal.items()):
        if '-' not in k: continue
        name, _, shade = k.rpartition('-')
        if not shade.isdigit(): continue
        by_name.setdefault(name, []).append((int(shade), v, k))
    for name, rows in by_name.items():
        rows.sort()
        lum = [(s, 0.2126*v[0] + 0.7152*v[1] + 0.0722*v[2], k) for s, v, k in rows]
        for i in range(1, len(lum)):
            if lum[i][1] > lum[i-1][1] + 1:      # +1 tolerance for near-ties
                bad.append(f'{lum[i][2]} is LIGHTER than {lum[i-1][2]}')
    return bad

# ── the Tailwind scales we need, spelled out rather than computed ──────────────────────
# n/4 rem is the spacing rule, but writing the few we use makes a wrong one visible.
# Tailwind's spacing scale is n/4 rem, with px/0/auto/full as the named exceptions. Computed
# rather than listed: the first version spelled out only the steps we happened to use, so
# `pl-1` fell through and produced nothing at all — silently, which is the whole bug this
# file exists to end.
SPACE_NAMED = {'0': '0px', 'px': '1px', 'auto': 'auto', 'full': '100%',
               '1/2': '50%', '1/3': '33.333333%', '2/3': '66.666667%', '1/4': '25%', '3/4': '75%'}
def space(v):
    if v in SPACE_NAMED: return SPACE_NAMED[v]
    try:
        n = float(v)
    except ValueError:
        return None
    if n < 0 or n > 96: return None
    r = n / 4
    return ('%g' % r) + 'rem'
RADIUS = {'3xl': '1.5rem'}
FONT   = {'6xl': ('3.75rem', '1')}

def esc(c):
    return re.sub(r'([.\[\]()/:!#%,*])', r'\\\1', c)

def colour(pal, token):
    """token: 'rose-600' or 'white' or 'emerald-200/40' -> a css colour string."""
    alpha = None
    if '/' in token:
        token, a = token.split('/', 1)
        alpha = int(a) / 100
    v = pal.get(token) or TABLE.get(token)
    if v is None:
        return None
    return (f'rgb({v[0]} {v[1]} {v[2]} / {alpha:g})' if alpha is not None
            else f'rgb({v[0]} {v[1]} {v[2]})')

def arb(v):
    """[88vh] -> 88vh, [0.15em] -> 0.15em, [60%] -> 60%"""
    return v[1:-1].replace('_', ' ') if v.startswith('[') and v.endswith(']') else None

def decls(cls, pal):
    """The declaration body for ONE utility, or None if this generator does not know it."""
    c = cls
    neg = c.startswith('-')
    if neg: c = c[1:]

    # Gradient stops are not a colour property — they set Tailwind's own custom properties,
    # and `from-*` is the one that DEFINES --tw-gradient-stops. Without it the whole
    # linear-gradient() is invalid and NOTHING paints, which is exactly how the UAT login
    # screen ended up with no background at all while `via-` and `to-` shipped fine.
    # The shapes below are copied from the vendored file's own from-emerald-700 /
    # via-teal-800 / to-slate-900, so this build and that build agree byte for byte.
    m = re.match(r'^(from|via|to)-(.+)$', c)
    if m:
        pos, rest = m.groups()
        v = pal.get(rest) or TABLE.get(rest)
        if v:
            hexv = '#%02x%02x%02x' % v
            rgba0 = f'rgba({v[0]},{v[1]},{v[2]},0)'
            if pos == 'from':
                return (f'--tw-gradient-from: {hexv} var(--tw-gradient-from-position);'
                        f' --tw-gradient-to: {rgba0} var(--tw-gradient-to-position);'
                        ' --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);')
            if pos == 'via':
                return (f'--tw-gradient-to: {rgba0} var(--tw-gradient-to-position);'
                        f' --tw-gradient-stops: var(--tw-gradient-from), {hexv}'
                        ' var(--tw-gradient-via-position), var(--tw-gradient-to);')
            return f'--tw-gradient-to: {hexv} var(--tw-gradient-to-position);'

    m = re.match(r'^(bg|text|border-t|border|divide|placeholder|accent|ring)-(.+)$', c)
    if m:
        prop, rest = m.groups()
        a = arb(rest)
        if prop == 'text' and a:                       # text-[92px]
            return f'font-size: {a}; line-height: 1;'
        col = colour(pal, rest)
        if col:
            return {'bg': f'background-color: {col};',
                    'text': f'color: {col};',
                    'border': f'border-color: {col};',
                    'border-t': f'border-top-color: {col};',
                    'ring': f'--tw-ring-color: {col};',
                    'divide': f'border-color: {col};',
                    'accent': f'accent-color: {col};'}.get(prop)

    m = re.match(r'^(gap-x|gap-y|gap|px|py|pr|pl|pt|pb|mx|my|mr|ml|mt|mb|p|m)-(.+)$', c)
    if m:
        prop, v = m.groups()
        size = space(v) or arb(v)
        if size:
            base = {'p': ['padding'], 'm': ['margin'], 'gap': ['gap'],
                    'gap-x': ['column-gap'], 'gap-y': ['row-gap'],
                    'px': ['padding-left', 'padding-right'], 'py': ['padding-top', 'padding-bottom'],
                    'pr': ['padding-right'], 'pl': ['padding-left'],
                    'pt': ['padding-top'], 'pb': ['padding-bottom'],
                    'mx': ['margin-left', 'margin-right'], 'my': ['margin-top', 'margin-bottom'],
                    'mr': ['margin-right'], 'ml': ['margin-left'],
                    'mt': ['margin-top'], 'mb': ['margin-bottom']}[prop]
            sz = ('-' + size) if neg else size
            return ' '.join(f'{b}: {sz};' for b in base)

    m = re.match(r'^(top|left|right|bottom)-(.+)$', c)
    if m:
        side, v = m.groups()
        size = '50%' if v == '1/2' else (space(v) or arb(v))
        if size:
            return f'{side}: {"-" + size if neg else size};'

    if c == 'translate-x-1/2':
        return ('--tw-translate-x: ' + ('-50%' if neg else '50%') + ';'
                ' transform: translate(var(--tw-translate-x), var(--tw-translate-y, 0));')

    m = re.match(r'^z-(.+)$', c)
    if m:
        v = arb(m.group(1)) or (m.group(1) if m.group(1).isdigit() else None)
        if v: return f'z-index: {v};'

    m = re.match(r'^(w|h|min-w|min-h|max-w|max-h)-(.+)$', c)
    if m:
        prop, v = m.groups()
        size = space(v) or arb(v)
        if size:
            return {'w': 'width', 'h': 'height', 'min-w': 'min-width',
                    'min-h': 'min-height', 'max-w': 'max-width', 'max-h': 'max-height'}[prop] + f': {size};'

    m = re.match(r'^tracking-(.+)$', c)
    if m:
        a = arb(m.group(1))
        if a: return f'letter-spacing: {a};'

    m = re.match(r'^opacity-(\d+)$', c)
    if m: return f'opacity: {int(m.group(1))/100:g};'

    m = re.match(r'^rounded-(.+)$', c)
    if m and m.group(1) in RADIUS: return f'border-radius: {RADIUS[m.group(1)]};'

    m = re.match(r'^text-(\d?xl|6xl)$', c)
    if m and m.group(1) in FONT:
        s, lh = FONT[m.group(1)]
        return f'font-size: {s}; line-height: {lh};'

    m = re.match(r'^col-span-(\d+)$', c)
    if m: return f'grid-column: span {m.group(1)} / span {m.group(1)};'

    m = re.match(r'^scale-(\d+)$', c)
    if m:
        s = int(m.group(1))/100
        return (f'--tw-scale-x: {s:g}; --tw-scale-y: {s:g};'
                ' transform: translate(var(--tw-translate-x, 0), var(--tw-translate-y, 0))'
                ' scale(var(--tw-scale-x), var(--tw-scale-y));')

    if c == 'prose':
        # @tailwindcss/typography is a plugin we do not ship and are not going to. This is
        # the honest subset: kb_approvals.html renders approved knowledge-base articles with
        # x-html, and without SOMETHING here Tailwind's preflight has already stripped the
        # headings and the list bullets, so an article renders as one wall of text.
        return None   # handled as a block below — needs descendant selectors
    m = re.match(r'^cursor-(zoom-out|zoom-in|wait|default|pointer|not-allowed|help|move|text|crosshair)$', c)
    if m: return f'cursor: {m.group(1)};'
    if c == 'underline':        return 'text-decoration-line: underline;'
    m = re.match(r'^line-clamp-(\d+)$', c)
    if m:
        return ('overflow: hidden; display: -webkit-box;'
                f' -webkit-box-orient: vertical; -webkit-line-clamp: {m.group(1)};')
    return None

# Classes that are SUPPOSED to have no rule of their own.
SINGLE_WORD_UTILITIES = set('''
block
inline
flex
grid
hidden
contents
table
absolute
relative
fixed
sticky
static
italic
underline
truncate
uppercase
lowercase
capitalize
group
container
isolate
invisible
visible
rounded
border
shadow
ring
transform
transition
resize
sr-only
antialiased
'''.split())

NO_RULE = {
    # A marker Tailwind reads only as an ancestor of group-hover:* — no declarations of its own.
    'group',
    # postcard.html's toolbar styles its links with `.toolbar a`, by TAG. `.sheet` is a hook
    # that never needed a rule; the link has looked right all along. Listed rather than
    # generated so the census stops reporting it and nobody "fixes" it twice.
    'sheet',
}

VARIANTS = {
    'hover': ':hover', 'focus': ':focus', 'active': ':active', 'disabled': ':disabled',
}
SCREENS = {'sm': '640px', 'md': '768px', 'lg': '1024px'}

def rule_for(cls, pal):
    """Full CSS text for one class, or None."""
    if cls in NO_RULE:
        return f'/* .{cls} — a marker class, no declarations by design */\n'
    if cls == 'prose':
        return (
            '/* .prose — the subset @tailwindcss/typography would have given us. The plugin is\n'
            '   not vendored and is not going to be; this covers what kb_approvals.html renders\n'
            '   through x-html, where preflight has already flattened every heading and list. */\n'
            '.prose { color: #374151; line-height: 1.75; }\n'
            '.prose > * + * { margin-top: 1.25em; }\n'
            '.prose h1 { font-size: 2.25em; font-weight: 800; line-height: 1.15; margin-top: 0; }\n'
            '.prose h2 { font-size: 1.5em;  font-weight: 700; line-height: 1.33; margin-top: 2em; }\n'
            '.prose h3 { font-size: 1.25em; font-weight: 600; line-height: 1.6;  margin-top: 1.6em; }\n'
            '.prose h1, .prose h2, .prose h3, .prose h4 { color: #111827; }\n'
            '.prose ul { list-style: disc;    padding-left: 1.625em; }\n'
            '.prose ol { list-style: decimal; padding-left: 1.625em; }\n'
            '.prose li { margin: .5em 0; }\n'
            '.prose a { color: #4f46e5; text-decoration: underline; }\n'
            '.prose strong { font-weight: 600; color: #111827; }\n'
            '.prose code { font-family: ui-monospace, monospace; font-size: .875em;\n'
            '              background: #f3f4f6; padding: .15em .35em; border-radius: .25rem; }\n'
            '.prose pre { background: #1f2937; color: #f9fafb; padding: 1em; border-radius: .5rem;\n'
            '             overflow-x: auto; }\n'
            '.prose blockquote { border-left: .25rem solid #e5e7eb; padding-left: 1em;\n'
            '                    font-style: italic; color: #4b5563; }\n'
            '.prose img { max-width: 100%; height: auto; }\n'
            '.prose hr { border-color: #e5e7eb; margin: 2em 0; }\n')
    sel = '.' + esc(cls)

    for v, pseudo in VARIANTS.items():
        if cls.startswith(v + ':'):
            body = decls(cls[len(v)+1:], pal)
            return f'{sel}{pseudo} {{ {body} }}\n' if body else None
    if cls.startswith('group-hover:'):
        body = decls(cls[len('group-hover:'):], pal)
        return f'.group:hover {sel} {{ {body} }}\n' if body else None
    for s, px in SCREENS.items():
        if cls.startswith(s + ':'):
            body = decls(cls[len(s)+1:], pal)
            return f'@media (min-width: {px}) {{ {sel} {{ {body} }} }}\n' if body else None

    if cls.startswith('!'):
        body = decls(cls[1:], pal)
        if body:
            body = re.sub(r';\s*', ' !important; ', body).strip()
            return f'{sel} {{ {body} }}\n'
        return None

    if cls.startswith('divide-'):
        body = decls(cls, pal)
        return f'{sel} > :not([hidden]) ~ :not([hidden]) {{ {body} }}\n' if body else None
    if cls.startswith('placeholder-'):
        body = decls('text-' + cls[len('placeholder-'):], pal)
        return f'{sel}::placeholder {{ {body} }}\n' if body else None

    body = decls(cls, pal)
    return f'{sel} {{ {body} }}\n' if body else None

# ── the census: what the templates ask for that nothing defines ────────────────────────
def page_styles(txt):
    return ''.join(m.group(0) for m in re.finditer(r'<style[\s\S]*?</style>', txt))

def census(css, extra_css):
    base = page_styles(open(os.path.join(TPL, 'base.html')).read())
    seen = {}
    for f in sorted(glob.glob(os.path.join(TPL, '*.html'))):
        txt = open(f).read()
        own = page_styles(txt)
        # Two sources, because the second one is where the login page's whole palette hid.
        #   1. literal class="…" attributes
        #   2. Jinja string literals assigned with {% set %} — login.html picks its gradient
        #      per environment that way, so `from-cyan-700` never appeared in any class=""
        #      and the census reported the page clean while the UAT tablet showed the shop's
        #      own name in white on near-white for two days.
        segs = []
        for m in re.finditer(r'(?<![-:\w])class="([^"]*)"', txt):
            seg = m.group(1)
            if '{{' in seg or '{%' in seg:      # a Jinja-built class list; the literals below cover it
                continue
            segs.append(seg)
        # Alpine bindings name real classes too: :class="x ? 'bg-rose-50' : 'bg-white'".
        # But the SAME attribute holds comparison operands — :class="method === 'cash' ? …"
        # — and a heuristic that only asks "does this look like a word" harvested `cash`,
        # `visa`, `twint` and 41 other data values as if they were utilities. A utility
        # either carries a separator or is one of the handful of single-word ones.
        for m in re.finditer(r':class="([^"]*)"', txt):
            for lit in re.finditer(r"'([^']*)'", m.group(1)):
                toks = lit.group(1).split()
                if toks and all(
                        (re.search(r'[-:/\[]', tk) or tk in SINGLE_WORD_UTILITIES)
                        and re.match(r'^-?[a-z][-a-z0-9:/\[\]().!#%,]*$', tk)
                        for tk in toks):
                    segs.append(lit.group(1))
        for m in re.finditer(r"{%-?\s*set\s+\w+\s*=\s*'([^']*)'", txt):
            lit = m.group(1)
            # only treat it as a class list if every token looks like one
            toks = lit.split()
            if toks and all(re.match(r'^-?[a-z][-a-z0-9:/\[\]().!#%,]*$', tk) for tk in toks):
                segs.append(lit)
        for seg in segs:
            for c in seg.split():
                if not c or not re.match(r'^[-a-z0-9:/\[\]().!#%,]+$', c, re.I):
                    continue
                # A SUBSTRING TEST IS NOT A SELECTOR TEST. `.bg-rose-50` is a substring of
                # `.bg-rose-500`, and `.pl-1` of `.pl-1\.5` — so seven classes were reported
                # as already present, no rule was generated, and prove-classes-exist.js
                # (which measures the browser rather than grepping a file) found them dead.
                # A class name ends where an identifier character stops.
                pat = re.compile(re.escape('.' + esc(c)) + r'(?![0-9A-Za-z_\\-])')
                if any(pat.search(b) for b in (css, base, own, extra_css)):
                    continue
                seen.setdefault(c, set()).add(os.path.basename(f))
    return seen

def main():
    css = open(CSS).read()
    pal = harvest(css)
    pal.update({k: v for k, v in TABLE.items() if k not in pal})
    bad = check_monotonic(pal)
    if bad:
        print('PALETTE LOOKS WRONG — a shade is lighter than a lighter-numbered one:')
        for b in bad: print('   ' + b)
        sys.exit(2)
    print(f'palette: {len(pal)} colours ({len(pal) - len(TABLE)} read out of tailwind.css)')

    missing = census(css, '')
    rules, unresolved = [], []
    for c in sorted(missing):
        r = rule_for(c, pal)
        (rules.append((c, r)) if r else unresolved.append(c))

    head = (
        '/* tailwind-addendum.css — GENERATED by scripts/make-css-addendum.py. Do not edit.\n'
        '   The utilities our templates ask for that the vendored tailwind.css does not carry.\n'
        '   Loaded immediately AFTER tailwind.css so these sit with the other utilities:\n'
        '   above Banco\'s base classes, below nothing. Regenerate after adding new classes,\n'
        '   and scripts/prove-classes-exist.js fails the build if you forget.\n'
        f'   {len(rules)} rules. */\n\n')
    open(OUT, 'w').write(head + ''.join(r for _, r in rules))
    print(f'wrote {OUT}  —  {len(rules)} rules')
    if unresolved:
        print(f'\nNOT GENERATED ({len(unresolved)}) — these need a decision, not a rule:')
        for c in unresolved:
            print(f'   {c:26} {", ".join(sorted(missing[c]))[:60]}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
