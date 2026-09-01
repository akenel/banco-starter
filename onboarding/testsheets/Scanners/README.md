# Scanner guns — setup and the keyboard-layout trap

## The trap, first

**A scanner gun is a keyboard.** It doesn't send text — it presses the *key* that produces a character
on **its own** configured layout, and the OS reads that key through the layout **the session** uses.
Mismatch them and punctuation silently mutates.

Seen for real on 2026-07-29, both guns, both machines:

```
page showed:   QR-LOGO-15
gun typed:     QR'LOGO'15
```

Gun on **US**, session on **Swiss German (`ch`)**. US puts `-` right of `0`; Swiss German reads that key
as `'`.

**Why it hides for weeks:** EAN-13 is pure digits, and digits are identical across these layouts. Till
scanning looks perfect. But **every SKU has a hyphen** (`TAM-21796`), so the first Code128 SKU label
scanned finds nothing.

| Layout | key right of `0` | key right of `.` |
|---|---|---|
| US | `-` | `/` |
| UK / GB | `-` | `/` |
| **Swiss German** | `'` | `-` |
| **German** | `ß` | `-` |

German and Swiss German agree on `-`. That matters below.

> It is also **per-user**: `gsettings` layout is per session, so the bug can appear for one user and not
> another on the same machine — nasty when the kiosk auto-logs-in as one user and staff switch to another.
> Check both: `localectl status; gsettings get org.gnome.desktop.input-sources sources`

> ⚠️ **And it is per-MACHINE, which is the part that bites when a shop adds a till.** Both guns were set to
> **German** on 2026-07-29 to match Swiss German *Linux* sessions. Move a gun to a **Windows** till whose
> layout is US English and the mismatch is simply reversed — same silent corruption, opposite direction.
> The gun's setting is not "right" or "wrong" on its own; it is only right **relative to the machine it is
> plugged into**. On Windows: *Settings → Time & Language → Language & region*. Re-run the test sheet on
> every new till, and never assume a gun that worked yesterday is correct on today's hardware.

---

## Connecting a gun — use the dongle, not Bluetooth

Three ways, and the manufacturer's default is also the right one for a till (BCST-35 manual §4.1, page 3):

| Mode | Default | What it takes | Verdict |
|---|---|---|---|
| **Wireless adapter (2.4 GHz dongle)** | **★ yes** | Plug the dongle in. LED flashes = paired. | **Use this.** |
| Wired (USB cable) | no | Cable into the gun's USB-B socket | Fine. Tethers the gun. |
| Bluetooth (HID) | no | Scan `Bluetooth Pairing` (page 3), then pair in the OS | Last resort. |

### 🔴 "It doesn't scan" may be the GUN, not the barcode

*Angel, 2026-08-06, spot-checking the previous day's bindings:* the **Netum read everything**, while
the **Inateck read most and choked on a few of the same codes**. He had bound those items the day
before with the Netum and hit no trouble at all.

**So a failed read is not proof of a bad code.** Two guns, same packet, different verdicts — and the
expensive mistake is the one that follows: concluding the barcode is unreadable, then re-binding or
re-creating a row that was already perfectly correct. That is how a duplicate is born.

**The rule: before declaring a code dead, try the OTHER gun.** It costs five seconds. Only if both
guns fail is it the packet — and then the 2026-08-02 lesson applies (it may be an outer multipack;
open it and scan a single).

Worth knowing which is which: the **Netum** is the more capable reader here. The Inateck is a fine
2D imager and reads our QR labels down to 10 mm, but on worn or curved 1D codes the Netum wins.

### 🔵 Bluetooth won't hold? It is almost never the radio

*Angel, 2026-08-06, pairing the Inateck to his phone: "connecting is really unreliable, what do I do
wrong… actually it was easier — I just needed to add the new device. I had another name before, I
deleted that and now it works fine, and I renamed the BT connection so I cannot mess it up."*

**A stale bond is the usual culprit**, and it presents as a bad radio rather than as bookkeeping.
Work down this list before suspecting the gun:

1. **Delete the OLD pairing entry and add it fresh.** A half-dead bond from an earlier attempt keeps
   answering and then dropping. This is what it was.
