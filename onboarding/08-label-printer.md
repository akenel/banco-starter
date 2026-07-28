# 8 · The label printer — Brother QL-820NWBc

**You do not need anything from Brother's website.** No driver download, no CD, no `linux-brprinter-installer`.
Debian ships everything required. This guide gets a label out of the machine and makes it survive a reboot.

Written against the **QL-820NWBc** on Debian 12, wired up 2026-07-28. Setup used in the shop: **till cabled
straight to the labeler over USB** — no network in the path.

---

## What's actually happening

```
your script  ->  lp  ->  CUPS  ->  usb:// backend  ->  USB cable  ->  printer
                              (printer-driver-ptouch)
```

Four parts, all packaged by Debian. `printer-driver-ptouch` is an open-source CUPS driver that lists the
QL-820NWB explicitly and marks it *recommended*.

> **Why not the "driverless" path?** Debian also has `ipp-usb`, which re-presents a USB printer as a network
> printer so CUPS can use its generic `everywhere` driver. It looks elegant and it *mostly* works — but its USB
> session goes stale after a few minutes and never recovers, hanging every print job. We chased that for an
> evening. See [The ipp-usb trap](#the-ipp-usb-trap). The ptouch driver has none of that, prints in ~4 s, and
> gives better controls (print density, auto-cut, continuous-tape lengths).

---

## Setup

### Step A · Install the driver and get `ipp-usb` out of the way

```bash
sudo apt install -y printer-driver-ptouch

# stop ipp-usb grabbing the printer, so CUPS's own usb:// backend can have it
sudo cp scripts/ipp-usb-quirks/Brother.conf /usr/share/ipp-usb/quirks/
sudo systemctl restart ipp-usb

# stop cups-browsed inventing phantom queues (see troubleshooting)
sudo systemctl disable --now cups-browsed
```

Check the printer is now visible to CUPS directly:

```
lpinfo -v | grep -i usb
#  -> direct usb://Brother/QL-820NWB?serial=000C6G972376
```

> ⚠️ `lsusb` shows this printer **even when it is switched off** — it keeps its USB chip alive on bus power. So
> "it appears in `lsusb`" does *not* mean it's on. Confirm the **LCD is lit**.

### Step B · Create the queue

Use *your* serial from the `lpinfo -v` line above.

```bash
lpadmin -p BancoLabel -E \
  -v "usb://Brother/QL-820NWB?serial=000C6G972376" \
  -m "ptouch:0/ppd/ptouch-driver/Brother-QL-820NWB-ptouch-ql.ppd" \
  -D "Banco label printer (QL-820NWBc, direct USB)"

lpadmin -p BancoLabel -o PageSize=62mm -o MediaType=Tape -o AutoCut=True -o PrintQuality=High
lpadmin -d BancoLabel
```

No `sudo` needed if you're in the `lpadmin` group (`id | grep lpadmin`). Verify:

```
lpstat -v      # -> device for BancoLabel: usb://Brother/QL-820NWB?serial=...
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

Or bypass the script — any PNG or PDF works:

```
lp -d BancoLabel -o PageSize=62mm -o MediaType=Tape yourlabel.png
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

Everything prints at **300 dpi** (or `300x600dpi`), monochrome. Red/black (DK-22251) is not wired up.

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

On the ptouch/direct-USB path a label takes **~3–4 s**, consistently. If you're seeing 25–60 s, you're still on
`ipp-usb` — that path re-calibrates on every wake.

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

- **`scripts/print-label.py` prints text only.** Barcodes aren't in it yet. The *web* label page
  (`/pos/products/<id>/label`) already renders a scannable EAN-13, so the gap is in the CLI tool.
- **The web label page hasn't been proven against the roll.** Its print CSS is `@page{ size:62mm auto }`, which
  should match the DK-44205, but whether Chrome and CUPS agree on `auto` is untested.
- **A remote Banco cannot print here.** `banco.wolfhold.app` runs on another machine, and no server on the
  internet can reach a USB printer on your laptop. Printing must be driven by something on the shop LAN — the
  local Banco instance, or a networked printer.
- Red/black printing (DK-22251) and P-touch Template mode are untouched.
