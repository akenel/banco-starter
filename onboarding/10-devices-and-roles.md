# 10 · Which device does what — and who does which job

*Written 2026-07-31 from a real kit test: a Windows 10 Lenovo tablet, an HP ProBook, a phone, two
scanner guns and a label printer. Every capability line was measured on the device, not assumed.*

---

## The two jobs, and why they must not be the same screen

This is the distinction everything else falls out of.

> **Setup is not selling.** Angel, after a day of it: *"At the cashier, this wouldn't work. This is
> me programming and setting these up ahead of time."*

| | **Setup** (owner / manager) | **Selling** (cashier) |
|---|---|---|
| Who | Angel, Felix | Leandra, Roger, Nathan |
| When | evenings, before the shop relies on it | all day, customer waiting |
| Looks like | scan the shelf → find the product on the web → judge it → set a price | scan → it rings up |
| Time per item | 30 s – 5 min, and that is fine | **2 seconds, or it is broken** |
| Screen | `/pos/shelf-intake` (manager) | `/pos/scan` |
| Decisions | many, and they need a human | **none** |

A cashier must never be asked "is it one of these?" mid-sale. If the till asks that, the catalogue
work was not finished — the answer is to do more setup, not to make the cashier faster.

---

## The devices

Measured on each machine with `<your Banco address>/pos/hardware` and `/static/tablet-check.html`.

| | 📱 Phone | 💻 **Tablet** (Win 10) | 🖥️ ProBook laptop |
|---|---|---|---|
| **Role** | emergency backup | **shop floor till** + Angel's capture work | back office / workhorse |
| Scanner gun | Bluetooth only — fiddly | **USB dongle** ✅ | dongle or cable ✅ |
| Swap guns mid-shift | re-pair each time | **just move the dongle** | just move the dongle |
| Camera / photograph a packet | ✅ **best of the three** | ❌ **none** | ✅ |
| Label printer | ✗ | ✗ (not wired) | ✅ the one that prints |
| Mobile | ✅ | ✅ enough | ✗ |

### What each is actually FOR

- **Tablet — the till, and Angel's capture tool.** One USB port is all it takes: dongle in, gun
  works, no pairing. Swapping to the second gun is unplug-replug. Windows 10 is fine and
  **should be left alone** — it works, and putting Linux on it would hand the staff something new
  to learn for no gain.
- **Phone — the backup, and the camera.** Worst for scanning (Bluetooth pairing, no USB) and best
  for photographing a packet. Keep it in the mix precisely for the job the tablet cannot do.
- **ProBook — the workhorse.** The label printer lives here, and so does anything that wants a real
  keyboard: bulk enrichment, reports, restores.

### The camera thing is a role boundary, not a bug

📷 snap-and-fill **does nothing on the tablet** — it has no camera, so the button appears to be
broken rather than saying so. The same flow works well on the phone.

That is not a defect to fix; it is the line between the devices. `/pos/hardware` now reports the
camera explicitly so the next person doesn't spend twenty minutes on it.

---

## Guns: buy two, and know why

The gun does **not** charge usefully while it is being used, and a flat gun mid-shift is a stopped
till. So:

- **Two guns, always.** One in hand, one on charge. This is not redundancy for breakage — it is the
  normal duty cycle.
- **The dongle beats Bluetooth** on any device with a USB port. It is the manufacturer's default,
  needs no driver or pairing, and — the real reason — **there is nothing to re-pair when it drops
  mid-sale.**
- A charging cradle at the kiosk gives the spare gun a home. A gun with no home gets lost.

Setup and the keyboard-layout trap: [`testsheets/Scanners/README.md`](testsheets/Scanners/README.md).

---

## Prices from the web are evidence, not prices

Finding a product by searching its EAN works ~9 times in 10, and the page will state a price. That
price is **not your price**, for two independent reasons:

1. **It may be another currency.** Angel's "Buzz" filters are French and priced in EUR. Banco shows
   the page's own currency label and refuses to prefill a foreign figure — you type yours.
