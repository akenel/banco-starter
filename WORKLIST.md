# WORKLIST — Banco POS starter

*The single source of truth for what's next, in order. Say the code word **"OPEN SHOP"** and the copilot opens this, states the top items, and starts the first actionable one. The bigger arc is in [`ROADMAP.md`](ROADMAP.md).*

> **This file is deliberately short.** It hit **1,734 lines** on 2026-08-13, at which point it
> stopped being a list you can open and act on. The narrative moved to
> [`worklist-archive/`](worklist-archive/) — **nothing was deleted**, and the split was verified
> line-for-line. **Keep it under ~150 lines**: when an item is finished, move it to
> [`worklist-archive/done.md`](worklist-archive/done.md) with its commit hashes; when a thread
> grows a long write-up, the write-up goes to the archive and a one-line pointer stays here.

*Last updated: 2026-08-13.*

---

## 🔴 FIXED TODAY, FOUND BY ANGEL IN TEN MINUTES OF ORDINARY USE — 2026-08-13

**Silent token refresh had NEVER worked in the sandbox.** He pressed a refusal button
mid-testsheet, was logged out, and **the refusal was never recorded** — the exact failure
that feature exists to prevent. Keycloak's own log:

```
REFRESH_TOKEN_ERROR  reason="Invalid token issuer.
                      Expected 'http://keycloak:8080/realms/kc-pos-realm-dev'"
```

The browser logs in at `localhost:8090` so its token says `iss=http://localhost:8090/…`;
`/pos/refresh` presented it to `keycloak:8080` from inside the network and Keycloak
refused. **Every session hard-logged-out ~5 min after login.** `compose.prod.yml` pins
`KC_HOSTNAME` and was always right — so the *broken* environment was the one where we
decide whether things work.

**Suite is 44 checks now** — Angel's exact sequence (refuse → dead session → log back in →
the record arrives, marked late) runs in 90 seconds.

**Fixed (`9f34f85`):** `KC_HOSTNAME_URL` pinned in `compose.yml`; `postboot-check.py` now
logs in and refreshes **for real** as a critical check (sabotaged → NOT READY, restored →
green); and the till **parks a refusal in `localStorage` before it posts**, flushing on
next login, with the row saying `[recorded late …]`. `occurred_at` stays the server's
clock — a client that can backdate evidence is not evidence.

⚠️ **No probe of mine could have found this.** They all finish in ~90 s with a fresh
token, and a harness that finishes inside five minutes cannot see a five-minute timeout.
Now pattern 6 in `CLAUDE.md`.

---

## 🔍 OPEN, NOT REPRODUCED — the till felt slow in Angel's browser

`[Violation] 'click' handler took 1144–2077ms`, seven times between 13:05 and 13:14 on
2026-08-13. **Measured here and could not reproduce it:** Add-to-cart, quantity, payment
select all run **80–100 ms**, and Checkout 500 ms (a page navigation), with zero
violations — in headless *and* in a fully rendered browser under Xvfb. One "Add" click
fires **no** network at all.

Two theories ruled out by checking rather than guessing: no rebuild was running during
that window (the app container last started 12:52, his violations begin 13:05), and the
i18n MutationObserver is already scoped to `childList`+`subtree` on *added* nodes only,
with a comment naming this exact hazard.

**What is left, and it is testable in 30 seconds:** his screenshot shows **DevTools open**
with the Elements panel live, plus several browser extensions. Alpine mutates the DOM on
every keystroke and every cart change, and a live Elements panel re-renders on each one.
→ Close DevTools, ring the same cart, and see whether it still lags. If it does,
`scratchpad/click-probe.js` names the offending handler in his own browser.

*Not a defect until it reproduces without DevTools — but not closed either.*

---

## 🚩 PROD IS HALF-DEPLOYED — SAFE, BUT UNFINISHED (2026-08-14)

**Nothing is broken. Nothing has changed for Felix.** The `git pull` landed on the box; the
deploy did not run — the command was typed as `deploy-prod.sh` instead of
`./scripts/deploy-prod.sh`, so the shell said *command not found*.

```
/root/banco-starter   git  999800d   ← today's code, ON DISK
banco-app             Up 6 days      ← still the OLD image, build 2f71b2e
```

So the till is serving ~2026-08-08 code and will keep doing so until someone runs the script.
That is a **safe** state, not a stuck one.

**To finish — and pick the moment, because it RESTARTS THE TILL:**

```
ssh banco
cd /root/banco-starter
./scripts/deploy-prod.sh          # note the ./scripts/ — that was the whole problem
```

⚠️ **Do it when the shop is closed or quiet.** It backs up to B2 first and aborts if that
fails, then rebuilds every container — the till is down for a minute or two. It also now runs
two new gates: the Keycloak public-URL preflight, and `standup.sh` (which installs the
append-only trigger — without it the 18+ evidence would be editable on prod).

**Afterwards, the sanity check:** the login screen's build stamp should read `999800d`, and
`./scripts/standup.sh` should print **SAFE TO TEST** including *"18+ evidence is append-only"*
and *"silent token refresh works"*.

---

## ▶️ NOW — needs Angel's hands

1. **⛔ The two bulk catalogue scripts are blocked on WHERE they run, not on code.**
   Local dev has **6 products**; the 5,111 live on the prod/UAT box, and `deploy-prod.sh` is
   written to run *on* that server. Decide: a shell on prod, or a dump pulled down here. Then
   `enrich-from-source.py --apply` (~90 min) and `adopt-images.py --apply` (~137 min).
   → detail in [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md)

