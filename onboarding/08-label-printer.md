# 8 · The label printer — Brother QL-820NWBc

**You do not need anything from Brother's website.** No driver download, no CD, no `linux-brprinter-installer`.
Debian ships everything required. This guide gets a label out of the machine and makes it survive a reboot.

Written against the **QL-820NWBc** on Debian 12, wired up 2026-07-28.

> ## ✅ STATUS: working over the USB cable, verified unattended
>
> Proven 2026-07-28: printer left idle **14 minutes** until `ipp-usb` went stale, then a print with **zero human
> intervention** — the script spotted the dead session, restarted the daemon, and the label came out. Confirmed
> by hand, LED green.
>
> **The one flaw, and its fix.** `ipp-usb`'s USB session dies after roughly **6–11 minutes** idle and never
> re-opens. Jobs then hang forever at "now printing" while the printer sits there lit and `READY` — which looks
> exactly like a sleeping printer and is not. `print-label.py` now checks before every job and restarts the
> daemon when needed. Not elegant; it works, and it says what it is doing.
>
> **Dead ends — don't re-walk these:**
>
> | Tried | Result |
> |---|---|
> | `printer-driver-ptouch` 1.6 (direct `usb://`) | **Zero labels.** Every job → *"Wrong roll type — check the print data"*, across all four `MediaType` × `PageSize` combinations. Lists the QL-820NWB as *recommended*; does not drive it. |
> | `brother_ql` 0.9.4 (raw raster via pyusb) | Same rejection. |
> | `brother_ql_next` 0.12.0 (raw raster) | Same rejection. |
>
> Every **raw-raster** path was rejected; only the printer's own **IPP** service accepts jobs. Why is not
> understood. It is *not* the media settings — the printer's own status bytes over raw USB (`ESC i S`) report
> `62mm`, type `0x0a` continuous, no error bits: exactly what every rejected job declared.
>
> Also chased and found innocent: **Auto Power Off** (a blanked LCD is burn-in protection, not standby) and the
> roll type.

---

## If you're picking this up cold

Written down deliberately, because most of it cost hours to learn and none of it is guessable. If you're the
next person — or Angel in six months — this is the part that saves you the day we spent.

**Five faults, and what each one looked like.** Every single one *looked like* a broken printer. None was.

| Symptom | Actual cause |
|---|---|
| Jobs queue, "now printing", nothing comes out, LED green | `ipp-usb`'s USB session went stale. Restart the daemon; don't touch the printer. |
| Printed nothing, no error, clean CUPS drain | Browser rendered the label onto **A4** — `@page{ size: 62mm auto }` is invalid CSS and silently falls back. |
| Some jobs vanish entirely | `cups-browsed`'s phantom queue accepts jobs then swallows them. Disable it. |
| Label prints but won't scan | Barcode below the size a scanner can resolve. Small labels need a QR, not an EAN-13. |
| Product not found when scanning a SKU | Scanner gun's keyboard layout ≠ session's. `-` arrives as `'`. |

**The four habits that actually solved them:**

1. **"The queue drained" ≠ "a label came out."** The printer accepts data in ~3 s and rejects it afterwards.
   A clean `lpstat` proves nothing. Only a human holding the label proves it.
2. **Read the device's own status before touching settings.** `ESC i S` over raw USB returns media width, type
   and error bits. One read ended hours of guessing between roll types — and showed the settings had been
   right the whole time.
3. **When a browser print does nothing, save it as a PDF and run `pdfinfo`.** It shows what the browser
   *actually* decided. `Page size: 594.96 x 841.92 pts (A4)` ended a three-hour hunt in one command.
4. **Test with something that can reveal the fault.** The scanner keyboard bug only surfaced because the test
   codes contained hyphens. Numeric test codes would have passed clean and shipped the bug to the shop.

**And one that cost the most time:** the vendor-specific driver is not automatically the better bet. Three
Brother-specific drivers printed **zero** labels; the generic CUPS/IPP path worked. Prefer the path with
verified output over the one that looks more purpose-built.

---

## Which machine does what (read this first)

The single most confusing thing about printing here: **Banco runs on a server, but printing happens on the till.**