2. **Even in the right currency it is somebody else's retail price in another country.** It tells
   you roughly what a thing costs. It does not tell you what this shop charges.

The sale price is always typed by a human. Shelf intake will not let you create a product without
one — an item that rings up at 0.00 is worse than one that is missing, because the missing one gets
noticed.

---

## The routine, in order

**Before the shop opens, on every machine you will use:**

1. `<your Banco address>/pos/hardware` — scan a hyphenated test code. Green = the gun and that
   machine agree. Do this **per machine**, every time a gun moves.

**Setup session — AT THE SHELF, tablet in hand, one section at a time.** (Corrected 2026-07-31:
you cannot carry a few hundred codes back to a desk. Choosing between `Slim` and `Slim mit Filter`
needs the packet, and by then you don't have it — see [09](09-shelf-intake.md).)

2. Gun into `Inventurmodus`, scan **one shelf section** (10–15 facings). ~2 s each, no thinking.
3. Scan `Anzahl der gescannten Barcodes` and check the count.
4. `/pos/shelf-intake` → type the count → scan `Daten hochladen` into the big box.
5. Counts agree? Then `Daten im Cache löschen`, then `Normalmodus`.
6. Work them **with the packets still in front of you**:
   - **① Type two or three words off the label** — most of the shop is already in the catalogue and
     only its barcode is a fiction. Pick by the **bold** words and the picture. ~15 seconds.
   - **② Only if nothing matches**, find it on the web and paste the page. ~1 minute.
   - **Unsure?** Skip it. A wrong bind is worse than none.
7. Next section.

**Proving it (the only step that counts):**

7. Go to `/pos/scan` on the **till** and scan ten of those products at random. If they ring up, the
   catalogue is real. Tests passing is not done; a human holding a packet is done.

---

## The detachable tablets — answered 2026-08-04

The "other Lenovo units" below turned out to be **ThinkPad X1 Tablet Gen 2** (7th-gen i5 vPro,
detachable folio, LTE modem). Felix handed one over to be scrapped; it now runs Debian and prints
labels. Full build sheet: [`13-tablet-x1-debian.md`](13-tablet-x1-debian.md).

**Target fleet — Angel, 2026-08-04:** *"There'll be two tablets, two guns, and everything's charging
all day long, and the mobile phone is on backup. That's the way it has to be."*

| | 📱 Phone | 💻 Tablet (Win 10) | 📲 **X1 Tablet** ×2 (Debian) | 🖥️ ProBook |
|---|---|---|---|---|
| **Role** | backup + camera | shop floor till | **till + capture** | back office |
| Scanner gun | Bluetooth only | USB dongle ✅ | **USB-A dongle *or* Bluetooth** ✅ | ✅ |
| Label printer | ✗ | ✗ | ✅ **over Bluetooth** | ✅ |
| Camera | ✅ best | ❌ | ❌ | ✅ |
| Detaches | — | ✗ | ✅ folio, portrait or landscape | — |

**The X1 changes one thing that mattered:** it has **one USB-A port and the gun needs it**, so the
printer had to go wireless. It prints over **Bluetooth** — `printer-driver-ptouch` 1.7.1, which
works where 1.6 failed. Gun and printer now run at the same time on one tablet.

**Windows 10 on the *old* tablet still gets left alone.** It works, and the argument above stands.
The X1s are additional machines, not replacements.

---

## Still open

- **Charging cradle** for the spare gun — where does it live on the counter? More urgent now: two
  tablets and two guns means four things wanting a home and a charger on that counter.
- **Build the second X1.** Follow the build sheet in [`13`](13-tablet-x1-debian.md) §BUILD SHEET.
- **Label printer over Wi-Fi.** Bluetooth solved the tablet, but the QL is a `NWB` and putting it on
  the network would let *every* machine print, including the old Win 10 tablet and the phone. Still
  worth doing.
- **No internet means no selling.** Banco lives in a data centre, so a WAN outage stops the till
  whatever you do about Wi-Fi. See the failover section in [`13`](13-tablet-x1-debian.md) — the
  honest answer is a Banco running *in* the shop, which is a real decision, not a setting.