2. **Rename the connection to something unmistakable** ("Angel phone — Inateck"). These guns all
   advertise near-identical default names; with two guns and three hosts you will pair the wrong one.
3. **The gun bonds to ONE host.** If the tablet is nearby with Bluetooth on, it will try to reconnect
   there. **Turn the tablet's Bluetooth off while pairing the phone**, or unpair it there first.
4. **Is it even in Bluetooth mode?** The BCST-35 ships in *Wireless Adapter* mode and does not
   advertise at all until you scan `Enter Setup` → `Bluetooth Paring (HID Mode)` → `Save and Exit`
   (manual §4.1, page 3 — scan straight off the screen).
5. **On Android, Gboard must be the active keyboard** (manual §4.3, page 4): set the gun to
   *Windows/Android Mode* + *US Keyboard*. With another keyboard app it pairs and then behaves
   erratically — which reads exactly like an unreliable connection.

> ⚠️ **One gun cannot be right for both hosts.** The tablet wants **German Keyboard** (QWERTZ, correct
> hyphen); the phone wants **US Keyboard** with Gboard. That is a setting on the GUN, not per host —
> so a gun that moves between them needs re-scanning each time, or it types wrong characters on one.
> **Decide which host each gun belongs to.** The Netum is dongle-only, so it is the tablet's; leaving
> the Inateck as the phone's gun keeps both settings stable.

**Why the dongle wins, and it isn't just convenience.** It presents as a plain USB keyboard: no driver,
no pairing dialog, no OS Bluetooth stack, and **nothing to re-pair when it drops mid-sale**. Bluetooth HID
on a till has one failure mode the dongle simply doesn't have — the gun silently unpairs, and the next scan
goes nowhere while a customer waits. The dongle either is plugged in or it isn't.

The gun is 2.402–2.480 GHz with a 2600 mAh battery, charged over the same USB cable.

> **If the wireless link starts dropping characters**, the manual's own repair is to re-bind the gun to its
> adapter: scan `Enter Setup` → `Wireless Adapter Mode` → `Exit and Save`. Try that before suspecting the gun.

> **One USB port on the device?** That's the real constraint on a tablet, not the connection mode. Check
> whether that port is also how the tablet charges — if it is, you want a small **powered** USB hub, so the
> till can charge and scan at once. A gun that works only while the tablet is unplugged is a shop-floor
> problem you'll discover at the worst moment.

**System setting:** the BCST-35 ships in `Windows/Android` mode (manual §4.3), which is already correct for a
Windows till or an Android tablet. Only Mac/iOS needs changing.

---

## Inateck BCST-35 (the CHF 36 one)

2D imager — reads QR, Data Matrix, PDF417, Aztec as well as all the usual 1D. Confirmed reading our QR
labels down to **10 mm**.

**Configuration is by scanning barcodes out of the manual** (`Inateck_BCST-35_..._User_Manual-V1.2.pdf`,
in this folder). The barcodes are images, so text-searching the PDF finds nothing — open it and look.

**There is no Swiss German option.** Available: US *(factory default)*, German, French, Italian, Spanish,
UK, Canadian, Japanese, Swedish, Dutch, Danish, Norwegian, Portuguese, Polish.

**Use German.** It puts `-` on the same key as Swiss German, and both are QWERTZ, so letters, digits and
hyphens all come through correctly on a `ch` machine.

### Setting it — manual page 4, "Keyboard Setting"

Scan these three in order. You can scan straight off the screen.

1. **`Enter Setup`** — wide barcode at the **top** of the page
2. **`German Keyboard`**
3. **`Save and Exit`** — wide barcode at the **bottom** of the page

The manual's own rule: *[Enter Setup] – [Specific Function Setting] – [Exit and Save]*. Blue LED stays lit
while in setup mode. A `(*)` next to a barcode means factory default.

### Then verify — do not assume

Open **`<your Banco address>/static/scanner-gun-test.html`** — **on the machine the gun is plugged into**,
because that is whose keyboard layout decides the answer. Click the capture box, scan a few codes:

```
QR-LOGO-15   ✅ gun and session agree
QR'LOGO'15   ❌ still mismatched
```

Every code on that page names its own size, so the log also tells you the smallest one your gun manages.

