# Archive — backlog (not yet scheduled)

*Moved out of `WORKLIST.md` on 2026-08-13. Nothing edited.*

---

### 💡 FIRST-USE AGE CHECK — Angel's idea, 2026-08-22, NOT BUILT

*"The first time the member tries to make a purchase, a popup appears… the cashier verifies their
age, maybe with a quick look, or if in doubt asks for ID… so all anon members have the age
checked but verified."*

**This is better than asking for a date of birth, and it should probably replace it.** No DOB is
stored at all — maximum anonymity, nothing under FADP to hold — and the check is a human looking
at a human, which is what the law actually wants. It gives a rung *above* `member_confirmed`
(a self-tick) that persists, instead of re-asking every visit.

Design notes before anyone builds it:
- **Record HOW.** "Looked over 25" and "checked their ID" are not the same evidence and must not
  share a value. Write it to `age_check_event` (append-only) with who and when.
- **A look does not self-correct.** A DOB makes a 17-year-old legal on their birthday; a staff
  glance marks them verified forever. Consider recording an ID check as permanent and a glance
  as needing a re-look after N months.
- **Hang it off the SCAN, never the spoken code** — see the 810,000 above.
- **A verified card in a younger sibling's hand is still verified.** That is the bearer-token
  limit of every loyalty card and worth stating out loud rather than discovering.

