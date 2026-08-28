# LESSONS — append-only

*Every one of these cost something. They live here rather than in `CLAUDE.md` because that
file loads every session and this list had grown to two-thirds of it. The **patterns** stay in
`CLAUDE.md`; the **evidence** is here. When something bites, add a line at the bottom — and if it
is a new instance of a pattern already listed in `CLAUDE.md`, bump the count there.*

---

When something bites you, write the lesson here in one line so it never bites twice.

- 2026-07-22 — Inline comments on `.env` value lines get parsed as the value; keep comments on their own line.
- 2026-07-28 — `lsusb` lists the Brother QL-820NWB **even when it's switched off** (USB chip runs on bus power). "Device is present" ≠ "device is on" — confirm the LCD is lit before debugging anything else.
- 2026-07-28 — CUPS queues auto-made by `cups-browsed` (`implicitclass://…`) are **temporary and disappear**. For anything a shop depends on, create a permanent queue with `lpadmin` pointed straight at the real device URI.
- 2026-07-28 — The QL-820NWB's **first job after waking takes ~25–30 s** (roll calibration); later jobs take ~4 s. A slow first label is not a stuck queue — don't cancel it early and go hunting for a bug that isn't there.
- 2026-07-28 — **`ipp-usb` goes stale after minutes and never recovers**: `0 bytes` on every request, blank web page, print jobs hang — while the printer sits there lit and `READY`. `sudo systemctl restart ipp-usb` fixes it *without touching the printer*, and that's also the diagnostic. A blanked LCD + blinking LED reads exactly like standby and sent me chasing the printer's Auto Power Off for an hour. **Suspect the daemon before the hardware.**
- 2026-07-28 — **"CUPS drained the job" is NOT "a label came out."** The printer accepts the data in ~3 s and only *then* rejects it, so a clean `lpstat` proves nothing. I called success on several jobs that printed nothing. For anything physical, the only proof is a human holding the thing.
- 2026-07-28 — When a device's behaviour makes no sense, **read its own status registers before touching settings**. The QL answers `ESC i S` over raw USB with media width, media type and error bits. One read ended hours of guessing between roll types — and proved the settings had been right all along. Hunt for the device's diagnostic channel early.
- 2026-07-28 — **`@page{ size: 62mm auto }` is INVALID CSS** — the spec allows `auto` OR one/two lengths, never a length plus `auto`. Browsers drop the declaration and silently fall back to **A4**, so a label renders in the corner of a sheet and the label printer discards it: no error, clean CUPS drain, green LED, nothing printed. **When a browser print does nothing, `Save as PDF` and run `pdfinfo` on it** — it shows what the browser actually decided, not what you assumed. That one command ended a three-hour hunt.
- 2026-07-28 — After changing print CSS, **hard-refresh (`Ctrl+Shift+R`) or use a private window**. Inline styles ride along with a cached page, so we kept testing a fix that was already deployed.
- 2026-07-28 — Three Brother-specific drivers (`printer-driver-ptouch` 1.6, `brother_ql` 0.9.4, `brother_ql_next` 0.12.0) printed **zero** labels on the QL-820NWBc — every raw-raster job rejected as "wrong roll type" — while the generic CUPS `everywhere`/IPP path worked. **The vendor-specific driver is not automatically the better bet.** Prefer the path with verified output over the one that looks more purpose-built.
- 2026-07-28 — `ipp-usb` redirects every request to `http://localhost:60000/` regardless of the address you use, so "use 127.0.0.1 instead" does *not* dodge an IPv6-first `localhost`. This box's `/etc/hosts` was also missing the standard `127.0.0.1 localhost` / `::1 localhost` lines entirely — worth checking with `getent ahosts localhost` when a local service hangs.

