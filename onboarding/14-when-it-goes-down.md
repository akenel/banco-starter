# 14 · When it goes down — what actually breaks, and what is worth building

*Design note, 2026-08-04. Written after an evening that started with "should the shop run its own
server?" and ended with Angel arguing the other way and winning. Kept because the reasoning is more
useful than the conclusion.*

---

## The question

Banco runs at `banco.wolfhold.app`, on one box in a data centre. So **no internet means no selling.**
The tablet build gave the shop four network paths — shop Wi-Fi, phone hotspot, and two tablet SIMs
on two genuinely different Swiss networks — but every one of them reaches the same server.

That looked like an argument for running Banco **in the shop**. It mostly is not, and the reason is
worth writing down before someone re-derives it.

---

## What actually breaks — and what each option covers

| What fails | How often | Can the shop sell? | Does on-prem help? |
|---|---|---|---|
| **Power out** | rare, hours | ❌ card terminal dead, printer dead, lights out | **Barely.** Laptop and tablets have batteries — the *system* survives. The shop mostly does not. |
| **Internet out, power fine** | occasional, usually same-day | ❌ today | ✅ **Yes. This is the only case it genuinely fixes.** |
| **Bad deploy / app bug** | most likely of all | ❌ | ❌ **No.** The bad code follows you on-prem. |
| **Hetzner outage** | rare | ❌ | ✅ yes |
| **Shop server dies** | — | ❌ | 🆕 **a failure you did not have before** |

---

## The trade nobody mentions

> *Angel:* **"You're trading either your laptop is gonna save the day, or Hetzner is gonna save the
> day. And the Hetzner servers are extremely good — probably more reliable than some laptop."**

He is right, and it is the strongest point in the whole discussion.

A Hetzner box has redundant power, N+1 cooling, ECC memory, monitored hardware and staff on site
around the clock. The proposed shop server is a **2015 laptop found in the rubbish** with a consumer
SSD, no ECC, and a shop's worth of dust, heat and people who might need that socket.

**On-prem does not buy reliability. It buys independence from the WAN.** Those are different goods,
and it is easy to sell the second while implying the first. The honest expectation is that a shop
laptop has **more** downtime than Hetzner — just downtime you can walk over to and reboot.

---

## The realism argument

> *Angel:* **"Are we planning for something realistic here? Power comes back within four hours. If
> it's out for three days you've got bigger fish to fry than selling some papers. The question is: is
> the internet down and do we have a new internet connection? That's usually solvable the same day —
> a reboot in most cases."**

This is the part that settles it.

The scenario on-prem uniquely fixes is **internet down, power up, for longer than a shop can absorb.**
Against that we have already spent the money that matters: four independent paths, two of them on
separate mobile networks. For all four to fail at once *and* stay failed long enough to hurt is not
where the next franc of effort belongs.

And in the case that *is* common — a bad deploy, an app bug — on-prem does nothing at all. The bug
travels with you.

---

## Verdict: not now

**Do not build it.** Revisit only if one of these becomes true:

- The shop's internet proves genuinely unreliable **in practice, measured** — not feared. If the till
  logs outages over a few months, that is evidence. Until then it is a hunch.
- The shop grows past the point where a lost hour is absorbable.
- The on-prem hardware and someone to look after it are free anyway, *and* the HTTPS and remote-access
  problems below are already solved for other reasons.

**If it is ever built, the costs are not the app.** `docker compose up` is the easy half. The real
work is:

- **Keycloak signs its hostname into every token.** New hostname means `KC_HOSTNAME`, the realm
  issuer and every client redirect URI change together, or logins fail in ways that read like the app
  broke.
- **HTTPS on a LAN.** Plain `http://192.168.x.x` is **not a secure context**, so the phone's camera
  snap-fill stops working and it looks like a regression. Caddy handles it — **DNS-01 needs only a
  TXT record**, so a real Let's Encrypt cert is possible without publishing the shop's internal IP.
  Caddy also ships an internal CA as a fallback. **Traefik is not needed**; Caddy already does both,
  and swapping would mean rewriting `compose.prod.yml`, `Caddyfile.example` and `go-live.py` for zero
  gain.
