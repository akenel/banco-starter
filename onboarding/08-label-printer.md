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