- 2026-07-30 — **A catalogue full of MINTED barcodes is a catalogue you cannot scan.** The July import created 5,111 products; Tamar publishes no EAN, so Banco fabricated `2xxx` codes for 5,103 of them. Every field was excellent (99% prices/images/categories) and the one fabricated column made the whole thing unusable at a till. **Never invent an identifier that exists in the physical world** — leave it blank and let the first scan bind it.
- 2026-08-02 — **A WRONG bind looks exactly like a right one — only a re-scan can tell them apart.** In the database both are a barcode pointing at a product: nothing missing, nothing erroring, no report flagging it. So after binding a section, walk back and re-scan the SAME products with the packets in hand. It caught Cannazym bound to Cannaboost (same brand, same bottle, adjacent barcodes, CHF 12 vs CHF 35) — which nothing in Banco could have found. It also surfaced eleven duplicate Tamar rows, one being the same grinder at two prices, as a side effect of checking properly. Verification against REALITY finds a class of error that verification against the database cannot.
- 2026-08-02 — **A barcode that resolves nowhere is usually an OUTER pack, or not shop stock.** GS1 assigns a code per packaging level and the multipack's is often registered nowhere public while the single's is everywhere: a 3-pack of OCB returned nothing, the singles inside (`30058569`) resolved instantly. **Open the pack and scan what's inside** before searching. And a code that finds nothing anywhere is often correct — it was a packet of batteries that wandered in. Skip is the button working, not failing.
- 2026-08-02 — **Batch size is set by the FAILURES, not the scanning.** A failed lookup hands you a number and nothing else — no name, no photo, no shelf position — so you cannot even tell which product it was. At a 90% hit rate: 30 scanned = 3 to re-find while you are still in that aisle; 300 scanned = 30, and a second trip. Scan one section, finish it, move on.
- 2026-07-31 — **When a match "isn't found", suspect the pipe, not the data.** Eight times in one day the right row was sitting in the database and something between the query and the screen discarded it: HTML entities left encoded (0.429 instead of 1.000), `pc.` vs `Stk.`, an absent size treated as a size, `KingSize` losing by exactly 0.000, tied scores nobody broke, a 400 KB fetch cap on a 1.4 MB page. **Every one failed silently and looked like "this source has no data".** Before concluding a source is useless, print what actually arrived.
- 2026-07-31 — **A sample you can check beats a sample that is merely large.** Offered a 200-product dry run, Angel asked for six he already knew the answers to — and that caught a scraper that spoke only German against `/en/` URLs. It would have reported "0 tier ladders found" across all 5,111 products with nothing looking wrong.
- 2026-07-31 — **A test that pins a known-dangerous behaviour is worse than no test.** `test_bundle_vs_per_unit_differ_on_same_data` asserted a 3× overcharge as correct, commented "exactly the bug Felix hit", and stayed green while the shop carried the risk. It made the danger look decided.
- 2026-07-31 — **A filter downstream of a fix can quietly undo it.** The DE↔EN folding really did take the Blow pair from 0.417 to 0.857 — and then the dedup guard's same-size rule threw the match away anyway, because `_product_size` knew `pcs` but not the singular `pc.`, so the English name yielded *no* size token while the German yielded `1stk`. Every unit test passed; the guard had been dead for that pair since the day the folding shipped. **Found only by calling the live endpoint with the exact pair it exists to catch and getting `[]` back.** Test the fix, then test the whole chain the fix runs in — and note that count units (`Stk.`/`pc.`) are language-specific too, just like the names.
- 2026-08-03 — **A filter must judge the string that MATCHED, not the row's headline.** The same "downstream filter undoes the fix" lesson from 07-31, biting a second time and worse. The merge now records the packet name as a searchable alias; the alias was written, the SQL scored it 1.000, and search returned `[]` — because `brands_conflict` and the same-size rule both compared the query against `products.name`. `"Purize Xtra Slim Charcoal Filters"` vs `"Aktivkohlefilter 6mm 50er Beutel"` is a brand conflict, so the row died one line after being found. **An alias that reads like a translation would have hidden this forever; the filters killed exactly the rows aliases exist to rescue.** The SQL had grouped by product and taken `MAX(sim)`, throwing away *which* name won. When you add a second thing to match on, check every filter downstream still knows which one it's judging.
- 2026-08-03 — **A PARTIAL copy of production doesn't look incomplete — it looks WRONG, and it accuses working code.** I loaded 200 real products into dev with the eight columns the enricher needed, leaving out `product_class` and `is_age_restricted` because the enricher never reads them. They defaulted to `standard` / not-gated. Angel then ran `reclass-age-gate.py` and got **24 products demanding an 18+ gate** — Parisienne tobacco tins, nicotine salts, CBD joints — and went to check UAT, where every one was classified fine. Twenty minutes of his time spent on a compliance scare I manufactured with a narrow `SELECT`. **When you copy rows for one tool, every other tool still reads them.** Copy the columns that make a row *true*, not the columns your task needs — or make the loader refuse.
- 2026-08-03 — **A remembered bug is a hypothesis, not a fact — re-measure before you fix it.** WORKLIST carried "spec parser loses fields on /en/ (Quöllfrisch 16 → 1)" for three days. It was backwards: 1 is the *correct* answer for that page, and the old 16 was one real spec plus fifteen rows of site footer. Fixing the note as written would have made the parser collect MORE junk. The real failure mode is the opposite one — running past the specs and inventing them.
- 2026-08-03 — **I cannot see a screen, so anything a person touches is verified by Angel or it is not verified at all.** The cash-box rebuild shipped with 35 unit tests, a 30-check live API proof and a verified prod deploy. Angel then spent 62 minutes on the tablet and found **seven** defects — *every one of them a screen*, not one reachable from the API. The worst two: the till screen would have **blocked the shop from opening** (the new 400/409 responses were dead ends with no note field), and a green **"✅ Balanced within tolerance" rendered over a box nobody had counted** — the precise lie §5 was written to prevent, in the largest element on the page, directly above the note explaining it was not true. **A green API is not a working product.** Budget for a human pass on every screen, and treat "machine-green" as the halfway mark, not the finish.
- 2026-08-03 — **When you remove a bad filter, grep for its twin before you claim it is fixed.** `_shift_sales` carried `cashier_id == user_id` and that one line was the whole shared-cash-box bug. I removed it, tested it, proved it live — and `shift_transactions` carried the *identical* filter twelve hundred lines away. The shift report totalled 2 transactions from both cashiers while the itemised log underneath listed 1. Angel spotted the mismatch on the report in minutes. **Standing rule 6 exists for exactly this and I still failed it**: the search costs one `grep`, and skipping it left a half-fixed feature that looked whole.
- 2026-08-03 — **A validation nobody can see is a silent failure.** A CHF 500 skim to the safe never existed: the cashier picked the movement, typed the amount, pressed Record — and a 400 for a blank free-text reason landed in an error banner at the **top of a page he had scrolled past**. Nothing saved, nothing looked wrong, and the report simply showed no paid-out. Two rules fall out: **put the outcome where the button is**, and **do not demand words a dropdown already said** — "to the safe" is a reason; requiring a sentence after it was pure friction, and friction is where money quietly goes missing.
- 2026-08-03 — **A setting that exists in the model, the migration and the API — and on no screen — is not a setting.** `cash_box_float` shipped complete on every layer a test can reach, so the §6 guard could only be configured with `curl`, which means never. Angel hit it as a hard FAIL two steps into the testsheet. Same shape as the force-close, which existed only as an endpoint until the one moment it was needed — and then had to be run by hand with `psql`. **If a human has to use it, it is not done until a human can reach it.**
- 2026-08-03 — **A script that recomputes what the server computes will accuse working code.** My live proof for the 5-rappen rounding derived the expected ticket itself: `0.50 × 95% = 0.475 → 0.48`. The server rounds the *discount* to the rappen and subtracts, giving `0.47`. Two ❌s, both mine, on code that was right. **Get the reference figure FROM the system, not from a second implementation of it** — here, ringing the identical cart on TWINT hands back the authoritative un-rounded total, and turns the check into the actual claim: same cart, two payment methods, differing by exactly the rounding.
- 2026-08-03 — **A client mirror is only as good as the test that runs it.** The checkout screen now rounds cash totals in JS to match `total_rounding.py`. This repo's most expensive bug shape is a mirror that silently drifts (the `pc.`/`Stk.` size table, dead for weeks with every unit test green). So the test *extracts the helpers out of `checkout.html` with a regex and executes them in `node`* over 2,000 totals against the Python. Then I broke the JS on purpose (nearest → floor) to confirm it fails. **A mirror test that never runs the mirror is decoration.**
- 2026-08-03 — **"It resolved" and "it is finished" are different claims, and reporting only the first CONGRATULATES you on the row you came back to fix.** Pam scans a new grinder, misses, types `grinder / 15.00`, sells it — all correct with a customer waiting, and the till binds the real EAN while doing it. Re-scan that packet and shelf intake said **"✅ already scans correctly"**, because the only question triage ever asked was *does this code resolve*. True, and the row was a one-word name with no category, cost, photo or description. The same day, the cockpit sorted that row **last** of 38 (busiest-first, and it had sold once) while `last_sold` sat computed, returned and printed on the card, never sorted on — and the bench card could fix category, price, cost, description, photo and 18+, but **not the name**, the only thing actually wrong with it. Three screens, three different ways of dropping the same row, **none of them an error**. When a screen reports a success, check it is answering the question the person asked.
- 2026-08-03 — **A probe found what my tests could not, because a test only asks what I thought to ask.** `?pid=<product>` was meant to mean "this exact row, whatever else is in the URL". I reset the gap clause and left the shelf scope standing, so `?pid=<grinder>&category=Grinders` returned **zero cards** — a dead end answering a scan just made. Twelve unit tests were green; the end-to-end probe caught it on the first run, because it exercised the messy real case (a stale filter in a URL) rather than the clean one. **And then the probe itself taught the same lesson twice**: it tore down by tracked id, crashed mid-run, and the next run died on the corpse of the last one. Anything that writes must sweep by prefix, not by what it remembers creating.
- 2026-08-03 — **A tool that only appears while the problem is invisible is not a tool.** `POST /catalog/merge` is built, tested and correct — and reachable from exactly one card: a shelf-intake row whose code is still **unknown**. Bind the EAN, which is the entire point of shelf intake, and the button vanishes. The catalog screen, the one place two identical rows are actually *seen*, has no merge at all. So Angel stood in front of `Canna Cannazym 1L` at CHF 43.90 and CHF 21.00 with the purpose-built fix sitting one HTTP call away and no way to press it. Same shape as `cash_box_float` (existed on every layer a test can reach, and on no screen) and the force-close (an endpoint until the night it was needed, then `psql`). **Ask where the person is STANDING when they need it, not whether the endpoint exists.**
- 2026-08-03 — **A 2× price gap on two rows with the same name is not a typo — it is the signature of two different products.** The instinct is to pick a price and merge. But one of those Cannazym rows carried no barcode at all, so nothing in the database could say what it physically was; the same brand and the same bottle already produced Cannazym-bound-to-Cannaboost at CHF 12 vs CHF 35. The disagreement is the *evidence*, and smoothing it over destroys it. Go and pick up both bottles first.
- 2026-07-30 — **"The data is good" and "the data is usable" are different claims.** Spent hours proving search worked while Angel kept saying it didn't. Both true: search ranked his product #1, but he wasn't searching — he was *scanning*, and a scan can't fall back to a name. Answer the job the person is doing, not the one you can measure.
- 2026-08-04 — **A password is only as portable as the KEYBOARD LAYOUT it was typed on** — and a login screen cannot tell you which one you got wrong. Angel set a deliberately simple password installing Debian on the X1 Tablet and could not log in minutes later; `y`/`z` swap between QWERTY and QWERTZ and every symbol moves, so the same keystrokes are a different string. Wrong layout and wrong password fail *identically*, which sent us to a 6-point GRUB console on a touchscreen — where the rescue shell has almost no `PATH` (`passwd` → *command not found*) and **also uses US layout regardless of the installed system**, so a fix typed perfectly there lands you back in GRUB. This is the scanner-gun layout trap wearing different clothes, and it cost a whole reinstall. **Any password typed before a desktop exists: lowercase letters and digits only, no `y`, no `z`, no symbols — and written on paper, not on the machine you are about to lock yourself out of.** The diagnostic when it happens: type the password into the *username* field, where it renders in the clear.
- 2026-08-04 — **A driver that failed is a fact about a VERSION, not about the hardware — re-measure before you rule it out.** The 07-28 lesson says three Brother-specific drivers printed **zero** labels on the QL-820NWB and to prefer the generic IPP path. True then, and I carried it into today as if it were permanent — warning Angel twice that Bluetooth was a dead end because it cannot carry IPP and forces the raster driver that failed. He wanted Bluetooth anyway (one USB port, and the scanner gun needs it), and **`printer-driver-ptouch` 1.7.1 printed the label first try** where 1.6 had rejected everything. The blocker had been fixed upstream in the months since. Same shape as the spec-parser note that was backwards for three days: **a remembered failure is a hypothesis with a timestamp on it.** Check the version number before repeating the verdict — and note the user's constraint was what forced the re-measure, not my judgement.
- 2026-08-05 — **An empty column is not always a gap — sometimes it is a DECISION, and the codebase says which.** `stock_quantity` is `1` on 5,099 of 5,163 rows and `min_stock`/`max_stock`/`lead_time_days` are populated on **zero**. I read that as unused machinery waiting to be switched on, worked out reorder points per category, and was about to paint red lines across the catalogue. Angel stopped me: *"we have a zero perpetual inventory system — did you forget that is the unique patentable thing we designed."* The repo had already said it in four places, including `reorder_item_model.py:4` — *"we never compute reorder from an on-hand count (**it's a lie**)"* — and `catalog.html:732` — *"**No min/max/reorder thresholds**: reorder guidance comes from sales velocity, not a count."* **And the replacement was already built**: `/reorder/suggestions` ranks by what the till actually sold. I had grepped the schema and the data but not the *doctrine*, so I found the columns and missed the sentence explaining why they are empty. **Before filling an empty field, grep for its name in the comments — a design that rejected something usually left a note saying so.**
- 2026-08-06 — **A SORT KEY ABOVE `score` IS A FILTER WEARING A BOOST'S CLOTHES.** The category hint shipped with a comment reading "⚠️ BOOST, NEVER FILTER" directly above `ORDER BY <category matches>, <name prefix>, score DESC` — score fourth. I wrote both. Photographed a **Greengo** grinder; the AI read `Greengo` + `Grinders` perfectly and the search returned ten generic grinders at 0.625, **not one a Greengo**, while the shop's six real `Greengo` rows sat at **1.000** and never appeared — they are filed under `Other`. Drop the category and they come back 1..6. Every same-shelf row, however bad, outranked every off-shelf row, however perfect, and `LIMIT` turned "ranked lower" into "does not exist". **A tier is a filter with extra steps; only an ADDITIVE bonus is a boost.** Third time this exact shape has bitten (07-31 dedup guard, 08-03 alias filters): a downstream rule quietly discarding the row the fix existed to find. And note what caught it — not a test, but running twelve real shelf photos through the live catalogue and *printing what came back*.
- 2026-08-06 — **THE SAME FILE HELD BOTH THE RULE AND ITS VIOLATION, 140 LINES APART.** `read_product_page` has refused to return a price since the day it shipped — *"a wrong price overcharges a customer"*, written in its own docstring. The `product` photo domain in the same module asked for `"price_estimate" a number in CHF if you can GUESS from the type`, and **four** screens auto-filled it the instant the field was blank: the TILL, new-product, goods-in, kiosk. Angel photographed three wooden grinders with a hand-written `10.-` sticker in frame; the model didn't need to guess, it could read it. The catalogue rows are CHF 39.00 and CHF 12.90. Nothing errored. **I wrote the testsheet step asserting this was already blocked, believing the docstring instead of reading the other path** — his FAIL was right and my expectation was wrong. When one path in a module enforces a safety rule, grep the module for the others *before* claiming the rule holds.
- 2026-08-06 — **`best_match_score` is computed, returned, documented — and rendered on NO screen.** The docstring promises "the UI can say 'found it' vs 'no strong match → search or create new'"; `grep` finds it in a JS comment and one assignment, never in markup. So six grinders at 0.5 look exactly like an exact 1.000 hit, and photographing an **SLX v2.5** — a real product genuinely absent from 5,379 rows — showed a list of confident-looking wrong grinders. Fourth time in this repo: `cash_box_float`, the force-close, `POST /catalog/merge`, now honest confidence. **Existing on every layer a test can reach is not shipping.**
- 2026-08-06 — **`reference_matches: 0` was an EMPTY TABLE, not a miss.** `reference_products` has **zero rows on prod**, so half of find-first has never worked there. I read `0` in four probes as "the reference doesn't have it" and moved on. Angel found the SLX grinder on fourtwenty.ch by hand in seconds — full specs, photo, the exact thing that table exists to hold. **A zero from a datasource is a claim about the datasource until you check it has any rows at all.**
- 2026-08-07 — **A GREEN TEST PROVES NOTHING UNTIL YOU BREAK THE THING IT WATCHES.** The till guard shipped with a test asserting both sale paths call `_guard_unverified_price`. It counted occurrences of `_guard_unverified_price(product` and required `>= 2` — but the **`def` line matches that pattern too**. I deleted a real call site from the legacy `/items` path and all 15 tests still passed. Caught only because I deliberately broke each guard one at a time; reading the test, it looks exactly right. The fix counts call sites with a regex that excludes the definition and asserts `== 2` with the two expected argument names. **Every guard I write now gets reverted on purpose before I claim it holds** — that step has caught something three times today (the category boost, the price mirror, this).
- 2026-08-06 — **A missing space costs the right answer, and German compounds have no spaces.** `Poker Chip Grinder` ranks `Grinder Metall 3teilig mit Sieb Poker Chip 42mm` **#1** at 0.611. `Pokerchip Grinder` — how a Swiss person actually types it — ranks it **out of the top 6** at 0.450, under a Hello Kitty grinder. The row survives the WHERE clause and then loses on score. Same family as the `pc.`/`Stk.` size table: a tokenisation difference silently discards the right row, with nothing erroring. Not yet fixed — decompounding is a real change, not a one-liner.
- 2026-08-13 — **I WROTE TWO TESTSHEETS ABOUT A SCREEN I HAD NEVER OPENED, AND ANGEL PAID FOR BOTH.** v1 told him to "decline the attestation"; that button is `🚫 Refuse — remove 18+ item(s)` and it is *client-side only*, so his 0-row result was correct and the test never ran. v2 told him to press `✅ Confirm 18+ walk-in` with a minor attached — **not rendered in that state**, said so in the template's own comment, and **his screenshot from the day before showed the two buttons that actually exist.** Half an hour of his time, twice, and the 08-03 lesson saying exactly this was loaded in my context both times. The failure mode is precise: **reading code and writing instructions about a screen.** For server work, reading the code IS the verification; the moment the work is a screen, it stops being verification and becomes a guess with citations. **The fix is not "be more careful" — it is `scripts/prove-till-18plus.js`.** Playwright, 27 checks, enumerating what the modal actually renders in each state. It found in 90 seconds what I had got wrong twice. **If a person touches it, open a browser or do not make the claim.**
- 2026-08-13 — **A PROBE THAT POSTS JSON CANNOT SEE AN `x-show`.** `prove-age-evidence.py` was 25/25 green on a feature no cashier could reach: `age_check_event` held 52 rows and **every one had been written by the probe itself.** No person had ever created a refusal record, and none could — `ageRefuse()` never called the server and `completeTransaction()` returned before the POST. The table recorded the exception (a server-side rejection, which almost never happens at a till) and missed the rule. **Green on the layer you can reach says nothing about the layer the user is standing on** — sixth instance in this repo, after `cash_box_float`, the force-close, `/catalog/merge`, honest confidence and `best_match_score`. Ask which door the person opens, then test *that* door.
- 2026-08-04 — **Reinstalling an empty machine beats debugging one.** The clever recovery existed and I walked Angel into it — GRUB, `init=/bin/bash`, remount rw — on a fresh tablet with nothing on it, tiny text, and no keyboard he trusted. He called it: wipe and start over. He was right, and I should have offered it first. **Weigh the fix against what the machine is actually worth**; a nothing-on-it box makes the twenty-minute certain path beat the five-minute clever one. The recovery path is still worth knowing — for a machine that has something on it.