- **Never use `.local`** — mDNS owns it and no public cert can be issued for it. Use subdomains of a
  domain we own.
- ⚠️ **Resolution must be local or the whole thing defeats itself.** A till resolving through public
  DNS cannot resolve anything when the WAN drops — the exact outage on-prem exists to survive.
  `/etc/hosts` on each machine is three files and zero infrastructure; `dnsmasq` on the shop box if
  the device list grows or phones need it (`/etc/hosts` cannot be edited on Android or iOS).
- **Tailscale for Angel's remote access, never as the shop's local path.** New Tailscale connections
  lean on its coordination servers, which is the one thing you do not want in the critical path of
  "the internet is down."

---

## What to do instead — all three already filed

The cheap things cover more of the real failure surface than the expensive thing does:

1. **Watch prod from outside it.** Right now the monitoring is Felix phoning. An external check on
   `/health/healthz` costs ten minutes and covers *every* server failure, including the bad deploy
   that on-prem would not have helped with.
2. **Restore a backup for real.** Never done. A backup looks identical whether it works or not, right
   up to the day it matters.
3. **Make the cart survive a crash.** The likeliest failure of all — one tablet, one dropped sale —
   and the one a cashier meets in person.

---

## And the answer that covers everything: paper

> *Angel:* **"You're gonna have to write it down and take the cash. That's all you can do."**

Every branch of the table above ends in the same place when it gets bad enough, and it costs nothing
to be ready for it. **The gap is not the paper — it is coming back from it.** See the backlog item on
re-entering offline sales.

**Angel's read on the price of getting that slightly wrong is worth recording**, because it changes
how much the fix is worth building:

> *"It would be the wrong time, when the sale didn't happen — but it wouldn't really be that bad,
> because it doesn't ever happen."*

So the expensive version — true backdating, shift reattribution, reopening a closed shift, a
permission story for editing money — is **not** justified by an event this rare. The cheap version
probably is: type the sales in when the system is back, and **use the cash box's existing note
mechanism to say why the drawer and the shift disagree.** Named cash reasons and notes already exist
from the 2026-08-03 work. An explained discrepancy is not a discrepancy; an unexplained one costs
somebody an evening.

---

## Don't write barcodes by hand — scan them into a text file

**The gun is a keyboard.** It does not know or care whether the internet exists. Open a plain text
editor on the tablet, scan, and the barcode types itself in — perfectly, every time.

That matters more here than it looks. `CATALOG-IDENTITY.md` says the **barcode is the identity**;
a hand-copied 13-digit EAN with one transposed digit is a worthless line. Scanning gives a clean
code with no transcription step at all. **Paper is the fallback to the fallback.**

The codebase already knew this — `catalog_workbook.py` was built around it:

> *"the BARCODE — scanned straight into the cell, since a scanner gun is just a keyboard"*

**Two things to settle while it is calm, not during an outage:**

1. **Test it once.** Scan into a plain text editor on the tablet and confirm the code lands clean.
   Same question as `/pos/hardware` — **use a hyphenated code**, because digits sit in the same place
   on every keyboard layout and prove nothing.
2. **Agree the line format now.** `EAN, qty, price` and re-entry is a paste. Let everyone invent
   their own under pressure and it is transcription work again, which is exactly what scanning was
   supposed to remove.

---

## 📦 The offline kit — and why it is bigger than an outage plan

*Angel's idea, 2026-08-04, and it is the best one in this document.*

A **daily export** sitting on the back-office laptop: the whole catalogue — names, barcodes, **sale
prices and costs** — as a real spreadsheet, plus the product images in a folder the sheet links to,
plus a simple order form.

When Banco is unreachable, Felix opens the file. He can look a product up, price a basket, fill the
form, and print it or save a PDF — *"I'll email it to you, give me your address"*. Nothing on that
path needs a server, a network, or Banco.

**Most of the machinery already exists.** `src/services/catalog_workbook.py` writes a genuine `.xlsx`
with formulas, dropdowns and conditional formatting, and its design rules were chosen for exactly
this: **formulas and validation, never macros**, so it opens in Excel, LibreOffice *and* Google
Sheets. This is a second export profile on a tool that already works, not a build from scratch.