⬜ **AND THE T&C PAGE IS NOT WRITTEN — deliberately.** Angel sketched it (*"plain English, not
lawyer talk"*): skipping the DOB is fine, but you may be asked for ID the first time if you look
underage; doing this underage is illegal and we will probably catch you at the counter; this is a
**points system only**, tracking purchases and spend, maybe a gift at bronze/silver/platinum. He
also said *"I'm just making stuff up."* **The wording is his, not mine** — a page that tells a
customer what they are agreeing to should not be invented by the copilot. Draft copy needed, then
DE at minimum; FR/IT need a speaker, not a guess.


---



- **💳 CREDITS ARE EARNED AND CANNOT BE SPENT — waiting on Felix, not on code.** *(Angel,
  2026-08-27: "credits can't be spent yet — Felix has to decide how to use credits. But we offer a
  discount, and Felix is wishy-washy on what a member means, so it's kind of working fine as per
  design. Might have to drop.")* Every sale writes `credits_balance` + a `CreditTransactionModel`
  row; there is **no redemption path at checkout**. The kiosk invites people to collect points
  nothing can redeem — which the 08-24 worklist called the biggest open item. It is not a defect:
  the discount is the working member benefit and the points are a ledger nobody has defined a use
  for. **Do not build a redemption path until Felix says what a member IS.** If he never does, the
  honest move is to stop advertising points rather than to build a mechanism.


### 🌙 DARK MODE — wanted, spec'd, NOT scheduled

Angel put the tablet in dark mode and Banco is still all white screens. **The power argument does
not hold** — the X1 Tablet is an **IPS LCD**, where the backlight burns the same whatever colour
the pixels are; dark mode saves power only on OLED. On an LCD the lever is *brightness*. So this is
a comfort feature — a bright white till in a dim shop is tiring over a shift, and an app that
ignores the OS setting looks broken. Fine reason to build it, different reason.

**Do NOT do it with Tailwind `dark:` variants.** Four classes alone account for **503 occurrences**
across the POS templates (`text-gray-900` ×204, `bg-white` ×148, `bg-gray-50` ×94, `bg-gray-100`
×57), before the rest of the palette — well over a thousand edits, on a live till, forever after
remembered by every new template.

**Do it in one place.** `base.html` already carries real CSS for `.btn-primary`, `.input-field` and
`.card`, and Tailwind's Play build emits its utilities as ordinary CSS, so one block repaints
everything:

```css
@media (prefers-color-scheme: dark) {
  .bg-white { background-color: #1c1c1e !important; }
  .text-gray-900 { color: #e8e8ea !important; }
  .bg-gray-50, .bg-gray-100 { background-color: #232326 !important; }
  /* ~30 more lines */
}
```

~40 lines, one file, follows the OS, reverts by deletion. **The cost is not the CSS — it is the
verification.** A blanket override will strand light text on newly-dark badges, and **the price
display is not cosmetic**: a cashier reads it fast, under pressure, with a customer waiting. Needs
a human on every screen — till, cart, checkout, catalogue, scan, receiving — the same afternoon the
18+ and price-warning passes each took. **Pick it up with an afternoon and fresh eyes, not at the
end of a long day.**



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


- **🪣 B2 lifecycle rule on `wolfhold-banco-backups`.** *(left over from the 08-14 B2 detour, moved
  here 2026-08-27)* The storage cap is lifted (31 GB, no cap, ~13¢/month) so nothing is blocked, but
  229 dumps since 20 July sit under "keep all versions" and nothing ages out. Also worth a look at
  `wolfhold-freehold-backups` — 35 files, **30.7 GB**, which is what blew the cap, not Banco.


- **👤 `store_settings.owner_name` — stop hardcoding a person into the UI.** *(Angel, 2026-08-07:
  "leave it for now, we can do the owner_name thing later")* **34 user-facing strings name a person**
  across `my_day.html`, the closeout flow and all three languages in `src/static/pos/pos-i18n.js` —
  `"Sent to Felix"`, `"Ask Felix to add you in Staff…"`, `"e.g. box is locked in the safe and Felix
  has the key"`, `"p. ex. la caisse est au coffre et Felix a la clé"`. It is **deliberate**: the
  i18n header lists `Felix/Ralph` alongside TWINT and Gizeh as names preserved across translations.
  For Artemis it reads warmly and beats "your manager" — Pam knows who Felix is. For anyone cloning
  the starter it is a stranger's name in their till.
  **The fix:** add `owner_name` to `store_settings` (default `"your manager"`), render it through
  the `{placeholder}` machinery the i18n file already supports, sweep the 34. Artemis keeps "Felix",
  a fresh install reads sensibly. ~1 hour across three languages.
  **Already done:** the cashier first-price panel and toast say *"a manager to check"* / *"flagged
  for review"*, pinned by a test in `src/tests/test_cashier_first_price.py`. Code COMMENTS naming
  Felix are provenance and stay — this is only about text on a screen.

- **📦 THE OFFLINE KIT — a daily bundle that works with no Banco at all.** *(Angel, 2026-08-04. Full
  reasoning: [`onboarding/14-when-it-goes-down.md`](onboarding/14-when-it-goes-down.md))* A dated
  export on the back-office laptop: the whole catalogue with **barcodes, sale prices AND costs** as a
  real `.xlsx`, product images in a subfolder the sheet links to by **relative path**, and a simple
  order form. Outage: Felix opens the file, looks a product up, prices a basket, fills the form,
  prints it or saves a PDF to email. Nothing on that path needs a server or a network.
  **Most of it exists.** `src/services/catalog_workbook.py` already writes a genuine `.xlsx` with
  formulas, dropdowns and conditional formatting, and its design rules were chosen for exactly this —
  **formulas and validation, never macros**, so it opens in Excel, LibreOffice *and* Google Sheets.
  This is a **second export profile**, not a build.
  **Make the order form a VLOOKUP, not a blank page:** scan the barcode into a cell, the name and
  price appear from the catalogue tab. A working till in a spreadsheet, with the gun already owned,
  no code and no network. (`catalog_workbook.py`'s own docstring: *"the BARCODE — scanned straight
  into the cell, since a scanner gun is just a keyboard"*.)
  **⭐ This is the project's premise made testable.** `CLAUDE.md`: *"kill the 'what if the vendor
  vanishes?' fear with ownership, not a promise."* Not a licence clause — a file on his laptop that
  opens without us and would still open in twenty years. Angel: *"The day he says I've had enough,
  Angelo — I'm taking my CSV file and going onto a spreadsheet version of this whole thing."* **That
  has to be true or the premise is marketing.** An owner who *can* walk away with a working
  spreadsheet is an owner who chose to stay.
  **Requirements:** generated **daily and automatically** (`scripts/install-backup-cron.sh` sets the
  pattern — a bundle nobody refreshes is stale on the one day it matters); **relative** image paths,
  zipped with the sheet; **costs included**, since half the value of owning a catalogue is knowing the
  margin. **Proof: open the bundle on a machine with the network off and price a real basket.** A
  green export script proves nothing — same rule as the label printer.
  **🔻 NOT high priority (Angel, 2026-08-04).** Item 3 and the shop scan come first. Filed with the
  groundwork done so it starts fast whenever it starts.
  **Gap analysis — code read 2026-08-04, so tomorrow is not discovery.** What exists: the Migration
  Workbench export at `pos_router.py:6285` + `src/services/catalog_workbook.py`, already carrying
  SKU · name · brand · **barcode** · category · **price** · **cost** · size · source URL · notes, with
  formulas, dropdowns and a working import back (`parse_worklist_workbook`, `pos_router.py:6395`).
  **Four things block it being the offline kit:**
  1. **It exports only UNFINISHED rows** — `_bench_gap_clause()` at `pos_router.py:6301`. That is the
     point of a worklist; the kit needs everything. Needs an "all products" profile.
  2. **⚠️ It silently caps at 2,000** — `min(limit, 2000)`, `pos_router.py:6303`. The catalogue is
     **5,173**, so a "full" export today drops ~3,000 products **and looks complete**. Exactly the
     shape the no-silent-caps rule exists for. Fix or paginate before anything else.
  3. **No images** — there is a `Photo?` yes/no column, not a link. The subfolder + relative paths +
     zip is the genuinely new part.
  4. **On demand, not daily.** Copy the pattern in `scripts/install-backup-cron.sh`.
  **Performance trap:** `_reference_best_match` runs **per row** (`pos_router.py:6330`) — one query
  each. Fine for a few hundred worklist rows, ~5,173 queries on a full export, and it will likely time
  out. That lookup is an enrichment aid, not catalogue data — **skip it in the offline profile** and
  the export gets fast. *(Phase B · the "own it" premise · shop floor)*

- **Scan into a text file during an outage — test it, and fix the line format.** *(2026-08-04)* The
  gun is a keyboard; it works with no internet. A plain text editor on the tablet beats paper because
  `CATALOG-IDENTITY.md` makes the **barcode the identity**, and a hand-copied 13-digit EAN with one
  transposed digit is a worthless line. Two small jobs, both while it is calm: **(a)** scan a
  **hyphenated** test code into a text editor on the tablet and confirm it lands clean — digits sit in
  the same place on every layout and prove nothing; **(b)** agree the line format, `EAN, qty, price`,
  so re-entry is a paste rather than transcription work, which is what scanning was supposed to
  remove. *(shop floor · ~30 min)*

- **🏠 ❄️ PARKED — run Banco in the shop.** *(raised and then argued down 2026-08-04. Full reasoning:
  [`onboarding/14-when-it-goes-down.md`](onboarding/14-when-it-goes-down.md) — read that before
  reviving this.)*
  **Verdict: do not build it.** Angel's objection is the right one — *"Hetzner servers are extremely
  good, probably more reliable than some laptop."* On-prem does **not** buy reliability, it buys
  independence from the WAN, and the proposed box is a 2015 rubbish-find laptop against a data centre
  with redundant power, ECC and staff on site. Expect **more** downtime, just downtime you can walk
  over to. It also does nothing for the likeliest failure of all — a bad deploy or an app bug follows
  you on-prem — and barely helps in a power cut, when the card terminal and the lights are out
  anyway. The one case it uniquely fixes is *internet down, power up, for hours*, and four
  independent paths (two on separate mobile networks) already make that unlikely.
  **Revive only if** the shop's internet proves unreliable **measured, not feared**, or the shop
  grows past absorbing a lost hour. Kept below because the implementation notes are worth having if
  that day comes.
  ---
  Four network paths all reach the same box in a data centre, so a Hetzner outage, a bad
  deploy or an expired cert still stops every till at once. Offline-capable tills would fix it and
  cost a **rewrite** — Banco is server-rendered Jinja, so offline means turning the till screen into
  a client-side app with a service worker, a local database and a sync layer, on top of stock
  conflicts, catalogue drift, shift boundaries and cash-only-because-Worldline-needs-the-network.
  **On-prem dodges nearly all of it.** "The internet is down" becomes "the WAN is down"; the till
  talks to a local server over the LAN exactly as it does today. No offline mode, no sync, no
  conflict resolution, **no line of the till screen changes.** Weeks, not months. And it is what the
  project claims to be: *a self-hostable POS a shop owner stands up and owns outright.* A shop that
  cannot sell when a data centre sneezes does not own it yet.
  **The hardware already exists.** Angel's CHF 40 rubbish-find HP: ~2015, **8 GB RAM**, **250 GB SSD**
  (he fitted it). Enough for one shop — Keycloak's JVM is the hungry one and worth a heap cap.
  **A laptop is a better shop server than a desktop: the battery is a built-in UPS**, so a power
  blip does not take the shop down.
  **The fiddly parts are NOT the app — they are these:**
  - **HTTPS on a LAN.** Caddy's normal Let's Encrypt flow needs public reachability. On a private
    address you need **DNS-01**, Tailscale certs, or a local CA. Not optional: plain `http://192.168…`
    is **not a secure context**, so the phone's camera snap-fill and anything else needing one
    **breaks**. Get this wrong and it looks like the app regressed.
  - **Remote access for Angel.** Deploys, restores and debugging all currently go over `ssh` to a
    public IP. Tailscale or WireGuard replaces that cleanly; port-forwarding on the shop router does
    not (and per 2026-08-04, the router is not always ours to configure).
  - **It becomes the single point of failure.** Off-site backups stop being hygiene and start being
    the whole recovery plan — see the untested-restore item above, which this promotes from "should"
    to "must".
  - **Theft and fire.** A shop box can walk. Off-site B2 covers the data loss; disclosure is a
    separate question, and disk encryption on a headless box has the same no-keyboard-at-boot trap
    that made us refuse it on the tablet.
  - **Pick ONE source of truth.** Running prod and on-prem together is split-brain. On-prem primary
    plus off-site backup is the clean shape. *(Phase A/B · architecture · the "own it" premise)*

- **Nobody is watching prod. Felix is the monitoring.** *(2026-08-04, from the client-vs-server
  crash review)* `restart: unless-stopped` is on every service and there are real healthchecks on the
  app and Postgres, so an app crash or a host reboot self-heals. **None of that covers host death,
  disk failure, a Hetzner outage, a bad deploy or an expired cert** — and in every one of those cases
  the way we find out is a phone call from the shop.
  **Wanted:** an external check on `https://banco.wolfhold.app/health/healthz` with an SMS or push
  alert. Free tier is fine; a till does not need five-nines, it needs *someone to know*.
  ⚠️ **It must run OFF the box.** A monitor living on the same host tells you nothing at the exact
  moment it matters — the classic green-that-cannot-turn-red, same call already made about the
  Keycloak and MinIO healthchecks in `compose.yml`. Cheapest item on this list by a distance and the
  biggest return. *(Phase A · ops)*

- **The backup has never been restored, so it is a belief.** *(2026-08-04)* `backup-to-b2` and
  `restore-to-b2` exist and run. Nothing has ever come *back*. Standing rule 4 says "Fixed" is a
  claim until the output is verified, and a backup is the purest example: it looks identical whether
  it works or not, right up to the day you need it.
  **Wanted: a restore drill, written down.** Restore the latest B2 backup to a scratch container,
  then check three things a human recognises — **the product count matches prod**, **a known
  transaction is present with the right total**, and **a login actually works** (Keycloak realm data
  is the part most likely to be missed). **Record how long it took** — that number is the real
  recovery time, and today nobody knows it. *(Phase A · ops · money-correctness)*

- **A crashed tablet loses the cart, and the spare tablet cannot pick it up.** *(2026-08-04)* The
  in-progress cart lives in **`sessionStorage`** — `pos_cart`, `checkout_customer`, `pos_sale_uuid`
  (`checkout.html:761`, `scan.html:1775`). Completed sales are safe on the server and `pos_sale_uuid`
  already prevents a double-charge on retry. But `sessionStorage` is scoped to the browser tab: it
  survives a reload and the scan↔checkout hop, and **dies with a browser crash, a reboot or a flat
  battery.**
  **The bit that undercuts the two-tablet plan:** `sessionStorage` does not travel, so tablet B
  **cannot resume tablet A's cart**. The spare is a fresh start and a re-scan, not a handover — worth
  saying out loud before a cashier is told otherwise. `held_orders` is the manual park-it-safely tool
  that exists today.
  **Wanted:** the cart survives a crash — either auto-hold server-side, or move it to `localStorage`.
  ⚠️ **Not a find-and-replace:** `localStorage` is shared across tabs and never expires, so a naive
  swap trades a lost cart for a stale or bleeding one. Needs a decision, not a rename. *(shop floor ·
  Phase A)*

- **Paper-and-pen is the real last resort — and Banco has no way back from it.** *(Angel,
  2026-08-04, listing the failover stack: shop Wi-Fi → phone hotspot → two tablet SIMs on two
  different networks → paper and pen)* The connectivity side is now genuinely hard to break. The
  tail is what happens **after** the shop sells on paper for an hour: someone has to key those sales
  in, and today they land with **today's timestamp, in the current shift, under whoever is typing** —
  not when, where or by whom the money was actually taken.
  **That breaks the cash box.** The drawer holds cash the shift never recorded, so §5's tolerance
  check flags a discrepancy that is not one, and the shift report disagrees with the money in the
  box — the exact failure [`12-the-cash-box.md`](onboarding/12-the-cash-box.md) exists to prevent.
  **Wanted:** enter a sale after the fact — backdated, attributed to the right cashier and the right
  shift, and **marked as an offline sale** so the audit trail says why it arrived late. Needs a
  permission story (backdating is a money-editing power) and a decision on whether a closed shift can
  be reopened or the sale attaches some other way.
  **Note it is the same problem as offline selling.** If the till ever queues sales locally during an
  outage and syncs them later, it needs exactly this re-entry path. Solve it once.
  **⚖️ Scope it CHEAP first — Angel's read on the cost of getting it slightly wrong (2026-08-04):**
  *"It would be the wrong time, when the sale didn't happen — but it wouldn't really be that bad,
  because it doesn't ever happen."* So true backdating, shift reattribution, reopening a closed shift
  and a permission story for editing money are **not** justified by an event this rare. The cheap
  version probably is: key the sales in when the system is back and **use the cash box's existing
  named reasons and note field** to say why the drawer and the shift disagree. An explained
  discrepancy is not a discrepancy; an unexplained one costs somebody an evening. Build the cheap one,
  and only reach for the expensive one if it happens twice. *(Phase A · money-correctness · shop
  floor)*

- **The transactions PDF export stops after page one.** *(Angel, 2026-08-04)* Exported the
  transactions report both ways: **CSV came out perfect**, the **PDF produced only the first page**
  when it should have been two or three. So the data is right and the PDF renderer is truncating —
  pagination, not content. **Reproducible locally; no printer needed.** The bug is in generating the
  PDF, not in printing it, so "open the PDF and count the pages" is a complete test — Felix's
  Windows printer at the shop is a separate, later question about drivers and paper. Worth doing
  before any report is put in front of an accountant, because a report that silently drops pages is
  worse than one that fails. *(Phase A · reports)*

- **TARGET SALE PRICE — the cashier names the total, not the discount.** *(shop floor · Angel's
  idea 2026-08-03)* Felix **deliberately does not discount** — he holds the selling price and
  gives a **free treat** instead (papers for CHF 3 plus a lollipop, rather than CHF 2.95). That
  mechanism already exists and works: `line_item.is_treat`, and the Z-report prints
  *"Treats given (free) — 4 · cost CHF 0.45"*.
  But a cashier still needs a way to close the deal in front of her: *"62.99? ok just give me
  60 and it's a deal."* Today the only tool is a **percentage**, which is the wrong shape — she
  is not thinking "15% off", she is thinking "sixty francs".
  **Wanted:** type the TARGET TOTAL; Banco derives the discount and records it as one. Should
  also accept a price **above** catalogue (Angel: *"if she enters a new higher price for a
  catalog sale that would be possible too"*) — worth its own discussion, since that is a price
  override and needs a permission story.
  **Bonus: it dissolves the rounding edge case.** A target is a number a human types — 60, 55,
  12.50 — so it is payable by construction. Percentage discounts are the *only* thing producing
  unpayable totals like 62.99.


- **⚠️ 7 Blow "Pure" products carry the "Mix" description — and it contradicts itself.** e.g. `Blow vorgebauter CBD Joint Pure "Diesel"` (TAM-19238, real EAN 7640183261763) reads *"JOINTS NEXT GENERATION (without tobacco) ... a wonderfully balanced **mix between tobacco and cannabis**"* — both claims in one paragraph. The Pure copy was cloned from the Mix and only the header changed. **17 products share that sentence.** This is not cosmetic: tobacco content is a legal fact in Switzerland, and Pure vs Mix is also a CHF 9.90 vs CHF 6.90 price difference, so a customer reading the description gets the wrong product. The error is UPSTREAM (Artemis's own site) — Banco imported it faithfully — so fixing it here means either correcting the source or overriding locally, and that is a decision for Felix. Also note this now interacts with classification, which reads descriptions since 2026-07-30. *(shop floor · data quality)*


- **Retail tier prices aren't reaching the POS.** Banco fully supports quantity breaks — `products.price_tiers` is `[{min_qty, unit_price}]` with `tier_mode` per_unit/bundle, and `test_pricing_tiers.py` covers it. The gap is the DATA SOURCE: `supplier_search/tamar.py::_tiers()` scrapes Tamar's `<table class="BulkPrices">`, which is what Felix **pays** (wholesale). What the till needs is what the customer **pays** — the breaks on **artemisluzern.ch** (e.g. Gizeh Air Plus 200er `TAM-23153`: CHF 3.90 / 3.70 ab 10 / 3.50 ab 50). There is no handler for that site. **This is a consistency problem, not a feature request:** the shop's own website advertises a price the till won't honour, and a regular buying ten boxes of tubes will notice. Scope to consumables (papers, tubes, filters, tips, lighters) — the same set that already has breaks online, so the list picks itself. *(shop floor · customer-facing)*


- **Reports disagree on which timestamp defines a sale.** `/transactions` filters `created_at`, `/reports/product-sales` filters `completed_at`. For a cart opened at 23:58 and paid at 00:02 those land on different days, so the two pages can still disagree by one transaction even now the timezone is consistent. `completed_at` is probably right for revenue (that's when money moved) but it needs a decision, not a swap — and open carts have no `completed_at` at all. *(Phase A · money-correctness)*

- **Red leaf on the QR (two-colour printing).** The QL-820NWB is a genuine black/red printer and Angel bought it for that. Three things must line up and only one does today: ✅ hardware supports it · ❌ needs **DK-22251** black/red media (current DK-44205 is black-only) · ❌ the CUPS driverless path exposes `ColorModel: *Gray` only, no red. `brother_ql` does support red (`62red` label type) but is one of the three drivers that printed **zero** labels on this machine — so red via Linux means re-walking a proven dead end. **Easiest route: a Windows till**, where Brother's own driver handles two-colour natively. Worth knowing: a red leaf would NOT hurt scanning — cheap 1D laser guns can't see red ink at all, but both our guns are 2D imagers, and the leaf is a *hole* in the code either way, so error correction fills it regardless of colour. `make-leaf-mark.py --colour` already takes any colour, so the artwork side is free. *(shop floor · nice-to-have)*
- **More label sizes than Small/Medium.** Angel's idea after the leaf-QR sizing tests: the label screen has two buttons, but the scan test showed **18mm QR (variant D) reads just as cleanly as 20mm** — so a genuinely small sticker is available for small items where a 62×28mm label is overkill. Wants a few more buttons: e.g. Tiny (18mm QR, short), Small (20mm QR — current), Medium (shelf-talker, EAN-13). Pairs naturally with the labeller settings section, since the sizes should be shop-configurable rather than hardcoded in the template. *(shop floor)*
- **Label printer settings section (store settings).** Today the queue name `BancoLabel`, the roll width and the label sizes are hardcoded — in `print-label.py`, in `product_label.html`, and in the guide. On the shop ProBook the queue that actually worked was the auto-discovered *Brother QL-820NWB* one, NOT `BancoLabel`, which is exactly the assumption breaking. Wanted: a settings block for queue name, roll width, default size (small/medium), and named templates. Turns "Angel's laptop prints labels" into "any shop configures this". *(shop floor)*
- **`deploy-prod.sh` reports failure on a healthy prod deploy.** Its gate runs `postboot-check.py`, which probes `http://localhost:8000` — but in production the app sits behind Caddy and isn't published on host port 8000, so it prints `❌ NOT READY / the new code is NOT serving` while the site is perfectly fine (verified: `/health/healthz` 200, `/pos` 200, correct build stamp). A false alarm at exactly the moment someone is most anxious. Make the check use `APP_PUBLIC_HOST` over HTTPS when it's set. *(Phase A)*
- **Debounce the sale-screen product search.** `scan.html:85` fires `searchProducts()` on *every* keystroke with no debounce and no request sequencing, so a scanner burst (13 chars in milliseconds) launches ~13 overlapping searches and whichever lands last wins — including the `q=''` one, which the SQL short-circuits to "return everything" (`pos_router.py:2690`). That's why searching a full barcode in the **Search** tab showed all 24 products instead of one. Not urgent: the **Barcode** tab is the right field for a gun and works correctly. Fix is one attribute, matching the pattern already used at `scan.html:530`: `@input.debounce.300ms="searchProducts()"`. Also saves ~12 wasted API calls per typed word on a till. *(shop floor)*
- **Two search boxes side by side invite the wrong one.** On the sale screen the 🔍 Search tab (names) and 📊 Barcode tab (scanner) look alike; a barcode typed into Search silently misbehaves. Worth making the gun-shaped one the obvious default, or having Search notice it was handed 13 digits. *(UX)*
- **Put the label printer on the network.** It's a QL-820NW**B** — Ethernet/Wi-Fi on board. Not needed for Docker (containers already reach `ipp-usb` at `172.17.0.1:60000` — verified), but it removes the USB/`ipp-usb` layer entirely and lets any till on the shop LAN print. *(shop floor)*
- **Reframe the catalog workbook as THE bootstrap path.** `catalog_workbook.py` is the real "load your own catalog once" tool but guide 05 buries it under "Way 4 · ask for the import guide." Document it as the initialization step; make the import idempotent (upsert by barcode). *(Phase B)*
- Verify the firewall actually closed the raw ports (5432/8080/8000) — turn the instruction into a check. *(Phase A)*
- Assert Keycloak runs in production mode (`start`, not `start-dev`) in `compose.prod.yml`. *(Phase A)*
- Onboarding dry-run as a brand-new owner; close the gaps it exposes. *(Phase B)*
- Sharpen the AI setup coach for a non-technical owner. *(Phase B)*