- 2026-08-13 — **A HARNESS THAT FINISHES IN 90 SECONDS CANNOT SEE A 5-MINUTE TIMEOUT.** Angel pressed a refusal button mid-testsheet, was logged out, and the refusal was never recorded. I could not reproduce it: my browser suite ran green every time, because every run takes ~90 s with a freshly minted token. Keycloak's own log had the answer — `REFRESH_TOKEN_ERROR ... "Invalid token issuer. Expected 'http://keycloak:8080/realms/kc-pos-realm-dev'"`. The browser logs in at `localhost:8090` so its token says `iss=http://localhost:8090/...`; `/pos/refresh` presented that token to `http://keycloak:8080/...` from inside the network and Keycloak refused it. **So silent refresh had never worked in the sandbox, and every session hard-logged-out ~5 minutes after login** — while the refresh endpoint's own docstring promises *"the cashier is NEVER hard-logged-out mid-sale"*. `compose.prod.yml` pins `KC_HOSTNAME` and was always right, which is exactly why nobody caught it: **the broken environment was the one where we decide whether things work.** Fixed by pinning `KC_HOSTNAME_URL` in dev, and the readiness gate now logs in and refreshes for real, so it can never come back silently. **Ask what the harness is structurally blind to — time, idleness, a second tab, a real day — because no amount of running it again will surface any of them.**
- 2026-08-13 — **A COMPLIANCE RECORD THAT A LOGOUT CAN DELETE IS NOT A RECORD.** The refusal POSTed, the 401 made the API helper log the cashier out, the page navigated to Keycloak, and the toast explaining the loss went with it. The item still came off the sale — so the customer was correctly turned away and **nothing anywhere said the evidence had been lost**. The fix is not a louder toast: the till now parks the refusal in `localStorage` *before* it posts, and flushes it on the next successful login, with the row itself carrying `[recorded late — the till could not reach the server at HH:MM]`. `occurred_at` stays the server's clock, because a client that can backdate evidence is not evidence. **Write-ahead, then send: for anything that must not be lost, the local copy comes first and the network comes second.**

- 2026-08-13 — **I TURNED A FINISHED PIECE OF WORK BACK INTO AN UNFINISHED ONE.** Angel ran the human half of the 18+ sheet, marked it PASS, and asked *"it seems to work fine IMHO — do you agree?"*. The honest answer was **yes**: he had just made three real refusals at a real till, in German, and they were recorded — a thing that was impossible that same morning. Instead I came back with three more findings. **Two of them were mine**: my test suite was ringing as `pam`, so one of the rows he read back was the machine's, and a step (H6) whose question his own correct flow never reached. His reply: *"I don't know what you're looking for and what I need to test anymore."* That is the cost, and it is not a small one — it makes a person distrust work that is actually good. **Standing rule 5 cuts both ways.** "Human-green beats machine-green" means a human confirming it is the FINISH LINE, not permission to start another lap. When the person who owns the thing says it works: say yes, close it, write down what is left as a decision rather than a defect, and go and do the next item.

- 2026-08-14 — **"BELT AND BRACES" WAS THE BUG, AND I WROTE THOSE WORDS IN THE COMMENT ABOVE IT.** Deploying to Felix's shop crash-looped Keycloak: `ERROR: You can not set both 'hostname' and 'hostname-url' options`. `compose.prod.yml` is an OVERLAY on `compose.yml`; the base already set `KC_HOSTNAME_URL` and the overlay already set `KC_HOSTNAME`, and I added `KC_HOSTNAME_URL` to the overlay *as well*, calling it "pinned EXPLICITLY, belt and braces". Two correct-looking settings that are illegal together. **The app never went down — `banco.wolfhold.app` served 200 the whole time on the new build — only the login door died**, which is a failure mode worth knowing: the shop looks alive and nobody can get in. Worse, the preflight I had written that same morning *passed* the broken config, because it validated each value on its own and never the pair. **Defensive redundancy is not free: two settings that each look right can be forbidden together, and the guard must know that.** Fixed to keep `hostname-url` only (it carries the https scheme Caddy terminates), and the preflight now refuses when both are set — proven by restoring the exact broken file and watching it go red.

---

## 2026-08-21 — a day of prices, and four ways a number lies

**The shop floor found three of the four money bugs. None of my tests would have.**