---

## Netum NS L8 (the CHF 55 one)

Also a 2D imager, and the better scanner of the two — faster and more forgiving on awkward angles.

**Its config codes live on the web, not in the box.** The booklet exists but is thin; the full set is at:

**<https://doc1.netum.net/L8/en/keyboard>**

Open that page and scan the layout you want **straight off the screen**. Same three-step pattern as any gun:
enter setup → pick the setting → save.

Set to **German** for the same reason as the Inateck — Swiss German isn't usually offered, and German puts `-`
on the same physical key.

> Bookmark that URL, or save the page. A gun whose config lives on a vendor website is one domain change away
> from being unconfigurable — which is exactly the sort of thing that bites three years later when a shop
> replaces a till.

---

## Both guns, as configured 2026-07-29

| | Inateck BCST-35 | Netum NS L8 |
|---|---|---|
| Price | ~CHF 36 | ~CHF 55 |
| 2D (QR) | ✅ | ✅ |
| Config via | PDF in this folder, page 4 | <https://doc1.netum.net/L8/en/keyboard> |
| Layout set to | German | German |
| Verified | `-` comes through correctly, QR to 10 mm | `-` correct, QR reads |

Both passed `/static/scanner-gun-test.html` after the change: hyphens arrive as `-`, not `'`.


---

## Inventory mode — scan the whole shop, upload later