```
        SERVER  (Hetzner, banco.wolfhold.app)          TILL  (the counter machine)
        ├── banco-app      ← builds the label page     ├── Brother QL  ← USB cable
        ├── postgres                                   ├── ipp-usb     ← USB → IPP bridge
        ├── keycloak            ...sends HTML...       ├── CUPS        ← the BancoLabel queue
        └── caddy              ─────────────────►      └── browser     ← presses Print
                                                            │
                                                            ▼
                                                        the label
```

When a cashier taps **🏷️ Label → Print**, the *page* came from the server, but every step after that happens on
the till: browser → CUPS → `ipp-usb` → USB cable → printer. **The server never touches the printer** and has no
idea one exists.

So printer setup is **per-till machine setup**, not part of the app:

| | Where it lives | Survives a deploy? |
|---|---|---|
| Banco app code | server | replaced every deploy |
| CUPS queue `BancoLabel` | **till**, `/etc/cups` | ✅ |
| `ipp-usb` + keepalive timer | **till**, `/etc/systemd/system` | ✅ |
| sudoers rule | **till**, `/etc/sudoers.d` | ✅ |
| `/opt/banco/label-printer-keepalive.sh` | **till**, `/opt` | ✅ |

**You never re-run the printer setup after a deploy.** Once per till, then forget it.

---

## Setting up a new till (the back-office desktop, a second counter, anything)

Do this on the machine **with the USB cable plugged into the printer**. Takes about ten minutes.

1. **Plug in and switch on.** Wait for the LCD to light. Confirm Debian sees it:
   ```
   lsusb | grep -i brother      # → ID 04f9:209d ... QL-820NWB
   ```
2. **Add yourself to `lpadmin`** if you aren't already (`id | grep lpadmin`), then log out and back in.
3. **Kill `cups-browsed`** — it invents a phantom queue that silently eats jobs:
   ```
   sudo systemctl disable --now cups-browsed
   ```
4. **Create the queue** (Step B below). Keep the name `BancoLabel` — the scripts and the print dialog expect it.
5. **Install the keepalive** (Step A2 below):
   ```
   sudo ./scripts/install-label-keepalive.sh
   ```
6. **Prove it.** Print one from the browser, then leave it half an hour and print again *cold*. The second one is
   the real test — that's what used to fail.

That's the whole thing. Nothing to repeat, nothing tied to a release.

---

## Other ways to print (phones, the back office, several counters)

**USB is right for one dedicated till.** It's what this guide sets up: simple, no network, nothing to configure
on the printer. The cost is `ipp-usb` and the keepalive timer that babysits it.

**For anything else, put the printer on the shop network.** The QL-820NW**B** has Ethernet, Wi-Fi *and* Bluetooth
built in. On the LAN it becomes an ordinary network printer, and a lot of problems simply stop existing:

- **No `ipp-usb`** — so **no keepalive needed either**. That entire class of failure is a USB-bridge problem; it
  doesn't exist over the network.
- **Any machine can print** — back office, second counter, laptop — each just adds a queue pointing at its IP.
- **Phones work natively.** The printer speaks IPP, so iPhones print via **AirPrint** and Androids via the
  built-in **Mopria/Default Print Service**, with no app and no Banco changes. Open the label page on a phone,
  tap Print, done.

Setting it up: join Wi-Fi (or plug in Ethernet) from the printer's own web UI — reachable over the USB cable at
`http://localhost:60000/` before you unplug it. Then on each machine:

```
lpadmin -p BancoLabel -E -v "ipp://192.168.x.240/ipp/print" -m everywhere
```

Two cautions:
- **Give the printer a static IP** (set on the printer itself, e.g. `.240`). Without it a DHCP lease change
  silently breaks every queue — and on a router you don't control you can't make a reservation.
- **Not a guest network or a phone hotspot.** Both usually isolate clients: devices get internet but can't see
  each other, and printing fails with no useful error.

**Bluetooth** is paired and works, but it's the weakest option for a till: it's a serial link with no CUPS
backend on Linux, so Banco can't drive it — you'd be printing from Brother's own mobile app, not from Banco.
Fine as a phone-in-your-hand fallback; not a counter solution.