**① A guard's second failure mode.** July's rescue — "a per-unit tier above the base price must
mean a pack total" — was written after a 3× OVERcharge and it has been earning its keep. Its
comment claimed both branches "can only ever move money toward the customer, which is the only
safe direction for a guess." Unbounded, that is not safety, it is the other loss: Gizeh Rolls
Slim Pink, base 2.90 with a 3.10 rung, re-read as "10 for 3.10" and rang **nineteen packs at
CHF 5.89**. A guess is worth making only while it stays plausible — bounded at half of base now.

**② The rule was never in the data.** "What does a customer pay for FOUR packs on a 3-for-10?"
is not answerable from the catalogue, the code or the feed. Angel asked **Ralph**, who serves
the counter: *"the pricing starts again — so 4 packs would be 14 total."* Banco charged 13.33.
Two tests had to be REVISED against that answer, and one of them was mine and wrong in a way no
amount of re-reading would have shown, because it was not bad arithmetic — it was the wrong rule.

**③ ×8 · Green on the layer you can reach.** `prove-cart-agrees-with-till.js` compared four tier
ladders and every one used `tier_mode: 'bundle'` — the single mode in which the rescue branch
cannot run. So the suite was structurally blind to it, and the cart showed **CHF 15.00** where
the drawer would take 5.00, on the screen a cashier reads aloud to a customer. Not an untested
line: an untested MODE. *Ask what your harness cannot see, not what it has not covered.*

**④ Changing a semantic leaves siblings behind.** Ralph's rule replaced bundle mode's pro-rata
maths — and the rescue path kept returning the old flat rate. Result: the same "3 for 5" rang
7.00 on one cart line and 6.67 on the next. Pattern 2 wearing new clothes: when you change what
something MEANS, every place that reads it has to be re-read.

**⑤ A prover that has never been dirty is not proved.** `prove-barcode-binding.js` hard-deleted
its fixtures for weeks. That only ever worked because nothing it created had sold. The moment
another prover rang real sales, the foreign key — the books protecting themselves — started
throwing. Also: fixed barcodes collided with their own soft-deleted leftovers, and
`performance.now()` restarts near the same value each run, so SKUs collided too and the suite
failed about one run in two. **Green often enough to be believed is the worst state a test has.**

**⑥ Absence and presence must look different.** Three screens showed a price and said nothing
about whether a deal existed — so a row with the right price and a MISSING deal looked identical
to a finished one, which is wrong at the till in the direction that costs money. Angel found it
three separate times, once per screen. And a wrong-MODE tier now reads `3+ @ 5.00 ea` instead of
`3 for 5.00`, because that mistake rings correctly at three and wrongly at four — it looks right
exactly when you test it.

**⑦ And the design was the shopkeeper's.** I was drafting a price-group table with membership to
maintain. Angel said: *"if the paper has tier pricing then they can mix."* The deal IS the group.
No table, nothing to configure, and a roll can never pool with a paper because 10.00 ≠ 5.00.

---

## 2026-08-22 — the day being *accurate* turned out not to be enough

Angel rang three plain King Size papers and the till said 6.00 where the deal is 5.00. One
checkbox — *"price is for the whole pack"* — had been left unticked on one of them.

**1. A true label that reads like a deal is a lie that passes review.** The mis-saved row printed
`3+ @ 5.00 ea` on the catalogue row, the shelf row and the bench card. That is *exactly* what
per_unit means. It also claims 15.00 for three while the till charges 5.00, and it sat on four
live products for a day with nobody blinking — because a ladder printed in indigo reads as a
deal however absurd the number. The fix was not a better sentence, it was to **stop pricing a
row we know is wrong** and say so in red instead.

**2. A row that is right alone and wrong in company cannot be found by testing it alone.** Three
of the slim pack on its own rings 5.00 correctly — the server's above-base rescue reads the rung
as a pack. It only breaks in a mixed basket. Every single-product test passes. *Ask what shape of
input your harness never constructs.*

**3. The app manufactured its own warning.** `addTier()` creates a `1 → <price>` rung the first
time anyone taps "+ Add break" on a per_unit product, by design (BL-31). My first rule flagged
that as dead weight — so the app would have scolded Angel for using its own button, and inside a
week he would have stopped reading warnings. **Narrowed it: an equal rung is silent, a
disagreeing one is red.** *Before shipping a warning, run it against what your own UI produces on
ordinary use.* Six of the twelve assertions in the prover now exist only to keep it quiet.

**4. Two real leaks were hiding in that same shape.** Tycoon Gas labelled 6.90, ringing **5.00**.
Greengo Wide Rolls labelled 4.00, ringing **3.50**. A `min_qty: 1` rung replaces the shelf price,
and one unit is not a deal. The sweep found both on its first run; neither was visible from the
row anyone happened to be editing.

**5. A silent all-clear is indistinguishable from a dead feature.** Angel fixed all eight flagged
rows, the panel correctly vanished, and we spent twenty minutes and a dozen tool calls proving
nothing was broken. I checked the route, the logs, the query, the i18n bundle — and along the way
told him prod was serving a stale asset, which was **wrong**: my grep had dropped `/pos/` from
the path so I fetched a 404 and read the empty result as a stale file. *An empty result needs a
"nothing here" that is distinguishable from "did not run" — in the UI and in your own probes.*

**6. A save you have to go looking for is a save that does not happen.** Angel filled the New
Product form twice, told me he had saved, and **no POST ever reached the server**. The Create
button sat at y=1618 in an 1100px window — 500px below the fold, behind the bottom nav. My own
warning box made the reach ~90px worse. He was not doing it wrong; the button was not there. Now
sticky. *When someone says they did it and the system says they didn't, measure the geometry
before doubting the person.*

**7. My own repro accused working code — twice in one hour.** First a `.btn-success` selector that
grabbed a hidden "Yes — merge them" button and reported the Save button unreachable. Then a
`.replace()` on a 4-space-indented anchor against a 6-space line, which silently did nothing and
left a seed row uncreated. *A string replacement without an assert is a no-op waiting to be
believed.* Both were caught only because the failure looked implausible.

**8. An assertion that cannot fail is worse than no assertion.** I shipped `ok('an EAN-less row
says "no barcode yet"', nones >= 0)` — true of every number. A green tick that means nothing is
worse than a missing one, because it is counted.

**Angel ran the 25-check sheet on prod: `25 pass · 0 fail`.** The live shop now carries 92
quantity ladders and zero that cannot mean what they say.

---

## 2026-08-22, later — the till learned to explain itself, and two lies fell out

The build was *"the cart says WHY a line costs what it costs"*. Angel ran it, 17/17 GO. Then a
focused retest, 9 of 10 (the tenth he wrote *"looks fine, no confusion"* and did not tick).
Sixteen commits. What is worth keeping is not the feature.

**1. An honest label makes an old lie visible.** `pack ✓` had been printing on lines charged in
full for weeks and nobody saw it, because a green tick beside a number is not a claim anyone
reads. It only became obvious the moment `3 for CHF 5.00 — not reached yet` sat directly under it
and the two disagreed on the same line. *Adding a true statement next to a false one is a
debugging technique.*

**2. A group that saved nothing is not a deal.** Two King Size papers pool — same terms, same base
— but two is below the three-rung, so the pooled price IS the flat price. Both mirrors still
reported the group. On screen that was a wrong badge. On the server it set `tier_final`, which
takes a line out of `eligible_subtotal`, so **a manager's goodwill discount silently skipped two
full-price papers**. A flag whose name is a claim (*"a volume break set this price"*) must be set
by the claim being true, not by the code path that usually implies it.

**3. Three copies of a rule, and the third had drifted.** The server discounts only the eligible
portion — tobacco and alcohol never take a promotion, a volume-break line is discount-final.
`checkout.html` mirrored it, with a comment saying so. The till's own cart panel had no concept of
eligibility at all and applied the percentage to everything: **CHF 8.91 in the cart, CHF 9.41 at
checkout and in the drawer.** The cart is the screen the cashier quotes from. The server's comment
read *"the EXACT formula the till displays, so charged == shown"* — a comment asserting a property
nothing checked.

**4. The harness could not build the failing shape.** `prove-cart-agrees-with-till` ran green all
day across 320 quantities and 9 mixed baskets while this was live, because it compares line totals
and **never constructs a discounted basket**. That is not thin coverage, it is a shape the test
cannot make. Same family as the five-minute-timeout lesson, and the second time this year.

**5. A screen dump beats a tick — twice in one afternoon.** Angel pasted the literal cart text into
his UAT notes instead of just marking PASS. Both bugs above came out of those pastes; neither came
out of a test, and he had marked both steps PASS. *The evidence a tester leaves behind is worth
more than their verdict.* This is now written into the test-sheet template: a notes box on every
step, not only on failures.

**6. The format was already there.** Asked for "a robust testsheet format for our UAT system", I
built one — and then found thirteen sheets in `onboarding/testsheets/` that had already converged
on PASS/ISSUE/FAIL with persistence, 13/13, without anyone writing it down. What was actually
missing was a *template*: every sheet had been hand-built, which is why four had lost the copy
button and three the clock. *Before designing the house style, check whether the house already has
one.*

## 2026-08-22, evening — the LTE modem, and three status fields that were all telling the truth about the wrong thing

Felix wants the shop tablets to keep selling when the Wi-Fi dies, and handed over an X1 Tablet
Gen 2 with a nano-SIM in it. It took an afternoon. The fix was **one symlink**, and the cause was
named in plain English by the machine itself the moment debug logging went on.

