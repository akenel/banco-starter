# TESTING — how to prove Banco works before claiming it does

*There is no test runner here and no `npm test`. The proofs are **27 standalone scripts** you invoke
one at a time, on purpose. This file is the handoff doc for that: what they are, what they need, and
what they will do to your data if you point them at the wrong machine.*

*Written 2026-08-27. The rule they all serve is in [`STANDING-RULES.md`](STANDING-RULES.md) #4 and #5:
"fixed" is a claim until the output is verified, and a human confirming it beats a green test.*

---

## The one thing that trips everyone up

**Playwright is borrowed, not installed.** This repo has **no `package.json`, no `node_modules`, and
no node build — deliberately.** Alpine.js is vendored as a plain file so a shop owner can clone this
and run it without a JavaScript toolchain. Adding `node_modules` would break that promise.

So the browser tests reach *outside* the repo for Playwright:

```bash
NODE_PATH=/path/to/any/node_modules node scripts/prove-till-18plus.js
```

On Angel's machine that path is `/home/angel/repos/helixnet/node_modules`. **Any** `node_modules`
containing `playwright` works. If it cannot find it the script exits **2** and prints the fix rather
than failing strangely. Browsers themselves cache in `~/.cache/ms-playwright` (`npx playwright
install chromium` once, from wherever you did install it).

---

## What's in the box

| | count | what they are |
|---|---|---|
| `scripts/prove-*.js` driving a **real browser** | **21** | Playwright + headless Chromium. The only things in this repo that can see an `x-show`. |
| `scripts/prove-*.js` with **no browser** | **1** | `prove-webcam-button-shows.js` — a pure-node harness, needs no stack and no Playwright. |
| `scripts/prove-*.py` **HTTP/DB probes** | **5** | `prove-age-evidence` · `prove-cash-box` · `prove-cash-rounding` · `prove-catalog-export` · `prove-name-alias`. Server-side truth only. |

**A Python probe cannot see a screen.** `prove-age-evidence.py` was 25/25 green on an 18+ feature no
cashier could reach, because an HTTP probe cannot see a hidden button. That is why the `.js` ones
exist. Pick by what you are claiming: server behaviour → `.py` is enough; anything a person looks at
or taps → it has to be the browser, or a human.

---

## Before you run anything

**1. A stack must be up and reachable.** Default target is `http://localhost:3000`, overridden with
`BANCO_URL`. Stand it up with [`QUICKSTART.md`](QUICKSTART.md) (`./scripts/rebuild.sh` then
`./scripts/standup.sh`).

**2. Some expect the demo catalogue.** Several look for seeded products by name — e.g.
`prove-till-18plus.js` wants `CBD Gummy`. Against a shop running `HX_SEED_DEMO=false` they fail for
reasons that look like bugs but are missing fixtures. Override with `BANCO_AGE_ITEM`,
`BANCO_PLAIN_ITEM`, `BANCO_SECOND_ITEM`, `PROBE_EAN`.

**3. `src/` is baked into the image — there is no bind mount.** `docker compose restart app` restarts
the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh` first, or you
will test the previous build and believe it.

---

## ⚠️ These write real data. Two guards, and they are not the same.

| guard | scripts | what it unlocks |
|---|---|---|
| `BANCO_ALLOW_FAKE_SALES=1` | **3** — `prove-till-18plus.js`, `prove-mix-and-match.js`, `prove-age-evidence.py` | **Rings completed sales.** A completed transaction is a line in the Kassenbuch. They refund afterwards; the refund is also a line. |
| `BANCO_ALLOW_CATALOG_WRITES=1` | **11** — the pricing, barcode and shelf-row provers | Creates and edits products, prices and barcodes. |

Both default to off so it cannot happen by accident. **Neither guard makes it safe to point these at
the shop's live books** — they make it *possible*, which is not the same thing. Run them against
localhost or a throwaway.

**Cleanup:** test products are prefixed `ZZPROBE` and 7 scripts sweep in a `finally`. A crashed run
leaves residue:

```sql
DELETE FROM products WHERE sku LIKE 'ZZPROBE%';
DELETE FROM customers WHERE handle LIKE 'ZZTEST-%';   -- browser-prover member fixtures
```

---

## The login users are a deliberate choice, not boilerplate

Scripts log in as `ralph` (manager, 38 call sites), `pam` (cashier, 11) and `felix` (admin, 8) —
demo Keycloak users from the imported realm. Override with `BANCO_USER` / `BANCO_PASS`.

**`ralph` rather than `pam` is on purpose.** It keeps machine-written evidence separable from the
account a human rings real sales on. This bit twice: probe-written refusals turned up inside Angel's
own testsheet evidence and had to be picked out by hand. Do not "simplify" them to one user.

---

## Four mechanics that cost real time to discover

1. **Headless Chromium auto-DISMISSES native `confirm()`.** Without `page.on('dialog', d =>
   d.accept())` every sale silently cancels and the button looks dead. 4 scripts carry this.
2. **Wait for Alpine to hydrate before any `evaluate()`.** 9 scripts use a `waitAlpine()` helper.
   Read state too early and you get the pre-hydration DOM.
3. **The auth token lives at `sessionStorage['pos_token']`.**
4. **`BANCO_HEADED=1` opens a visible browser.** The single best debugging move when a script
   disagrees with you.

---

## The convention: watch it go red

**A new test is not trusted here until it has been seen failing.** Several scripts carry explicit
guard-break cases that must stay SILENT — assertions proving the check does *not* fire when it
shouldn't. Reverting each feature one at a time and counting the reds has caught something every
time it has been done ([`CLAUDE.md`](CLAUDE.md) pattern 4).

If you add a prover, add the guard-break with it, and say in the header how many should go red.

---

## Run them

```bash
# server-side only — no browser needed
BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py

# the actual screens
BANCO_ALLOW_FAKE_SALES=1 \
NODE_PATH=/home/angel/repos/helixnet/node_modules \
node scripts/prove-till-18plus.js

# no stack, no browser, no Playwright
node scripts/prove-webcam-button-shows.js
```

**Before promoting to prod**, `scripts/prove-till-18plus.js` (45 checks) is the gate.

---

## What this does not cover, and cannot

Worth knowing before you trust a green run — each of these is a real escape, not a hypothetical:

- **A test that finishes in five minutes cannot see a five-minute timeout.** Silent token refresh had
  never worked in the sandbox; every probe runs in 90 seconds with a fresh token, so nothing here
  could have found it. A human using it for ten minutes did.
- **A harness can be green on a shape it cannot make.** `prove-cart-agrees-with-till` compared 320
  quantities all day while the cart quoted a discount the drawer would not give — because it compares
  line totals and never *constructs a discounted basket*.
- **Verification against the database cannot find a wrong barcode bind.** A wrong one looks exactly
  like a right one from inside Postgres. Only re-scanning the packet tells them apart.
- **Nothing here proves a label came out of a printer.** "CUPS drained the job" is not "a label
  printed."

The full list, each with the evidence that earned it, is in [`LESSONS.md`](LESSONS.md); the patterns
that have bitten more than once are distilled at the top of [`CLAUDE.md`](CLAUDE.md).
