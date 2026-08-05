# 16 · Bill of materials — a complete Banco POS for Artemis Luzern

*Written 2026-08-05 from kit that is on the counter and working, not from a catalogue. Prices are
what Angel actually paid, in CHF. **This is the reference build**: what a second shop would need to
stand up the same thing.*

---

## The whole system, at a glance

| # | Item | Qty | Unit | Total | Status |
|---|---|---|---|---|---|
| 1 | **ThinkPad X1 Tablet Gen 2** (i5 vPro, 8 GB, detachable folio, LTE) | 2 | 0.– | **0.–** | 1 built ✅ · 1 promised by Felix |
| 2 | **HP laptop**, refurbished (rebuilt, new SSD) | 1 | 40.– | **40.–** | ✅ working |
| 3 | **Netum scanner gun** — store mode, 3,000 codes | 1 | ~40.– | **40.–** | ✅ working |
| 4 | **Inateck scanner gun** — Bluetooth + dongle | 1 | ~40.– | **40.–** | ✅ working |
| 5 | **Brother QL-820NWB** label printer | 1 | ~200.– | **200.–** | ✅ working (BT) |
| 6 | **DK-44205** continuous roll, 62 mm black | ≥2 | ~25.– | **50.–** | consumable |
| 7 | **Gun stand**, screwed to the counter | 1 | ~20.– | **20.–** | ⛔ to buy |
| 8 | **Power bar, 5+ sockets** | 1 | ~25.– | **25.–** | ⛔ to buy |
| 8b | **USB webcam** (any UVC) — the X1's built-in camera is IPU3 and **does not work on Linux** | 1–2 | ~20.– | **20–40.–** | ⛔ to buy |
| 9 | **Data-only SIM** (Yallo / Salt — *different networks*) | 2 | ~10.–/mo | **20.–/mo** | ⛔ optional |
| 10 | **Hetzner VPS** + `wolfhold.app` | 1 | ~10.–/mo | **10.–/mo** | ✅ running |
| 11 | **Backblaze B2** off-site backup | 1 | ~2.–/mo | **2.–/mo** | ✅ running |
| | **Hardware, one-off** | | | **≈ 415.–** | |
| | **Running cost** | | | **≈ 12–32.–/mo** | |

> **Under CHF 500 of hardware for a two-till shop**, and CHF 40 of it is the back-office machine.
> The dominant line is the label printer — everything else is second-hand, free, or a consumable.

**Already owned, no line item:** Felix's Windows PC and document printer, the shop mobile (hotspot +
camera), the old Win 10 tablet, and the shop Wi-Fi.

---

## What each piece is FOR

Roles and the reasoning live in [`10-devices-and-roles.md`](10-devices-and-roles.md). In one line each:

- **Tablet ×2** — the tills. Selling, stock checks, label printing. **Interchangeable**, which is the
  whole point: either one is the spare.
- **HP laptop** — back office. Bulk enrichment, reports, restores, photo booth. Anything wanting a
  real keyboard.
- **Netum** — shelf intake. **Only gun that can buffer a section.**
- **Inateck** — the till and roaming checks. **Only gun that works without the tablet's USB port.**
- **QL-820NWB** — shelf labels. Bluetooth today; **on the LAN it serves every machine**, including
  Felix's Windows box.
- **Phone** — backup, hotspot, and the **only good camera** in the kit.

---

## The counter is a charging station that happens to sell things

This is the part nobody budgets for and everybody needs.

- **Gun stand screwed down** — it does not move, so the guns always have the same home. A gun with no
  home gets lost.
- **The power bar wants 5 sockets**: 2 guns + printer + tablet + laptop.
- **Both guns and both tablets live on charge between uses.** That is what makes "everything live"
  survivable — nothing is off-duty waiting to be needed.
- **Label the two gun cables.** They are not interchangeable.
- **Cable slack.** A yanked gun must not drag the bar off the counter.

---

## What is NOT in this BOM, and why

- **Cash drawer / card terminal** — Felix's Worldline setup stays as it is. Banco does not touch it.
- **A shop server.** Deliberately: see [`14-when-it-goes-down.md`](14-when-it-goes-down.md). A
  rubbish-find laptop is not more reliable than a data centre.
- **A second label printer.** The ladder in doc 14 says a dead labeller does **not** stop selling —
  labels are shelf prep. Buy the spare when it proves annoying, not before.
- **A UPS.** The tablets and the laptop have batteries. The printer and the card terminal do not, and
  in a power cut the shop has bigger problems.

---

## Standing it up, in order

1. Build tablet #2 — [`13-tablet-x1-debian.md`](13-tablet-x1-debian.md) § BUILD SHEET, ~90 min.
2. **QL on the shop Wi-Fi** — fills most of the print matrix in doc 10 in one move.
3. Stand screwed down, power bar in, cables labelled.
4. `/pos/hardware` with a **hyphenated** code: 2 guns × 3 machines.
5. SIMs, if bought — **two different networks**, or it is one network twice.
6. Save shop Wi-Fi + both hotspots on both tablets, and pin the switch launchers.

---

## 🎯 The catalogue decision: the 300 hottest, not all 5,173

*Angel, 2026-08-05: "we only sell to seed except the 300 hottest items — the rest we wait, or do we
take the time to clean and validate every EAN in the shop now?"*

**Do the 300. Do not validate the whole shop.** Three reasons, all already learned here:

**1. The long tail binds itself, for free.** The till binds a real EAN on first scan — that is the
Pam-and-the-grinder path from 2026-08-03. Every slow mover gets validated **the day it actually
sells**, by the person holding it, at zero extra cost. Pre-validating 4,800 items to avoid that is
work done twice.

**2. Verification only counts against reality.** The 2026-08-02 lesson: *a wrong bind looks exactly
like a right one — only a re-scan can tell them apart.* So "validate everything" means physically
handling 5,173 packets **twice**. Rushed, that is how Cannazym ends up bound to Cannaboost — CHF 12
against CHF 35, same brand, same bottle, and nothing in the database able to notice.

**3. 300 hot items is most of the till's work.** Realistically 80 %+ of scans. Get those right and
the till feels solid. In the tail, *skip it* is usually the correct answer anyway.

**Do this alongside:** **log the unknown EANs that get hit at the till.** That turns the tail from a
4,800-item wall into a **ranked queue driven by real demand** — the next thing to validate is
whatever customers actually brought to the counter. Cheap to capture, and it beats guessing.

**Working rule:** one shelf section at a time, worked with the packets still in front of you. Per
2026-08-02, **batch size is set by the failures, not the scanning** — 30 scanned means 3 to re-find
while you are still in that aisle; 300 scanned means 30 and a second trip.