> ⚠️ **CORRECTED 2026-08-22 — THE STORE-MODE GUN IS THE NETUM, NOT THE INATECK.**
> This section used to open *"The BCST-35 stores up to 3,000 codes offline"*, citing the Inateck
> manual §4.6, and `WORKLIST.md` said the opposite. Angel settled it from the bench:
> *"the NetumScan gun holds the 3000 codes, well tested and works fine. The Inateck gun is ok but
> only single shooter, and it has a Bluetooth feature so it can be used with a tablet or phone."*
> **The gun that walks the shelf is the Netum NS L8.** The Inateck BCST-35 is the single-shot
> gun, and its Bluetooth is what makes it the phone/tablet one. The Inateck manual may well
> document an Inventurmodus of its own — nobody here uses it, and the tested path is the Netum.
> The barcode table below came out of the Inateck PDF; **use the Netum's own key sheet**
> (<https://doc1.netum.net/L8/en/keyboard>) for the real thing.

**The Netum NS L8 stores up to 3,000 codes offline** — tested and working, 2026-08-22. This is
the right way to build a catalog: walk the shelves scanning, then do the desk work later, batched.

**The dump survives the browser textarea.** That was the last open unknown in shelf intake and
Angel closed it: *"there are no issues."* `/pos/shelf-intake` is read-only until you act on the
triage (`pos_router.py:1002` — *"Nothing is written"*), so a practice run costs nothing.

> ⚠️ **These five do NOT need Enter Setup / Save and Exit.** Scan the one you want, on its own.
> (Manual: *"Das Scannen von 'Beginn der Einrichtung' oder 'Speichern und Beenden' ist für die
> Verwendung der 5 folgenden Barcodes nicht erforderlich."*)

| Barcode (naming from the Inateck PDF; check the Netum sheet for its equivalents) | Does |
|---|---|
| **Inventurmodus** | gun STORES scans instead of transmitting |
| **(*) Normalmodus** | back to live scanning — the factory default |
| **Daten hochladen** | dumps the whole cache as keystrokes into whatever has focus |
| **Daten im Cache löschen** | wipes the cache |
| **Anzahl der gescannten Barcodes hochladen** | types how many are stored |

### The workflow

**The screen that receives the dump is `/pos/shelf-intake`** — it parses the keystrokes, splits
the shelf into already-known and still-unknown, and walks you through the unknowns in batches of
ten. Full guide: [`../../09-shelf-intake.md`](../../09-shelf-intake.md).

1. Scan **Inventurmodus**. The gun stops transmitting and starts collecting.
2. Walk the shelves. Scan everything. ~20 minutes for a shop. Nothing to look at, no screen.
3. Scan **Anzahl der gescannten Barcodes** into any text field and write the number down.
4. Back at a laptop: open `/pos/shelf-intake`, type that number in, click into the big box.
5. Scan **Daten hochladen** — every code types itself out.
6. Only once the screen agrees on the count: scan **Daten im Cache löschen**, then
   **Normalmodus** to return to till use.

> **Check the count first.** Scan *Anzahl der gescannten Barcodes* before uploading, so you know
> whether the dump was complete. A half-uploaded shelf silently looks like a finished one.

### Why this beats scanning at the counter

It separates the **physical** work from the **desk** work. Capturing at the till means hunting for
each product's identity while standing in a shop with customers waiting — measured at ~5 minutes a
product. Scanning the shelf is ~2 seconds a product, and the hunting happens afterwards, batched,
with two screens and no queue behind you.

It also makes the shelf define the catalog rather than the wholesaler's list — so you end up with
what the shop actually stocks, each with the EAN that is genuinely on the packet.

---

## Other guns

Config barcodes are **vendor and model specific** — never scan one gun's codes into another. Find the model
number on the underside or in the battery compartment, then get that manufacturer's manual.

If a gun's layout list doesn't include anything workable, look for **"ALT + keypad"** / **"Unicode output"**
mode: it types by numeric code rather than key position, so it is layout-independent.

---

## Banco covers this anyway

`_find_product_by_any_barcode` (`src/routes/pos_router.py`) retries layout-corrected candidates when a
scanned code matches nothing — so `TAM'21796` still resolves to `TAM-21796`. It is a **fallback, never a
rewrite**: only tried after the raw code found nothing, so a real apostrophe can't be corrupted. A hit logs
a warning naming the correction, so a mis-set gun surfaces rather than hiding.

Fix the gun anyway. The fallback is a safety net for shops running hardware we didn't choose.


---

## The backup gun — five minutes lost, 2026-09-01, and none of it was the gun's fault

The good gun (NETUM NSL8) went flat mid-shift. Grabbing the spare — the cheap yellow Inateck
BCST-35 — took **three to five minutes** to get working, in a situation where the whole point of a
spare is that it takes ten seconds. Every step of it will happen again to somebody else.

**1 · A Bluetooth gun holds ONE pairing, and it was still paired to a phone.** The spare had last
been used with Angel's phone and reconnected to it the moment it woke. Plugging its dongle into the
tablet did nothing, and there is no message anywhere saying why. *Turning the phone's Bluetooth off
was not enough on its own* — the tablet then had to discover and pair it.

**2 · The dongle and Bluetooth are different MODES, not two routes to the same place.** With the gun
in Bluetooth mode the 2.4G dongle is inert, and vice versa. Mode is set by scanning a config
barcode from the manual (`Inateck_BCST-35_Barcode_Scanner_User_Manual-V1.2_251117.pdf`, in this
folder). A dongle sitting in a USB port is *not* evidence that the gun will use it.

**3 · ⚠️ TWO GUNS MEANS TWO OF THE SAME GUN.** Angel's own conclusion, and it is the real lesson:
*"basically, you wanna have two of exactly the same guns."* Different models mean different modes,
different pairing, different dongles and different capability — all discovered under pressure, at
the counter, in front of a customer. Two identical guns, one always charging, is one procedure
instead of two.

**4 · The cheap gun cannot read a screen.** The NETUM scans a barcode off a monitor without
complaint; the Inateck has no chance. It is around 90% as good on paper labels and noticeably worse
on the hard ones — crumpled, curved, low contrast. Good enough for a spare, not good enough to be
the only gun.

> **This kills the obvious design for a scan self-test.** A page that *displays* a barcode for the
> operator to scan works for the good gun and fails for the cheap one — and the moment you most
> need a self-test is the moment you are holding the spare. A scan test must **receive** a code,
> not display one: an empty box that says what arrived, scanned off any product on the shelf.

**5 · The cheap gun has a green light. The good one does not.** On the Inateck you can see it is
alive. The NETUM's flat battery announced itself only as a double beep and no red flash — which is
what made it read as a software fault for twenty minutes.

**Open, and it is a genuine trade:** should the tablet keep Bluetooth on permanently? It is what
makes the spare work instantly. It also drains the battery all day, on a machine whose own charge
matters more than the gun's — the gun has a spare and the tablet does not.