**The order form should be a VLOOKUP, not a blank page.** Scan the barcode into a cell; the name and
price appear from the catalogue tab. That is a working cash till in a spreadsheet, using the gun you
already own, with no code and no network.

### Why this is the point of the whole project

`CLAUDE.md` states the premise: *"kill the 'what if the vendor vanishes?' fear with ownership, not a
promise."*

**This is that promise made testable.** Not a licence clause, not a repository he will never read —
a file on his own laptop that opens without us, and would still open in twenty years. Angel put it
best:

> *"The day he says, listen, I've had enough, Angelo, you're just too much for me — I'm taking my
> CSV file and I'm going onto a spreadsheet version of this whole thing."*

**That has to be true, or the premise is marketing.** A shop owner who can walk away with a working
spreadsheet is a shop owner who chose to stay.

### What it needs to actually work

- **Generated daily and automatically.** A bundle nobody refreshes is stale on the one day it is
  needed. `scripts/install-backup-cron.sh` already establishes the pattern.
- **Images as relative paths into a subfolder**, zipped with the sheet — absolute URLs are dead links
  the moment the network is.
- **Costs included, not just sale prices.** Half the value of a catalogue you own is knowing your
  margin.
- **Proved the only way that counts:** open the bundle on a machine with the network switched off and
  price a real basket. A green export script proves nothing — same rule as the label printer.

---

---

## 🪜 The degradation ladder — what to do when it gets ugly

*Pin this by the till. Each rung: what still works, and the one action.*

| # | What broke | Can the shop sell? | Do this |
|---|---|---|---|
| **0** | nothing | ✅ | — |
| **1** | a tablet or a gun dies | ✅ | **Take the spare.** Two of each is why they exist. ⚠️ The cart does **not** transfer — re-scan the basket. |
| **2** | labeller's network path | ✅ | Switch to the **Bluetooth** queue. Or the USB cable. |
| **3** | labeller dead entirely | ✅ | **Keep selling.** Labels are *shelf prep*, not part of a sale. Catch up later. |
| **4** | shop Wi-Fi | ✅ | **One tap** — *Switch to Hotspot* or *Switch to Mobile*. It will **not** switch itself, in either direction. |
| **5** | all internet | ⚠️ **cash only** | Cards are gone — Worldline needs the network. Put up a **cash-only** sign. **Scan into a text file**, don't write EANs by hand. |
| **6** | Banco itself (bad deploy, Hetzner) | ⚠️ cash only | Same as 5. Network is fine, so **the phone camera still works** — photograph anything unclear. |
| **7** | power | ⚠️ cash only, briefly | Tablets and the laptop run on battery; the printer and card terminal do not. **The offline spreadsheet** on the back-office laptop is the lookup. Then paper. |
| **8** | everything | ⚠️ cash only | **Paper and cash.** Nothing else to do, and it is enough. |

### The three things worth knowing before you need them

**Rung 3 is the reassuring one.** A dead labeller feels like a stopped shop and is not — nothing in a
sale depends on printing a label. Say that to staff in advance or someone will close the till over it.

**Rungs 5 and up are all the same shop:** cash, a list of scanned barcodes, and a customer who does
not care. The only real loss is **card payments**, and no amount of engineering fixes that.

**Every rung ends the same way — coming back.** The sale is not the problem; the *re-entry* is. See
the backlog item on offline sales, and the note above about scoping it cheap.

### Recovery order when it all comes back

1. **Power-cycle the labeller** if it was mid-job — but remember the queue lives on the tablet, so
   `retry-job` is what makes that enough on its own.
2. **Tap back to shop Wi-Fi.** It does not return by itself.
3. **Key in the scanned list**, and use the cash box's note field to say why the drawer is high.
4. **Then** print the labels you skipped at rung 3.

---

## The whole plan, on one line

**Four ways onto the internet · scan into a text file when they all fail · a daily spreadsheet bundle
that works without us · and a documented way back in.**
