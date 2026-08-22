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