**1. Every error message described a symptom one layer below the cause.** `nmcli` said the gsm
device was `unavailable`. `mmcli` said `state: failed / sim-missing`. `mmcli -m any -e` said
`Core.Retry: Invalid transition`. All three were accurate and all three were downstream of the same
thing: the modem ships **FCC-locked** and refuses `RadioState=on` until the host sends a vendor
unlock. ModemManager knows how, but since 1.18.4 the unlock scripts ship *disabled* and Debian
enables none — so MM tried, found no script, and reported a generic failure. One `-G DEBUG` run
printed `attempting FCC unlock... file doesn't exist` and the afternoon was over.
*Turn on the device's own log before proposing a fourth hypothesis.*

**2. A status field read at the wrong moment is a confident false negative.** *(And I did it twice
in one day — see the postscript.)* `sim-missing` was
reported while the WWAN radio was still soft-blocked — a powered-down modem has never energised the
slot, so it *cannot* report anything else. I read it as evidence about the card, and Angel pulled
and re-seated a SIM twice on my say-so. It was never about the card. *Before believing a reading,
ask whether the thing being measured was switched on.* Same family as the five-minute-timeout
lesson: the harness — here, the query — was structurally incapable of the answer I wanted.

**3. I agreed with a paste that contradicted itself, nearly.** Angel wrote *"i think SIM is ok now
… it sees it"* over a paste that still read `sim-missing` — it was old scrollback, wrong copy. Had
I taken the human verdict at face value we would have moved on to APNs with a dead modem. Standing
rule 5 says a human confirming it is done; it does **not** say agree with a claim the pasted
evidence refutes. The later *"i turned off wifi and i can still run banco on the web"* is the real
thing, and that one is done.

**4. The device name moved and would have broken it silently.** `cdc-wdm0` came back as `cdc-wdm2`
after a reboot. A NetworkManager profile pinned to `ifname cdc-wdm0` would have worked all through
testing and failed on some future boot — i.e. during the outage it exists to survive. `ifname '*'`.
*An identifier that survived every test you ran is not thereby stable.*

**5. And the thing that is still not proved.** Everything after the manual
`qmicli --dms-set-fcc-authentication` ran on that authorisation, which persists until the modem
loses power — `systemctl restart` does not power-cycle it. So `registered / on / attached` says
nothing about whether the symlink works. **Only a cold boot tests it.** Beyond that, the whole
build was proved at Angel's flat on `Init7_1A34`, not in Luzern: different SSID (so the Wi-Fi route
metric is unset there), different concrete, different coverage. Home signal was 29 %.
*Where the person is standing includes which building.*

## 2026-08-22, later still — the camera dead end that was the wrong dead end

Doc 13 had carried a verdict since 2026-08-05: *"the kernel sees the imaging unit on the PCI bus and
nothing attached to the other end… do not re-run this hunt."* Angel asked for the camera. Re-running
it took twenty minutes and the verdict was wrong.

**1. Absence in a log is not absence in the hardware.** The August conclusion came from
`dmesg | grep int3472` returning nothing. That is what an empty socket looks like — and *equally*
what a machine whose glue modules never loaded looks like. Nobody asked ACPI. On kernel `6.12.101`
the ACPI namespace declares **two fitted, enabled sensors** (OV2740 `INT3474:01`, OV5670
`INT3477:00`, both `status=15`) and the kernel prints *"Found supported sensor… Connected 1
cameras"*. The hardware was there the whole time. *When concluding a thing does not exist, query the
registry that would know, not the log of a process that may never have run.*

**2. The note saved itself by dating itself.** That same block said *"a measurement with a timestamp,
not a permanent verdict — re-check after a major kernel jump."* That sentence is the only reason it
got re-opened instead of believed. **Write the expiry condition into the verdict.** The rewritten
section now names a *ten-second* re-check — `sudo dmesg | grep -i tps68470` — instead of "re-run the
hunt", so the next person spends seconds, not an afternoon.

**3. The new dead end is real, and it is better than the old one.** Both fitted sensors are powered
by one PMIC (`INT3472:05`, TPS68470) which fails with *"No board-data found for this model"*; no
other power provider is present. Board data is a DMI-matched table compiled into the kernel and this
model is not in it. So: sensors never get power → no I²C client → no sensor entity in the media
graph → `cam -l` empty. **Same answer as August — buy the USB webcam — arrived at for a reason that
is checkable, specific, and names what would have to change.** A correct conclusion resting on a
wrong premise is a bug that has not gone off yet.

**4. Two afternoons, same shape, opposite directions.** The LTE modem looked broken and was one
symlink from working. The camera looked settled and was two sensors nobody had found. *Both remembered
verdicts were hypotheses with timestamps; both needed re-measuring; neither survived it.*

## 2026-08-22, end of day — the camera worked and the button was hidden

Angel found a USB webcam, plugged it into the tablet: *"i just plugged it in and it just works."*
It did — in GNOME. In Banco, ✨ Snap & fill opened a **file picker** and the 📷 Webcam button was
not on the screen at all. His verdict: *"kinda stupid for snap and fill for a new product."* Right,
and precisely so: that button is the **no-barcode** path, so a file picker is a dead end by
definition — the item is unmarked, that is why you are photographing it.

**The cause was a category error in one predicate.** `posIsTouchDevice()` split the world into
phone-or-laptop on `maxTouchPoints`. A Linux tablet is *both*: a touchscreen **and** a desktop
browser that ignores the file input's `capture` attribute. So it received the phone branch's
attribute, which does nothing there, and the phone branch's hidden button. Neither path — on the
only machine in the shop with a working camera. **A touchscreen is not a phone.** The axis that
matters is the OS, because only a phone has a native camera app worth handing off to.

**What makes this pattern 1 and not just a bug:** every layer I could reach was green. The webcam
enumerated, `uvcvideo` bound, GNOME showed a picture, `PosCameraPhoto.capture()` was correct code
that had presumably worked on a laptop. The failure existed **only on the screen Angel was standing
in front of**, and only because of a boolean decided three files away. Reading `pos-scanner.js` on
its own would never have found it; it took a person tapping the button and getting a file dialog.

**And the fix needed a deploy to be true.** Committing it changed nothing for Angel — the tablet
talks to `banco.wolfhold.app`, which runs deployed code. "Fixed" meant *fixed in a repo*, which is
not a place anybody stands. It became real at `4206246` on prod, after a hard-reload past a cached
`pos-scanner.js`. *Ask not only which screen, but which copy of the code that screen is loading.*

Human-green, Angel on the tablet: **"the webcam button is there and it works."**

## 2026-08-22, night — the model was not guessing, the camera was starving it

Angel snapped a grinder that **was already in the catalogue** and snap-find missed it. His read:
*"it never finds a match in the catalog but the google search basically finds it fine."* He was
about to work around it by screenshotting Google Images.

**The matcher was innocent, and the way to know that was to ask prod, not to reason.** Running the
real ranking query against the live row (`Grinder Champ High White Leaf - 4-teiliger Ø50mm`) for
five plausible reads:

| what the AI reads | rank | score |
|---|---|---|
| `Champ High White Leaf Grinder` | 1 | 1.000 |
| `White Leaf Grinder` | 1 | 1.000 |
| `Grinder` | 1 | 1.000 |
| `Metal Herb Grinder 4-part 50mm` | **16** | 0.452 |

Even the bare word "Grinder" ranks it first. The only read that buries it is the **unbranded but
specific** one — and the picker shows 6. *Invented specifics do not just fail to help, they
actively displace the right row.* The function's own comment already said the model "answered 50mm
for nearly everything"; what was new is that this is enough to lose a perfect match.

**So why did the model describe instead of read?** `getUserMedia` was asked for a camera with no
size constraint, so it returned the browser default — commonly 640×480. Brand lettering on a tin is
mush at that size. And `image_intake` only ever DOWNSCALES (PRODUCT caps at 1024px): **no server-side
step can recover detail the capture never took.** Asked for 1920×1080 ideal, plus Angel framing the
lettering rather than the object, the same grinder came back rank 1. Human-green: *"perfect hit."*

**Three things worth keeping:**

1. **A quality complaint about a model is a claim about its input, until you have measured the
   input.** Nothing anywhere recorded what reached the vision service — a 640×480 webcam frame and
   a 12MP phone shot both arrive as "a JPEG". That is now logged (`vision intake: product WxH kB`).
   The debugging was blind for exactly as long as the measurement was missing.
2. **Ask the system for the ranking instead of theorising about it.** One SQL run against prod
   turned "the matcher is bad" into a table showing it is perfect for four reads out of five, and
   named the fifth. Same discipline as LESSONS #5, used the right way round.
3. **The workaround would have hidden the bug.** Screenshotting Google Images produces a sharp
   picture, so it would have "worked" — and left every future snap at 640×480, plus a catalogue
   of other people's photographs. `/catalog/page-facts` already existed for this and returns the
   **EAN**, which a screenshot never can. *When a user invents a workaround, find what it is
   compensating for before praising it.*


### Postscript to 2026-08-22 — I made lesson #2 again, six hours later

Angel's tablet took four hours to charge. I had him read `power_now`, got **8.45 W**, computed
`37.01 Wh ÷ 8.45 W = 4.4 h`, matched it against the observed time, declared the adapter undersized
and told him to buy a 45 W one. The arithmetic was clean and the conclusion was wrong.

**The reading was taken at 77 % and climbing.** Lithium cells charge hard to ~80 % and then taper
into constant-voltage, so 8.45 W describes the final stretch and nothing else. Extrapolating it
across a full charge is the same error as reading `sim-missing` off a modem whose radio was
switched off: *the instrument was fine, the moment was wrong.* And the matching number made it
worse — a coincidence that agrees with your theory feels like confirmation.

Angel caught it by checking the adapter: **65 W**, already above the 45 W this machine ships with.
*"is that true?"* — one question, and the whole finding fell over.