2. **🔫 The gun's inventory-mode dump is still unproven** — the last unknown in shelf intake, and
   the whole 10× path. Does a 20–30 code burst survive a browser textarea? ⚠️ The gun roles are
   **the reverse** of what the old deck assumed: the Netum has store mode, the Inateck does single
   scans. Re-test before planning around either.

---

## ✅ THE 18+ EVIDENCE WORK IS DONE — HUMAN-GREEN 2026-08-13, Angel

**He ran it, and he called it: *"it's working fine."*** Closed. Do not reopen it for another pass.

Proven by his own hands, at the till, in German: **three real refusals made by a person and
recorded** — 16:10:10 *no ID*, 16:11:39 and 16:14:20 *clearly under 18*. That was impossible
two weeks ago and still impossible this morning.

**His decisions, taken as final:**
- **F2 · "Mitglied entfernen & weiter" stays as it is.** *"If the guy doesn't want the person's
  name on there or the member, then they delete it, and they remove it."* The button is the
  feature, not a hole. **Un-pin it** — the suite should stop printing it as a KNOWN GAP.
- **H6 · the receipt is fine as it is.** It carries the 🔞 18+ chip per line
  (`receipt.html:149`); it does not carry the basis, and it does not need to.

*What survived from the machine side:* `scripts/prove-till-18plus.js` — 44 checks, runs in
90 seconds, rings as `ralph` so its rows never masquerade as a person's. Keep running it before
a promote; it is not a reason to run another human pass.

⚠️ **My mistake to not repeat.** After he marked the sheet PASS and asked whether I agreed, I
came back with three more findings — two of which were my own mess (my test rows sitting in his
evidence, a step whose question his flow never reached). That is how a finished piece of work
starts feeling unfinished. **When the human says it works, it works.** Standing rule 5 cuts both
ways: a human confirming it is the finish line, not the start of another lap.

---

## 🔜 NEXT

3. **🔐 Go-live hardening** — DNS preflight + a default-secret gate in `deploy-prod.sh`; and the DR
   restore (Move B), still **blocked on read-only B2 credentials**. The backup has never been
   restored, so it is a belief, not a capability.

---

## 🧹 NEEDS TRIAGE — read before trusting

[`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) holds ~1,000
lines of catalogue, till and shelf-intake items written between 07-30 and 08-07. **Their status was
not re-verified when they were archived**, and at least one was already wrong:

> the shared cash box was filed as *"design agreed 2026-08-03, not built"* — it shipped in
> `fd035dd`, and the `cashier_id == user_id` filter it describes is gone from the code.

**So: check the code before acting on anything in there.** Promoting the still-live ones up to NOW
is a 20-minute job worth doing once, not a thing to re-derive every session.

---

## ⏲️ A decision the logs raised — how long may a till sit idle?

Angel's 15:46 logout was **correct**: 152 minutes idle against a 60-minute
`ssoSessionIdleTimeout`. Not the refresh bug returning — refresh verified 200 at the time
of writing. But it is worth deciding deliberately for the shop rather than inheriting it:
**60 minutes of a backgrounded tab and the cashier is logged out.** In the foreground the
till polls and the session stays warm; a tablet asleep over lunch does not. Overnight
logout is *desirable*; a quiet Tuesday afternoon one is not.

---

## 📌 Standing facts worth not re-learning

- **The app image bakes `src/` in — there is no bind mount.** `docker compose restart app` restarts
  the **old** code and says nothing. Any change under `src/` needs `./scripts/rebuild.sh`.
- **Prod authenticates against the DEMO realm** (`kc-pos-realm-dev`, users felix/pam/ralph),
  imported from a file **in a public GitHub repo**. Still the go-live blocker.
- **Banco is zero-perpetual.** `stock_quantity = 1` is the *design*, not missing data. Never set
  `min_stock` / `max_stock` / reorder points — `/reorder/suggestions` ranks by what the till sold.
- **`age_check_event` is append-only** (a PL/pgSQL trigger, not `REVOKE` — which is a no-op against
  a table owner). Nothing can tidy a row away, including a mis-tap.

---

## 🧪 How to prove it before claiming it

| what | command |
|---|---|
| stand up | `./scripts/rebuild.sh` → `./scripts/standup.sh` |
| server-side 18+ evidence | `BANCO_ALLOW_FAKE_SALES=1 python3 scripts/prove-age-evidence.py` |
| **the actual screens** | `BANCO_ALLOW_FAKE_SALES=1 NODE_PATH=/home/angel/repos/helixnet/node_modules node scripts/prove-till-18plus.js` |

⚠️ Both scripts **ring real completed sales** and refund them afterwards; a completed transaction is
a line in the Kassenbuch. `BANCO_ALLOW_FAKE_SALES=1` exists so it cannot happen by accident.
Playwright is **borrowed via `NODE_PATH`, not vendored** — this repo has no node build, on purpose.

---

## 📚 The archive

| file | what's in it |
|---|---|
| [`worklist-archive/2026-08-18plus-and-compliance.md`](worklist-archive/2026-08-18plus-and-compliance.md) | Gate Zero, and the whole 18+ evidence thread 08-10 → 08-13 |
| [`worklist-archive/catalogue-and-till.md`](worklist-archive/catalogue-and-till.md) | catalogue, shelf intake, till and search, through 08-07 — **status unverified** |
| [`worklist-archive/backlog.md`](worklist-archive/backlog.md) | not yet scheduled — offline kit, monitoring, labels, exports |
| [`worklist-archive/done.md`](worklist-archive/done.md) | shipped, most recent first, with commit hashes |