> **Recommendation:** USB for the one machine that lives at the till. Network the moment a second device needs to
> print — it's less setup than doing USB twice, and it retires the keepalive entirely.

---

## Setting up a Windows till

> ⚠️ **Untested as of 2026-07-29** — written from the Windows/Brother documentation, not yet run on a real
> machine. Correct this section the first time you do it for real.

Windows is **simpler than Linux here, and backwards in one way**: on Linux you need nothing from Brother, on
Windows you need their driver. But none of the `ipp-usb` complexity exists — no `ipp-usb`, no `cups-browsed`, no
keepalive timer. **Those are Linux daemons. Skip all of it.** Windows drives the printer directly through
Brother's driver and its own spooler.

### Step 1 · Install Brother's driver (before plugging in)

Go to **support.brother.com** → search **QL-820NWB** → **Downloads** → pick your Windows version → install the
**Printer Driver** (the "Full Software Package" also gives you P-touch Editor, which you don't need for Banco).

Install the driver **first**, then plug in the USB cable. Windows otherwise grabs it with a generic driver you'll
have to unpick.

### Step 2 · Set the label size as the printer's default

This is the step people miss, and it's the one that produces blank or clipped labels.

**Settings → Bluetooth & devices → Printers & scanners → Brother QL-820NWB → Printing preferences**

- **Paper Size:** the roll that's loaded — `62mm` for continuous DK-22205/DK-44205
- **Quality:** 300 × 300 dpi
- **Auto Cut:** on, cut after each label

Set it here, not just in the browser — this is the default every app inherits.

### Step 3 · Print from Banco

Open a product → **🏷️ Label** → **Print** → destination **Brother QL-820NWB**. Same as Linux from here.

The `@page` CSS fix that makes the label render at roll size instead of A4 is server-side and already deployed,
so it applies to Windows automatically.

### PowerShell, if you want it

None of this is required — the GUI does everything. But for checking and unsticking, in an **admin** PowerShell:

```powershell
Get-Printer | Format-Table Name, DriverName, PortName    # is it installed?
Get-PrintJob -PrinterName "Brother QL-820NWB"            # what's queued?
Get-PrintJob -PrinterName "Brother QL-820NWB" | Remove-PrintJob   # clear a jam
Restart-Service -Name Spooler -Force                     # the "have you tried" of Windows printing
```

`Restart-Service Spooler` is the Windows analogue of our `systemctl restart ipp-usb` — the thing to try when jobs
queue and nothing comes out.

### What does NOT apply on Windows

- `install-label-keepalive.sh`, the systemd timer, the sudoers rule — **Linux only**
- `cups-browsed`, `ipp-usb`, `lpadmin`, `lpstat` — **Linux only**
- `scripts/print-label.py` — needs Python + CUPS; the browser path is the Windows route

### If it's a shared back-office machine

Rather than USB per machine, consider putting the printer on the shop LAN (see the section above). Windows adds a
network printer in a couple of clicks, phones then print via AirPrint/Mopria, and you stop maintaining printer
setup on every desktop.

---

## What's actually happening

```
your script  ->  lp  ->  CUPS  ->  ipp-usb  ->  USB cable  ->  printer
                          (everywhere driver)
```

All standard parts, all packaged by Debian — nothing proprietary. `ipp-usb` re-presents the USB printer as a
network printer on `localhost:60000`, and CUPS drives it with its built-in `everywhere` driver at 300 dpi.

---

## Setup

### Step A · Install and make it self-healing

```bash
# stop cups-browsed inventing phantom queues (see troubleshooting — this one bites)
sudo systemctl disable --now cups-browsed

# let the till restart ipp-usb without a password, so it can heal itself mid-shift
sudo cp scripts/sudoers/banco-label-printer /etc/sudoers.d/banco-label-printer
sudo chmod 0440 /etc/sudoers.d/banco-label-printer
sudo visudo -c          # must print "parsed OK"
```

The sudoers rule grants **exactly two commands** — `systemctl restart ipp-usb` and `systemctl kill ipp-usb` — no
wildcards, no shell. Edit the username in it if the till user isn't `angel`.

> Without this rule the script still prints; it just can't recover a stale `ipp-usb` on its own, and someone has
> to type a root password at the counter. That's not a thing that can happen with a customer waiting.

### Step A2 · Install the keepalive (do this, or the browser's Print button will randomly do nothing)

```bash
sudo ./scripts/install-label-keepalive.sh
```

`ipp-usb`'s USB session dies after **6–13 minutes idle** and never re-opens. Jobs then queue silently and nothing
comes out. `print-label.py` heals itself before printing — **a browser can't**: `window.print()` has no way to
restart a daemon, and an HTTPS page can't even reach `http://localhost`. So the till's Print button needs the
printer already awake.

The installed timer pokes it every 60 s with a status query. Since the failure is an *idle* timeout, that traffic
should stop it going stale at all; a restart is the fallback, not the mechanism.

> ### ⚠️ Run this on the TILL, not the server
>
> ```
> server (Banco app)          till (this machine)
> ├── banco-app               ├── Brother QL  ← USB cable
> ├── postgres                ├── ipp-usb
> └── caddy                   ├── CUPS / BancoLabel
>      ↑                      └── browser
>   serves the HTML                ↑
>                          does the actual printing
> ```
>
> Banco's pages come from the server, but printing happens **entirely on the till**. The server has no printer.
>
> **This is machine setup, not application code.** It installs into `/etc` and `/opt`, so it survives `git pull`,
> redeploys, reboots and power cuts. Run it **once per till** — never again after a deploy.

Check the printer is answering. Switch it on and wait for the **LCD to light**, then:

```
ipptool -tv ipp://localhost:60000/ipp/print \
  /usr/share/cups/ipptool/get-printer-attributes.test | grep -E "printer-state \(|make-and-model"
```

| What you see | Meaning |
|---|---|
| `printer-state (enum) = idle` + a model name | ✅ relaying properly |
| `RECEIVED: 0 bytes in response` | ❌ stale session — `sudo systemctl restart ipp-usb` |

> ⚠️ `lsusb` shows this printer **even when it is switched off** — it keeps its USB chip alive on bus power. So
> "it appears in `lsusb`" does *not* mean it's on. Confirm the **LCD is lit**.

### Step B · Create the queue

`cups-browsed` auto-creates a queue, but it's **temporary and vanishes**, and it rots into a disabled state that
silently swallows jobs. Step A disabled that daemon. Make your own permanent queue:

```bash
lpadmin -p BancoLabel -E -v "ipp://localhost:60000/ipp/print" -m everywhere \
  -D "Banco label printer (QL-820NWBc)" -L "Shop counter"

lpadmin -p BancoLabel -o CutMedia=EndOfPage
lpadmin -d BancoLabel
```

No `sudo` needed if you're in the `lpadmin` group (`id | grep lpadmin`). Verify:

```
lpstat -v      # -> device for BancoLabel: ipp://localhost:60000/ipp/print
```

The name `BancoLabel` is what the scripts use. Keep it.

### Step C · Print

```bash
python3 scripts/print-label.py "BANCO" "Espresso Beans 250g" "CHF 12.50"
```

First line is the headline, the rest step down. Text auto-shrinks to fit, so it can't silently print chopped off.

```bash
python3 scripts/print-label.py --status                    # is the printer OK?
python3 scripts/print-label.py --clear                     # unstick a jammed queue
python3 scripts/print-label.py --list-media                # what rolls are known
python3 scripts/print-label.py --dry-run --out /tmp/x.png "Check me"
python3 scripts/print-label.py -n 20 "Sale"                # 20 copies
python3 scripts/print-label.py -l 40 "Short one"           # 40mm long on continuous tape
python3 scripts/print-label.py -m 29x90 "Die-cut"          # a different roll
```

### Shelf labels with a barcode

```bash
python3 scripts/print-label.py -c 2000000217963 "Curaprox Zahnpasta CBD" "CHF 14.90" "TAM-21796"
```

`-c` / `--barcode` picks the symbology from the code itself:

| Code | Symbology |
|---|---|
| 13 digits | **EAN-13** (check digit verified) |
| 12 digits | **EAN-13** (check digit computed for you) |
| anything else | **Code128** — internal SKUs like `TAM-21796` |

The barcode gets reserved space *before* the text is laid out, so shrinking text can never encroach on it — an
unscannable barcode defeats the point of the label. It's capped at half the label height, and the spec's quiet
zone is preserved. If there genuinely isn't room, the script refuses rather than printing something that won't
scan:

```
No room for text and a barcode on 62x12mm.  Try a longer --length.
```

> **62 mm matters here.** An EAN-13 needs roughly 31 mm at 80% magnification before scanners start to struggle.
> On a 29 mm roll you cannot print a reliable EAN-13 across the width — which is why the shop roll is 62 mm.

### The two label sizes, and why Small is a QR

From the web UI you pick **Small** or **Medium**. They are not the same label shrunk — they carry different
codes, for a physical reason.

| | Small | Medium |
|---|---|---|
| Page | 62 × 24 mm | 62 × 55 mm |
| Code | **QR, 15 mm**, logo in the middle | **EAN-13**, 14 mm bars |
| Layout | QR left, price right | stacked, shelf-talker |
| For | price stickers on the item | shelf edges |

**Why Small can't use a barcode.** EAN-13 needs ~31 mm of width *and* ~23 mm of bar height to scan reliably.
A price sticker has neither. Our first attempt was 38 mm wide with 9 mm bars and **neither scanner gun in the
shop could read it** — it looked perfect on screen and was useless on the tin.

QR fixes it three ways: two-dimensional so the same 13 digits fit in a fraction of the area; Reed–Solomon
error correction, which a linear barcode has none of, so it survives being small, smudged or stuck on a curve;
and it reads from any angle.

**Measured against both guns 2026-07-29:** readable down to **10 mm**. We print at 15 mm for margin.

**The logo** comes from `receipt_logo_url` in store settings — per-shop, no hardcoding. When a logo is present
the error correction steps up from **M (~15% recoverable) to H (~30%)**, because we're punching a hole in the
middle of the code. The logo covers 22% of the width — about 5% of the area, well inside H's budget — on a
white plate so the scanner sees a clean edge instead of reading the logo as data.

> Tested at 12/15/20 mm and with an oversized 30% logo: **zero failures across 48 scans, both guns.**
> Evidence in `onboarding/testsheets/LOGO-QR-SCAN-TEST.html`.

### Printing from Banco's web UI

Open a product → **🏷️ Label** → **Print**, destination `BancoLabel`. Works from any browser on a machine that has
the printer — including against a Banco served from another host, because browser printing is client-side.

Two things had to be true before this worked, and both cost an evening:

**1. `@page` must declare BOTH lengths.** This looks fine and is invalid CSS:

```css
@page{ size: 62mm auto; }     /* ✗ INVALID — silently falls back to A4 */
@page{ size: 62mm 55mm; }     /* ✓ */
```

The spec allows `auto` OR one/two lengths — never a length combined with `auto`. Browsers drop the whole
declaration and default to **A4**, so the label renders in the corner of a sheet and the QL discards the job:
no error, clean CUPS drain, green LED, nothing printed. Chrome's own *Save as PDF* is what exposed it —
`pdfinfo` showed `Page size: 594.96 x 841.92 pts (A4)`.

> **When a browser print does nothing, save it as a PDF and run `pdfinfo` on it.** It shows you exactly what the
> browser decided, instead of what you assumed it decided.

**2. Hard-refresh after changing that CSS.** The styles are inline in the template, so a cached *page* carries the
old rule with it. `Ctrl+Shift+R`, or test in a private window. We chased a fix that was already deployed because
Chrome kept serving the old page.

Once both hold, any of the ~20 sizes in the print dialog work.

Or bypass the script — any PNG or PDF works:

```
lp -d BancoLabel -o media=Custom.62x60mm -o CutMedia=EndOfPage yourlabel.png
```

---


### Waste and the cutter — the two things a shop owner will notice

**Wasted tape.** On continuous roll the paper size's LENGTH is what feeds. If `@page` says 62×28mm but the print
dialog is on `29x62mm` or `62x100mm`, the printer advances 62mm or 100mm for a 28mm label — two to four times
the tape, every label. On a shop's stock that adds up fast, and it is the first thing an owner who wastes
nothing will point at.

Fix it once per till, on the queue, so nobody has to remember a dropdown:

```bash
lpadmin  -p BancoLabel -o media-default=Custom.62x28mm
lpoptions -p BancoLabel -o media=Custom.62x28mm
lpoptions -p BancoLabel | tr ' ' '\n' | grep -i media     # confirm it took
```

The driverless PPD accepts `Custom.WIDTHxHEIGHT`, so match the label exactly. Roll length per label then equals
the label, not a preset.

**Having to press the cutter button after every label** means auto-cut is not applying:

```bash
lpadmin  -p BancoLabel -o CutMedia=EndOfPage
lpoptions -p BancoLabel -o CutMedia=EndOfPage
lpoptions -p BancoLabel -l | grep -i cut                   # want *EndOfPage
```

| Setting | Cuts | Use when |
|---|---|---|
| `EndOfPage` | after every label | one at a time at the counter |
| `EndOfJob` | once, at the end | printing a batch — leaves a strip to tear |
| `None` | never | you cut by hand |

> The small label prints a thin border. That is a **cut guide**: continuous tape has no die line, so without an
> edge you are guessing with scissors.

## The other half: the scanner guns

Printing a label is only half the loop — something has to read it back. Full setup, and one trap that will
cost you a day if you meet it cold, in **[`testsheets/Scanners/README.md`](testsheets/Scanners/README.md)**.

The short version:

- **A scanner gun is a keyboard.** It presses the *key* that yields a character on **its** layout; the OS
  reads that key through **the session's** layout. Mismatch them and punctuation mutates.
- Both our guns shipped set to **US**. On a Swiss German session that turns `-` into `'`, so `TAM-21796`
  arrives as `TAM'21796` and the product isn't found.
- **It hides for weeks**, because EAN-13 is pure digits and digits are layout-independent. Till scanning
  looks perfect while every SKU silently fails.
- Fix: set both guns to **German** (Swiss German usually isn't offered; German puts `-` on the same key).
- Verify with **[`testsheets/SCANNER-GUN-TEST.html`](testsheets/SCANNER-GUN-TEST.html)** — every test code
  names its own size, so you also learn the smallest code your gun can read.

> Banco has a safety net for this: a scanned code that matches nothing is retried with layout corrections
> applied (`_find_product_by_any_barcode`). It's a **fallback, never a rewrite** — only tried after the raw
> code found nothing — and a hit logs a warning so a mis-set gun surfaces instead of hiding. Fix the gun
> anyway; the net is for shops running hardware we didn't choose.

## Rolls

The shop runs **DK-44205** — 62 mm × 30.48 m **continuous**, removable adhesive. 62 mm is the printer's full
print width, which matters: an EAN-13 needs ~31 mm to scan reliably, so narrow rolls squeeze barcodes below
usable magnification.

**Continuous vs die-cut** is the distinction that matters:

| | Length | Set with |
|---|---|---|
| **Continuous** (`62`, `29`, `38`, `50`, `54`, `12`) | you choose | `--length 60` |
| **Die-cut** (`29x90`, `62x100`, `17x54`, …) | fixed by the die | — |

The DK-11201 (29 × 90 mm die-cut) in the box is an *address label* roll — fine for testing, wrong shape for a
price sticker.

- **DK-44205** = removable adhesive. Peels clean; right for prices that change.
- **DK-22205** = same 62 mm tape, permanent adhesive. For labels that must stay stuck.

The printer auto-detects the roll type from a sensor on the spool — no menu setting when you swap.

Everything prints at **300 dpi**, monochrome. Red/black (DK-22251) is not wired up.

---

## Printer settings that matter

Set these on the printer, via its LCD menu or web UI:

| Setting | Set to | Why |
|---|---|---|
| **Command Mode** | **Raster** | Required for printing from a computer. `P-touch Template` is for *standalone* use with a barcode scanner and is the wrong mode here. |
| Auto Power Off (AC/DC) | **Off** | Defaults to **20 min**. A till printer must never nap. |
| Auto Power Off (Li-ion) | **Off** | Only with the battery pack fitted, but set it anyway. |
| Auto Power On | **Enable** | Comes back by itself after a power cut. |

> **The web UI is gone once you blacklist `ipp-usb`.** `http://localhost:60000/` was only ever `ipp-usb`
> forwarding the printer's page over the cable. Set these *before* Step A, or comment out the blacklist line in
> the quirk file and restart `ipp-usb` to get it back temporarily. On a networked printer it's at its own IP.

---

## Troubleshooting

### Nothing prints and nothing complains

```bash
python3 scripts/print-label.py --status     # where are jobs stuck? is it awake?
python3 scripts/print-label.py --clear      # cancel everything, re-enable
```

The classic cause is the **phantom queue**. `cups-browsed` auto-creates `Brother_QL_820NWB_USB`, which rots into:

```
printer Brother_QL_820NWB_USB disabled since ... -
    No destination host name supplied by cups-browsed for printer ..., is cups-browsed running?
```

A **disabled queue still accepts jobs and silently swallows them** — they pile up where you aren't looking, and
GUI print dialogs love picking it because the name sounds right. Deleting it doesn't help; `cups-browsed`
recreates it within seconds. Kill the daemon:

```bash
sudo systemctl disable --now cups-browsed
lpadmin -x Brother_QL_820NWB_USB
```

Then `lpstat -v` shows **only** `BancoLabel`, and nothing can misroute a job again.

### The ipp-usb trap

*Only relevant if you're still on the `ipp-usb` path — Step A removes it.* Symptoms:

- The LCD is lit and the printer says `READY` — it is **not** asleep
- Every IPP request returns `RECEIVED: 0 bytes`
- `http://localhost:60000/` is a **blank white page**
- Jobs queue, say "now printing", and hang forever

The printer is fine; `ipp-usb`'s USB session died and it never re-opens it.

```bash
sudo systemctl restart ipp-usb        # revives it instantly
```

**The diagnostic:** restart `ipp-usb` *without touching the printer*. If it comes back, the printer was awake all
along. Don't start with the printer's power settings — a blanked LCD (burn-in protection) plus a blinking LED
looks exactly like standby and will send you down the wrong path for an hour.

> Hangs in `deactivating`? `sudo systemctl kill -s KILL ipp-usb && sudo systemctl restart ipp-usb`

### Timing

Measured on this machine:

| | Time |
|---|---|
| First job after `ipp-usb` restarts, or after a long idle | ~25–55 s (roll calibration) |
| Jobs after that | ~4 s |

A slow first label is **not** a stuck queue. Give it a full minute before you believe it's wedged — we cancelled
several perfectly good jobs at 10 seconds and went hunting for bugs that weren't there.

### Job stuck, queue goes `stopped`

```bash
cancel -a BancoLabel && cupsenable BancoLabel
```

---

## If you'd rather use the network

The QL-820NW**B** has Ethernet and Wi-Fi built in. Direct USB is simpler and is what the shop runs, but network
suits multiple tills:

```
lpadmin -p BancoLabel -E -v "ipp://192.168.x.240/ipp/print" -m everywhere
```

- You only need the **SSID and password** — no router admin access. Configure Wi-Fi from the printer's web UI
  over the USB cable before unplugging.
- **Not a guest network or a phone hotspot.** Both usually have client isolation: devices get internet but can't
  see each other, and printing silently fails.
- **Set a static IP on the printer itself** (e.g. `.240`, high in the range). Without a DHCP reservation the
  address can change and the queue breaks silently — and on someone else's router you can't make one.

---

## Known gaps

- **Barcodes print and scan** — verified 2026-07-28 with the shop's own scanner: a printed 62 mm label read back
  `2000000217963` cleanly. Note that Banco then failed to *resolve* that code to the product (catalog search
  didn't filter, the sale screen didn't add it) — that's an app-side lookup bug, not a printing one. See
  `WORKLIST.md`.
- **The web label page hasn't been proven against the roll.** Its print CSS is `@page{ size:62mm auto }`, which
  should match the DK-44205, but whether Chrome and CUPS agree on `auto` is untested.
- **A remote Banco cannot print here.** `banco.wolfhold.app` runs on another machine, and no server on the
  internet can reach a USB printer on your laptop. Printing must be driven by something on the shop LAN — the
  local Banco instance, or a networked printer.
- Red/black printing (DK-22251) and P-touch Template mode are untouched.