**What generalises:** a single instantaneous sample of anything with a duty cycle, a taper, a warm-up
or a sleep state is not a rate. Before extrapolating one reading across a process, ask **where in
the process it was taken** — and prefer two samples at different points over one that happens to fit.


## 2026-08-24 — the catalog could not leave the building, and its own filter disagreed with the screen

Angel asked a one-line question: *"does banco have a button to download the existing catalog with
EAN and all the info to a CSV?"* The honest answer was **no**. Banco had three CSV exports — the
Banana daily summary, the transactions list, the product-sales report — and every one of them is a
report *about* selling. The only export that touched the catalog was the BL-131 worklist, which is
deliberately the opposite of what he asked for: `_bench_gap_clause()` filters it to the rows that
are still **unfinished**, capped at 2,000. Ask for "my catalog", get "the 500 rows still missing a
photo". The nearest raw route was `GET /products` at `limit=100` — 54 paged calls and a script.

That is a strange hole for a repo whose whole thesis is *"you can't clone SAP, you can clone this."*
**A shop that cannot get its own product list out of the box does not own it.** Everything else — the
compose file, the restore runbook, the go-live path — argues for ownership, and the one screen where
an owner would reach for their data had no door. Worth noticing how it happened: every export that
did exist was built for something a person asked for on a specific day (Felix's bookkeeping, Felix's
receipts). Nobody asks for the exit until they want to use it.

**Then the new endpoint made lesson #2 on its way out.**

`?category=` filtered with `lower(category) = lower(:category)`. Exact, obvious, and it passed every
check I wrote — because every check compared the export against *my own expectations of the export*.
The catalog screen it sits on filters with `category ILIKE '%' || :category || '%'`. The two only
diverge when one category name **contains** another, which this catalogue is full of ("Bongs" inside
"Pipes & Bongs"): the operator picks a shelf, sees both on screen, and downloads one. A file that
silently disagrees with the list you were staring at — and nothing in it looks wrong.

The only thing that could catch it was asking **both** endpoints the same question and diffing the
answers. `scripts/prove-catalog-export.py` now does exactly that: it pages `/search` to the end and
compares SKU sets against the export, for a full category name *and for a fragment of one*. The
fragment is the case that matters; it is the one that fails when a `=` quietly replaces an `ILIKE`.

**What generalises:** *a filter is only correct relative to the filter the user thinks they are
using.* When you add a second way to ask the same question, do not test it against your own
expectations — test it against the first way, with an input chosen so a wrong predicate must differ.
Self-consistent tests on a duplicated concept are the most confident kind of green there is.

**A footnote on my own harness, which is lesson #1 wearing a lab coat.** The browser proof failed on
its first run: `isVisible()` on a button whose `x-show="user.isManager"` depends on an async fetch.
The button was fine; the *check* raced. I nearly went looking for a bug in working code. The fix is
not a longer sleep — it is waiting on the real signal (`waitFor({state:'visible'})`), and, for the
cashier case, waiting for **the cashier's own banner** before asserting the button is absent.
Otherwise "the button is hidden" is true of a blank page, and passes for the worst possible reason.


## 2026-08-24, afternoon — three bugs, one shape: the server was right and the stored copy was wrong

A UAT on the live shop found four things. Three of them are the same bug wearing different clothes,
and I did not see it until the third one.

**The kiosk refused a blank username.** `submitSignup()` tested the handle against a 3–30 pattern
with no blank check. The server assigned `ART-AB12` on a blank handle, the schema had been changed
from `str` to `Optional[str]` for exactly this, and eight unit tests covered it. All green. The
comment sitting directly above the input read *"EVERY FIELD HERE IS OPTIONAL, AND THE FIRST ONE
USED TO BE COMPULSORY"* — true of the markup, false of the code seven hundred lines below it.

**Deactivated members would not go away.** `/customers/new-today` asked for everyone created today
and never asked whether they were still active. Angel's words were *"something is still cached"* —
and that is the interesting part. It read as caching **because every other screen already filtered
them**: the members list, the search, the till's card scan. When one screen out of four is wrong,
it does not look wrong. It looks stale.

**Clear cart did not clear the cart.** `confirmClearCart()` emptied `this.cart` and dropped the
idempotency key but never `pos_cart` — and the scan page restores the cart from `pos_cart` on every
load. So clearing worked on screen, the stale copy stayed in session storage, and the next
navigation resurrected it. Angel cleared twice; it could never have helped, because clearing had
never once touched the thing it was being restored from. Unchanged since the first commit — it needs
a trip to Checkout first, so a year of ordinary selling never produced the sequence.

**The shape.** In all three, the server was correct, the in-memory state was correct, the tests were
green, and **a stored copy on the layer the customer stands on was wrong**. Not a logic error —
a *synchronisation* error between a truth and its cached shadow. And the shadow always wins, because
the shadow is what renders.

**What generalises: state that is written in one place and read in another needs an owner, and every
mutation has to name every copy.** A clear that clears one of three keys is not a clear. Ask, of any
"reset", "clear" or "cancel": *what did this write, and does this delete all of it?*

**The half nobody reported, which is the real lesson about scope.** Fixing the cart, I checked what
else a sale leaves in session storage. `checkout_customer` — the member AND their age answer — was
also never dropped. So "start fresh" kept the last customer's card attached to the NEXT person's
sale: their discount, and their `is_of_age`, applied to somebody the cashier never looked at. That
is precisely the hole closed on 22 August, walking back in through a different door, and **it was
found by asking what else lives beside the thing that broke** rather than by fixing what was
reported. Standing rule 6, paying for itself in one line.

**And a caution against the same instinct.** Rule 6 also had me announce, mid-investigation, that
the till's member scan was unguarded — I had read the two `select(CustomerModel)` lines and not the
six below them, where an explicit `if not customer.is_active` returns *"Customer account is
inactive"*. There was never a hole. *Check the siblings, yes. Finish reading before you report one.*

---

## 2026-08-27 — four mechanical bugs wearing a hard problem's clothes

*Written at the shop, mid-trade, with Layla serving and Felix in and out. Everything below was
measured on the live box, not remembered.*

**The morning's real job was the cash box**, which had sat open since 7 August — sixteen days,
opened by pam, float CHF 200, six sales rung into it. Felix had counted the physical money: CHF
1216.90. My first instinct was the force-close, the manager-gated §5 escape hatch. **Wrong tool.**
Force-close is for a box that *cannot* be counted; this one was counted and sitting on the table.
The right move was the ordinary reconcile, which records `counted_verified = TRUE` and leaves no
asterisk on the books forever. *An escape hatch is not a shortcut, and reaching for it when the
normal path is open buys a permanent footnote for nothing.*

I also got the expected figure wrong on the way in — told Angel CHF 111.10 of cash sales when the
screen said 137.00, because I filtered `created_at >= '2026-08-07 19:46:09'` using a timestamp I
had myself rendered `AT TIME ZONE 'Europe/Zurich'` against a column stored in UTC. Two hours late,
two sales missed. **Lesson #5 exactly: get the reference figure FROM the system.** The screen was
right the whole time and I nearly talked him out of trusting it.

### The four bugs, and what each one actually was

Three Crank pipes were quick-added at the counter. All three printed a label. **None could be rung
up**, and working out why took Angel half an hour with three browser windows open.

1. **The small sticker printed a QR the till could not resolve.** The label route builds the code
   as `barcode or sku`, so a product with no manufacturer EAN gets a QR of its SKU — and
   `_find_product_by_any_barcode` had never once looked at the SKU. **The gun read it perfectly and
   the till said "not found".** A sticker that looks finished and dies at the counter is worse than
   printing nothing, because nothing at least tells the truth.
2. **The medium label printed `— no barcode —`** and nothing else, correctly, for the same reason.
3. **The gun sends SHIFT a beat late.** `SKU-1787825927800` arrives as `sKU-1787825927800` — first
   letter lowercase, the rest fine. **I had proved my own fix by TYPING the SKU**, which is the one
   way it would never be entered. Green on the layer I could reach, dead on the counter, an hour
   after I wrote that sentence about somebody else. Angel found it in one scan.
4. **The page title is the PDF filename.** Both label sizes shared one, so saving a medium
   destroyed the small. And two active products are named byte-identically
   (*JaJa Noir King Size XXL*), which would have collided invisibly.

And the small label had been **silently clipping** the code all along: `SKU-17878259278` printed for
`SKU-1787825927800`. Two characters gone. The fallback a human reads *when the scan fails* was
itself wrong. My first fix shrank the font and it still clipped — **guessing a size that "should
fit" is how the first attempt failed, so the second stopped guessing and let it wrap.**

### The one that was not about labels at all

Five JUICY Super Wraps, same product, five flavours. Two scanned. Three found nothing, and nothing
on the internet either. Angel's read at the counter: *"these are all the same and we need the bar
codes… doing this via the cart might be wrong."*

**Super Wrap GOLD was never missing.** It was sitting in the shop's own reference catalogue as
`0016165170458` while the gun sent `016165170458`. A US packet carries a 12-digit UPC-A; file it in
a European system and it becomes a 13-digit EAN-13 by gaining a leading zero. **Both spellings are
correct and nothing reconciled them.** Measured that afternoon:

```
2,632  reference rows a 12-digit scan could never reach     (24% of the FourTwenty feed)
  135  products stored 12-digit, 13 stored 13-digit padded  — same shop, both ways
   87  products present in BOTH catalogues under DIFFERENT padding
```

In one hour that morning the same till created `0616695693146`, `0602728160143` and
`716165251064` — three UPC-A codes, two spellings. **Lesson #2, in its purest form yet: an exact
match is a filter, and it was discarding the row the lookup existed to find.**

