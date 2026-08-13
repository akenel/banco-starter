---
name: browser-tests-borrow-playwright
description: Banco's browser tests need Playwright, which is deliberately NOT vendored here — it is borrowed from a sibling repo via NODE_PATH.
type: reference
---

`scripts/prove-till-18plus.js` drives the real till screens (Playwright + headless Chromium).
Banco has **no node build on purpose** — Alpine.js is vendored, there is no `package.json`, and
adding `node_modules` would break that. So the test **borrows** Playwright:

```
BANCO_ALLOW_FAKE_SALES=1 \
NODE_PATH=/home/angel/repos/helixnet/node_modules \
node scripts/prove-till-18plus.js
```

If that sibling repo moves or is cleaned, point `NODE_PATH` at any `node_modules` containing
`playwright`; the script exits `2` with instructions rather than failing strangely. Browsers
themselves are already cached in `~/.cache/ms-playwright`.

**Why it matters:** this is the only thing in the repo that can see an `x-show`. The HTTP probe
(`scripts/prove-age-evidence.py`) was 25/25 green on a feature no cashier could reach — see
pattern 1 and 6 in `CLAUDE.md`, and the 2026-08-13 entries in `LESSONS.md`.

**How to apply:** extend that script rather than writing a second harness. The mechanics that cost
time to discover are commented in it: accept native `confirm()` dialogs (headless auto-dismisses
them, so every sale silently cancels and looks like a dead button), wait for Alpine before any
`evaluate()`, and the auth token lives at `sessionStorage['pos_token']`.

Related: [[banco-is-real-production]]