Fixed as lookup tolerance only. **Nothing rewrites what is stored** — a shelf label already printed
carries whichever spelling it was born with and must keep scanning. The question gets asked both
ways; the answer stays where it is.

### What fell out of the side of it

Chasing the wraps surfaced something bigger than five products: **42 active blunts and wraps are
classed `standard` and sell with no ID gate, while 35 near-identical products on the same shelf are
gated correctly.** The split is arbitrary — *Blunt Wrap Platinum* gates, *Cyclones Blunt Hemp* does
not; *Super Wrap Blue* gates, *Super Wrap Tropical* does not.

Angel settled it by picking up the box: **it carries a cigarette-style tobacco health warning.**
FourTwenty classes all eight Super Wraps as `standard`. *The packet outranks the feed* — lesson #8,
verification against reality, arriving as a physical object in a hand.

Two things were deliberately NOT fixed. **The classifier does not know the words "blunt" or
"wrap"** — it catches *Swisher Sweets* and misses *Super Wrap Tropical* — so the safety net I was
about to add **would not have caught these**, and saying so mattered more than shipping it. And
**adopting from the supplier copies the supplier's 18+ answer with no safety net** while the till's
quick-add applies one: same operation, two answers, which is how Tropical came in ungated.

### The shape — and it is Angel's, not mine

He said it at the end of the day: *"I can not see users trying to use the shelf intake unless they
do a couple at a time — but is hard really hard to match products — not really our fault its just
hard."*

Half right, and the other half is the lesson. **Matching genuinely is hard** — 145 supplier codes
sit on more than one product, 71% of a 300-row sample scored below 0.5 similarity, and similarity
cannot even rank correctly (a right match at 0.46, a wrong one at 0.66). That part is real.

**But almost nothing that broke today was a matching problem.** A leading zero, a shift key, a
lookup that never read the SKU, a filename that overwrote itself. Every one deterministic, every one
fixable in an afternoon. And stacked together they made an *exact-identity* case — a product sitting
in the catalogue with a valid code — present itself as *"it's not even on the internet"*.

> **A mechanical failure in an easy case gets read as proof that the hard case is impossible.**
> The easy path failing quietly is what makes people conclude the hard path is hopeless — and then
> reach for cleverness, or for bulk, exactly where neither was needed.

**What generalises.** Before improving the fuzzy layer, prove the exact layer actually works, end to
end, on the machine the person is standing at. Today's work did not make matching better; it made
matching **less necessary** — 2,632 supplier rows moved from "hope the title lines up" to "the code
is the code", which is what `CATALOG-IDENTITY.md` said the answer was all along.

**And the design note worth keeping.** "A couple at a time" is not a limitation to engineer around;
for this shop it is the correct shape. 5,430 products against 50 transactions in the box's whole
life — intake here is *"a box arrived, put four things away"*, not a bulk import. A tool built for
four items done properly beats one built for four hundred done hopefully, and the four-hundred
version is exactly what minted 5,103 fake EANs that had to be unwound.

---

## 2026-08-27, evening — three things that were invisible, and one search on the wrong screen

*The afternoon's entry above was written at half past three. The shop stayed open, Angel kept
working, and the day's second half found a different family of bug: not wrong, not missing —
**invisible**.*

### 1. A refusal nobody could read

Angel typed a LOT number into the Barcode field. Banco refused, and refused **well** — the message
names what the string probably is (*"it is most likely the LOT or BATCH number printed next to the
real barcode"*) and says what to do instead. Perfect words. It rendered as a **toast, pinned to the
top-right of the viewport, for eight seconds**, while his eyes were on a modal in the middle of a
long page.

> *"i could not actually read the error -- it buried behind everything"*

He zoomed the browser to **40%** to find it. Lesson #12, which we already had, and which the
codebase had already paid for once: *a validation nobody can see is a silent failure.* The words
were never the problem. The refusal now renders inside the modal, above the button that failed, and
stays until dismissed.

### 2. One invisible character switched off an entire feature

Angel pasted a bong's `fourtwenty.ch` URL expecting the page's long German description. Nothing came
back, twice, and he concluded the reader had failed. **It had not.** It read the name, the price, the
EAN, the image and six facets correctly. Only the description was wrong, and it was this:

```
description = "‌"        ← ONE U+200C ZERO WIDTH NON-JOINER
```

Invisible. **Truthy.** And it survives `str.strip()`, because it is not whitespace. So:

```
thin = (not facts["description"]) or _looks_like_marketing(...)
     =  False                      or  False
     =  False
```

...and the model was **never asked to read the body prose at all**. The enrichment step was switched
off by a character nobody can see, on every fourtwenty.ch page, for as long as that code has existed.
Fixed by making the blankness test agree with the human looking at the field.

**The generalisation is the same one as the other two in this entry:** a truth test has to answer the
question a PERSON is asking. `if description:` asks "is this string non-empty?". The question was
"is there a description here?", and for one character those two answers differ.

### 3. The search that would have found it was on another screen

Angel hunted an old-favourite rasta bong through his catalogue, the photo matcher and Google, and
gave up:

> *"i have no chance"*

It was in `reference_products` the whole time — Black Leaf *Bong Rasta 18cm*, right EAN, right price,
with a photo. `GET /reference/search` finds it from the single word **"rasta"**, and that endpoint was
already wired into **Receiving** and into **Scan** — but not into the **Catalogue editor**, which is
where products are actually created. *Built, working, on the wrong screen* — the third instance this
week, after the clone endpoint and the force-close.

There was a second barrier, and it is not a software one: **he searched "rainbow" and the feed says
"rasta".** The trade vocabulary is German and nothing translates it. The new panel's empty state
therefore names the words — *rasta not rainbow, Kopf, Schliff, Kawumm* — because the vocabulary IS
the interface here.

### The one I built, measured, and threw away

The reference name-matcher rejects the exactly-correct word: `similarity('rasta', 'Bong Rasta 18cm')`
is **0.375**, under its 0.5 gate, while `word_similarity` scores it **1.000**. Obvious fix. I wrote
it — `GREATEST(similarity, word_similarity)` over title *and* description, exactly what the products
search at `pos_router.py:1715` already does — and then tested it against the old one on six real
inputs:

```
rainbow bong →  OLD: Rainbow Glass Bong 14cm
                NEW: BLAZE Gear Bong Rainbow/Metallic Blue 31cm     ← worse
```

**One case worse, none better.** Reverted, unshipped. Lesson #2's tail, earned again: *a SECOND way
to ask the same question must be tested against the FIRST, never against your own expectations.* It
felt obviously right for the twenty minutes between writing it and measuring it.

### And a verdict I gave three reads too early

The scanner gun corrupts characters. After two setting changes I saw three clean reads and told Angel
it was fixed. He sent nine more: **eight of fourteen still corrupt.** I had made, at n=3, exactly the
mistake I had warned him about two messages earlier — *"one read proves as little as one bad one"*.
A run of heads is not a fixed coin.

The gun was then parked deliberately, on a precise argument rather than fatigue: **the corruption only
lands on a digit immediately before an uppercase letter**, because that is where the shift key
asserts early. Pure-numeric codes never assert shift, so EAN-13 and UPC-A are structurally immune —
which is why every numeric barcode scanned perfectly all day. And Banco's own SKUs put their letters
at the FRONT (`SKU-1787…`), so no digit sits in front of an uppercase letter there either. The
pathological shape — digits, then uppercase, mid-string — is a lot number, which should never be
scanned into a barcode field anyway.

*Parking a bug is a decision, and it needs the same evidence as fixing one.* "It only breaks a shape
we never use, and here is why" is a reason. "We ran out of afternoon" is not.

---

## 2026-08-27, late — the duplicate factory was on the screen nobody was looking at

I opened this on the worklist's own note: *"on a PURE barcode miss `lazyLinkQuery` is empty, so
`openLazy()` skips `searchExisting()` — our own catalogue is never searched — and `confirmAdopt()`
then creates a new product."* I read `openLazyCapture`, agreed, and told Angel in plain words that
Banco never asks itself whether it already owns the packet.

**That was wrong, and the repo said so.** `scripts/prove-no-duplicate-on-a-miss.js` (`f673b66`)
already asserts the opposite, through the real screen, in nine steps. Its own header records a
previous session making the identical mistake and being disproved by reverting the code. I had read
`openLazyCapture` and not its **callers**, which pass the resolved name in — the same error, written
down, in the file named after the bug, and I made it anyway. *A prover is only memory if you read it
before you re-derive the thing it proves.*

The hole that was actually there is one screen over. A miss the supplier feed **knows** re-opens the
find-and-bind panel with the packet's real title already in the search box — that path was correct
and proven. A miss **nobody** knows does not open that panel at all. It leaves the department strip
and the on-the-fly create form on screen — *"New item — with the code you scanned"* — and between
the name a cashier types there and `POST /products/quick` there was nothing. No search, no question.

Which makes it the **normal** path, not the edge case. On a shelf where 91% of rows are filed under
a minted `200…` code that is on no packet, "the scan missed" is the ordinary state of a product we
already own — and the screen she lands on when that happens was the one that could not see the
catalogue. `createNoCodeItem()` does carry a duplicate guard, and it is exactly the wrong one: it
catches a collision on the **same barcode**, which can never fire here, because the twin is filed
under the fiction.

The fix pulled the two-source merge out of `searchExisting()` into `findOwned()` and gave the
on-the-fly form the same question in the same words — ranked search plus the DE↔EN folded matcher,
so *black* still finds *schwarz*. The row is offered above the Create button; tapping binds the
scanned code to what already exists. It never binds by itself (**LESSON #9**).

Two things worth keeping:

- **Pattern 1 again, ×12, and this time both screens were mine.** The capability existed, was
  proven, and was one panel away from the person who needed it. *Which screen is she standing on
  when the thing goes wrong?* — the answer here was "not that one", and no amount of reading the
  fixed path would have said so.
- **Watching it go red is what told the two paths apart.** Nine assertions green and four red in the
  same run, against the same build, is a sentence no amount of source-reading produces. The four
  reds were written before the fix and failed on the shipped image first (**LESSON #4**).

---

## 2026-08-28 — the pictures matched, the RANGE did not

Angel's idea, and it is a good one: every Tamar product carries an excellent photograph, and
FourTwenty publishes 11,014 real GTINs with photographs of their own. Show a person both pictures,
let them say *"yes, that is the same product"*, and bind the EAN. No supplier co-operation needed.

Two blind rounds against **ground truth he established himself** — 116 products where a human had
already bound the EAN off the packet. The EAN was hidden during review, decoys with no correct
answer were mixed in without telling him which, and only afterwards were his answers scored.

| | round 1 (papers/filters) | round 2 (wraps/tobacco/CBD/vapes) |
|---|---|---|
| exact agreement with the hand-bound EAN | 8/14 (57%) | 7/14 (50%) |
| **correct when the twin was actually shown** | 8/10 | **7/8 (88%)** |
| ranker never surfaced the twin | 4/14 | 6/14 |
| **decoys — false positives** | **0/6** | **0/6** |

**Twelve decoys across two rounds and not one false positive.** The human half of this is not the
risk. What went wrong in round 1 was a *variant* confusion — `Elements King Size` bound to
`Elements King Size Slim Papers`, two products of different width sitting on the same card. Round 2
put a dashed outline and a warning on any card where two candidates share a brand, and he then took
**three Blunt Wrap Platinum flavours in a row, all correct**. The same trap, defused by naming it.

### Five things worth keeping

**1. Same product, different photograph — so perceptual hashing cannot do this.** On products known
to be identical, only **2 of 14** image pairs were the same file; median dHash distance 0.35, which
is noise. Both wholesalers photograph their own stock. Pixel hashing scored 57% rank-1 against a
120-image lineup and fell to 50% against 1,761 — it degrades exactly as the pool grows, which is the
wrong direction for a catalogue. *This is a **semantic** comparison wearing a pixel comparison's
clothes. The answer is embeddings, not hashes.*

**2. The negative result was worth more than the positive one.** Twelve grinders and bongs returned
**zero matches** — and he was right every time. The candidates were category-mates, not twins:
`Grinder Alu CNC 4teilig mit Sieb` → `Dragon Grinder 4-teilig Leather Silver`. Only 28% of
grinders/bongs have even a 0.60 name candidate anywhere in the feed. **The two wholesalers' ranges
barely overlap on hardware**, because hardware is house-brand and own-import; they overlap on
consumables, because RAW and Gizeh and Purize are the same packets in both warehouses.

That splits the catalogue, and it halves the job:

```
CONSUMABLE (papers, filters, wraps, tobacco, CBD, vapes)   2,425  ← twins exist, worth matching
HARDWARE   (bongs, grinders, accessories, house-brand)     2,555  ← no twins. Keep the minted EAN.
```

*A minted code on a house-brand bong that exists in no other catalogue on earth is not a
failure — it is the correct answer.* Nothing is gained by hunting a number that was never issued.

**3. My own timer nearly killed a viable method — Pattern 5, third instance.** The first run
reported **128s per decision → 180 hours**, which reads as "not worth doing". It was an artifact:
the clock started when a card *scrolled into view*, and he scrolled the page before working, so
twelve cards started their timers at the same instant. The raw numbers were bimodal and obvious in
hindsight — `5, 5, 6, 7, 10, 24, 34, 87, 191, 193, 194, 195, …`. Real speed is **8–13 seconds**, and
the job is ~9 hours, not a month. *A harness that measures the wrong interval will accuse a working
method exactly as confidently as it would report a true one. Look at the raw distribution before
quoting a mean.*

**4. The title is the second check, and it decides the hard calls.** Angel, unprompted: *"i compare
picture first when obvious and when is a little tougher i compare the titles and that second check
is critical and determines the hit."* The tool had been treating the title as a caption. It is not —
it is the tie-breaker on exactly the cards that are worth getting right, and it deserves the same
room as the image. **Watch what the expert actually does before deciding what the screen should
show.**

**5. Checking the filter before shipping it, for once.** The plan was to drop every candidate whose
`artikel_pro_verkaufseinheit` ≠ 1, since a wholesaler's GTIN is often the box of fifty, not the
packet. Measured against the hand-bound truth first: 75 of 82 correct answers sit on a `units=1`
row, but **2 would have been discarded**, one of them a live mis-bind already in the shop
(`Smoking King Size brown Slim` → a row the feed calls a box of 50). So the rule became *rank down
and flag in orange*, never discard. **Pattern 2 is at ×7 because this is normally found afterwards.**

---

## 2026-08-28, afternoon — the run, and four things that went wrong in the harness

The picture-matcher met real work: 97 Rolling Papers cards, 85 needing an EAN and 12 of Angel's
own hand-bound answers salted in unlabelled. 41 bindings came out of it. What the day actually
taught, though, was mostly about the harness rather than the method.

### 1. THE RESCAN LOOP — the tool that seeds is not the tool that verifies

Angel's, and it closes the whole thing:

> *"its pretty simple to do with the gun in store mode and fed into the shelf intake tool — the odd
> balls or no eans will stand out and the ones that are bound are there listed for the user to
> double check and fix if they need too"*

Picture-matching produces a **hypothesis**: two photographs looked alike and a person agreed. Shelf
intake produces **truth**: a person is holding the packet and the gun reads what is printed on it.
They are not competing tools, they are the two halves of one loop — and the second half already
exists and is the tool Angel trusts most.

So the residual error never has to be hunted. Walk the shelf with the gun, and:

- a bound code that scans is **confirmed** (stamp `confirmed_at`, promote it out of hypothesis)
- a bound code that scans to the WRONG product stands out immediately, on screen, with the packet
  in your hand — the only place that error is visible at all
- an unbound item simply fails to scan and lands in intake like any new product

**A wrong image-match is discovered by ordinary shop work.** That is why `product_barcodes.source`
exists (BL-90b) and why an image-match never takes `products.barcode`: the minted code stays
primary until a packet says otherwise. *This is LESSON #8 with a mechanism attached — verification
against REALITY finds a class of error that verification against the database cannot, and the shop
performs it for free while trading.*

### 2. THE PRICE TELLS YOU IT IS A BOX. THE "UNITS" FIELD DOES NOT. (Pattern 2, ×8)

Angel: *"for that box versus single we could have a price and then i know that is a box price
versus a single and it becomes dead obvious"*. He was right, and it caught four of my errors
**before they were written**.

I had been reading `artikel_pro_verkaufseinheit` as items-per-box. Against what the shop actually
charges, that field is ambiguous — on papers it counts **leaves in a booklet** as often:

```
                          shop    feed   units field     truth
Elements Phantom KS Wide  2.00    5.00   "32"            32 leaves in one booklet
Smoking Supreme Smoqueen  2.00    2.00   "50 Booklet"    50 leaves. Same price = same thing
OCB DW kurz Organic Hemp  2.00   40.00   "25"            a real box, 20x the price
```

**Four of my five "case" codes were singles.** The price ratio flagged a different four, three of
which the units field missed entirely (OCB Virgin 26.7×, G-Rollz 15.4×, Elements Zushi 4.5×).
*A field whose meaning shifts between rows is worse than a missing field, because it reads as
authoritative. Cross it against a number that cannot lie — here, what the shop charges.*

### 3. MY HARNESS FED HIM A PREVIOUS RUN'S ANSWERS, AND I THEN BLAMED HIM FOR THEM

Every sheet used the same `localStorage` key. So the 97-card papers deck opened with **16 of its
first 17 cards already answered** — from round 3, a completely different set of products. Angel
spotted it (*"the first 12 or 14 were already set at the start"*); I had not.

Worse than the bug: **I had already analysed those answers as his.** I reported the one "mistake" he
made (`Raw KS slim Classic Ethereal`) and built a confident little theory about him rejecting
`Smoking Master Silver` twice. Both were artifacts. Re-run clean, he got **both right**.

*Contaminated state does not announce itself — it arrives looking exactly like data. Before drawing
a conclusion about a person's judgement from a harness you wrote, ask what the harness could have
put there on its own.* Fixed: the storage key is now per-run, so a new deck can never inherit.

### 4. THE INTERFACE SAID LOCKED WHEN IT MEANT DONE

> *"had I been asked 'are you sure' I could have cancelled — i was a little trigger happy"*

A decided card dimmed to 50% opacity. It was always clickable; nothing was ever locked. But 50%
opacity is the universal sign for *disabled*, so he believed a misclick was permanent and stopped
trying. **The affordance lied and the behaviour was fine, which is the harder failure to see** —
every test I could write would have passed. Fixed: 82% opacity, an explicit *"nothing is locked"*
line on decided cards, and a per-card ↺ clear.

### 5. And one near-miss worth naming

The first version of the apply commit put a real shop's **product ids, names and EANs into a
PUBLIC repo**. Caught before any push, and only because the deploy step made me look at the remote.
`scripts/ean-match/data/` is now gitignored. *A tool that reads production data will produce
production data, and it will land wherever the tool lives. Decide where its output goes at the
moment you create the folder, not at the moment you push.*
