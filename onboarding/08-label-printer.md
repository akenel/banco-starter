# 8 · The label printer — Brother QL-820NWBc

**You do not need anything from Brother's website.** No driver download, no CD, no `linux-brprinter-installer`.
Debian already ships everything required. This guide gets a label out of the machine in about five minutes, then
makes it permanent so it still works after a reboot.

Written against the **QL-820NWBc** on Debian 12, first wired up 2026-07-28.

---

## What's actually happening (the 30-second version)

Most people assume a printer needs a vendor driver. This one doesn't, because it speaks **IPP** — the same
standard protocol AirPrint uses. Debian has a daemon called **`ipp-usb`** that finds the printer on USB, and
re-presents it to the system as if it were a network printer on `localhost:60000`. CUPS then drives it with its
built-in `everywhere` driver.

```
your script  ->  lp  ->  CUPS  ->  ipp-usb (localhost:60000)  ->  USB cable  ->  printer
```

So the chain is all standard parts. Nothing proprietary anywhere in it.

---

## Step A · Check the machine already sees it

Plug in the USB cable, switch the printer on, wait for the **LCD to light up**, then:

```
lsusb | grep -i brother
```

You want a line like:

```
Bus 003 Device 004: ID 04f9:209d Brother Industries, Ltd QL-820NWB Label Printer
```

> ⚠️ **The big gotcha, learned the hard way.** `lsusb` shows this printer **even when it is switched off**. It
> keeps its USB chip alive on bus power. So seeing it here does *not* mean it's on. Always confirm the **LCD is
> lit**. Most "it won't print" mysteries are just a dark screen.

Now confirm the printer is actually *answering*:

```
ipptool -tv ipp://localhost:60000/ipp/print /usr/share/cups/ipptool/get-printer-attributes.test | grep -E "printer-state \(|make-and-model|media-default"
```

| What you see | What it means |
|---|---|
| `RECEIVED: 0 bytes in response` | ❌ Printer is **off or asleep**. Nothing else will work. |
| `printer-state (enum) = idle` + a model name | ✅ It's awake and talking. |

If you get `0 bytes`, switch the printer on and restart the daemon:

```
sudo systemctl restart ipp-usb
```

> If `ipp-usb` hangs in `deactivating`, it's blocked waiting on a printer that never answers. Force it:
> `sudo systemctl kill -s KILL ipp-usb; sudo systemctl restart ipp-usb`

---

## Step B · Create a permanent queue

CUPS auto-creates a queue for the printer, but it's a **temporary** one made by `cups-browsed` — it appears and
**vanishes** on its own. We watched it disappear mid-session. That's useless for a shop, so make your own:

```
lpadmin -p BancoLabel -E -v "ipp://localhost:60000/ipp/print" -m everywhere -D "Banco label printer (QL-820NWBc)"
lpadmin -p BancoLabel -o PageSize=29x90mm -o CutMedia=EndOfPage
lpadmin -d BancoLabel
```

You do **not** need `sudo` for this if your user is in the `lpadmin` group (`id | grep lpadmin`). Check it stuck:

```
lpstat -v          # -> device for BancoLabel: ipp://localhost:60000/ipp/print
```

The name `BancoLabel` is what the scripts use. Keep it.

---

## Step C · Print a label

```
python3 scripts/print-label.py "BANCO" "Espresso Beans 250g" "CHF 12.50"
```

First line is the headline, the rest step down in size. Text auto-shrinks to fit, so it can't silently print
chopped off. Other things it does:

```
python3 scripts/print-label.py --status                      # is the printer OK?
python3 scripts/print-label.py --clear                       # unstick a jammed queue
python3 scripts/print-label.py --list-media                  # what label sizes exist
python3 scripts/print-label.py --dry-run --out /tmp/x.png "Check me"   # render, don't print
python3 scripts/print-label.py -n 20 "Sale"                  # 20 copies
python3 scripts/print-label.py -m 62x100 "Big one"           # different roll
```

Or bypass the script entirely — any PNG or PDF works:

```
lp -d BancoLabel -o media=29x90mm -o CutMedia=EndOfPage yourlabel.png
```

---

## Label sizes

The roll in the box is **DK-11201, 29 × 90 mm**. The printer reports which roll is loaded — you don't have to
guess:

```
curl -sL http://127.0.0.1:60000/ | grep -o "Media Type.*" | head -1
```

Supported die-cut sizes: `12x12 17x54 17x87 23x23 24x24 29x42 29x52 29x54 29x62 29x90 38x90 39x48 58x58 60x86
62x100`, plus custom. Everything prints at **300 dpi**, monochrome.

> **Red printing** (DK-22251 black/red roll) is *not* available through this path — CUPS driverless only offers
> `ColorModel=Gray`. Red needs Brother's raster protocol. Not wired up; not needed yet.

---

## The printer's own web page

Nice trick: `ipp-usb` also forwards the printer's built-in web interface **over the USB cable**. Open:

```
http://127.0.0.1:60000/
```

> ⚠️ **Use `127.0.0.1`, not `localhost`.** On this machine `localhost` resolves to IPv6 `::1` first, but `ipp-usb`
> listens on **IPv4 only** (`ss -ltn 'sport = :60000'` shows `*:60000`). A browser pointed at `localhost:60000`
> just **spins forever** with no error. Check with `getent ahosts localhost` — if `::1` is the first line, that's
> your answer.
>
> If it still hangs on `127.0.0.1`, the printer is **asleep**. Wake it and retry.

You get live device status, media type, and all the printer's settings — network, Bluetooth, power. The config
pages want a password; it's printed **on the back of the machine, marked "Pwd"**. Change it if you ever put this
printer on the shop network.

---

## Troubleshooting

**⚠️ Read this one first: `ipp-usb` goes stale after a few minutes.**

This is the single biggest gotcha on the USB path, and it wasted an evening. Symptom:

- The printer's LCD is lit and it says `READY` — it is **not** asleep
- Every IPP request returns `RECEIVED: 0 bytes`
- `http://localhost:60000/` is a **blank white page**
- Print jobs queue, say "now printing", and hang forever

The printer is fine. **`ipp-usb`'s USB session has died and it doesn't re-open it.** The fix takes one command
and does *not* involve touching the printer:

```
sudo systemctl restart ipp-usb
```

**The diagnostic that proves it:** restart `ipp-usb` *without pressing anything on the printer*. If it springs
back to life, the printer was awake the whole time and `ipp-usb` was the fault. Don't go hunting through the
printer's power settings first — that's the wrong tree, and it looks convincing because the LCD blanks for
burn-in and the LED blinks, which reads exactly like standby.

> If `ipp-usb` hangs in `deactivating`: `sudo systemctl kill -s KILL ipp-usb && sudo systemctl restart ipp-usb`

**Worth trying:** the quirk in `scripts/ipp-usb-quirks/Brother.conf` forces a fresh connection per request
instead of reusing a stale one. Install it with:

```
sudo cp scripts/ipp-usb-quirks/Brother.conf /usr/share/ipp-usb/quirks/
sudo systemctl restart ipp-usb
```

**The real fix is to stop using USB.** See "Put it on the network" below — that removes `ipp-usb` from the chain
entirely, and with it this entire class of failure.

**Nothing prints and nothing complains. Where did my labels go?**

```
python3 scripts/print-label.py --status     # where are they stuck?
python3 scripts/print-label.py --clear      # cancel everything, re-enable
```

The usual cause: the job went to **`Brother_QL_820NWB_USB`** (the temporary `cups-browsed` queue) instead of
`BancoLabel`. That queue rots into this state —

```
printer Brother_QL_820NWB_USB disabled since ... -
    No destination host name supplied by cups-browsed for printer ..., is cups-browsed running?
```

— and a **disabled queue accepts jobs and silently swallows them**. They pile up where you aren't looking. Print
dialogs in GUI apps love picking it because it sounds like the real printer.

**Kill the phantom queue for good.** Deleting it doesn't work — `cups-browsed` recreates it within seconds. You
have to stop the daemon that makes it. You don't need it: it exists to auto-discover *shared network* printers,
and `BancoLabel` is a permanent local queue.

```
sudo systemctl disable --now cups-browsed
lpadmin -x Brother_QL_820NWB_USB
```

Then `lpstat -v` should show **only** `BancoLabel`.

**Nothing comes out, job sits in the queue, then the queue goes `stopped`.**
The printer is off or asleep. This is the #1 cause by a wide margin. Confirm the LCD is lit, then:

```
cancel -a BancoLabel && cupsenable BancoLabel
```

**The first label takes ages, then the rest are instant. Is it stuck?**
No — that's normal. The printer re-calibrates the roll when it wakes. Measured on this machine:

| | Time |
|---|---|
| First job after waking | ~25–30 s |
| Every job after that | ~4 s |

Don't cancel it at 10 seconds like we did. Give the first one a full minute before you believe it's wedged.

**It printed fine, then stopped a few minutes later.**
Auto Power Off. On the printer: **Menu → Settings → Auto Power Off** → set **AC Adapter** to **Off**. If you're
running on the Li-ion battery pack, set that one too — it naps much sooner. A till printer must never sleep.

**The queue disappeared.**
That was the temporary `cups-browsed` queue, not yours. Redo Step B; `BancoLabel` is permanent.

**Check everything at once.**

```
python3 scripts/print-label.py --status
```

---

## Put it on the network (the recommended setup)

The QL-820NW**B** has Ethernet and Wi-Fi built in. Using them removes `ipp-usb` — the most fragile piece in the
whole chain — and with it the stale-session hang above.

```
CUPS  ->  ipp://192.168.x.x/ipp/print      (no ipp-usb, no USB cable)
```

Why it's worth doing:

- **No `ipp-usb`**, so no stale sessions, no daemon restarts, no blank pages
- **Not tethered to one laptop** — any till on the shop LAN prints; close the lid and go home
- The printer's web UI is reachable at its **own IP**, which is a far saner place to manage it

Setup notes:

- You only need the **SSID and password** to join a printer to Wi-Fi — no router admin access required. You can
  configure Wi-Fi from the printer's web UI *over the USB cable* before you unplug it.
- **Don't use a guest network or a phone hotspot.** Both usually have client isolation, which lets devices reach
  the internet but not each other — printing silently fails.
- **Set a static IP on the printer itself** (e.g. `192.168.x.240`, high in the range) rather than relying on a
  DHCP reservation. Without it the address can change on a lease renewal and the queue breaks silently — and if
  it isn't your router, you can't make a reservation anyway.

Then re-point the queue:

```
lpadmin -p BancoLabel -E -v "ipp://192.168.x.240/ipp/print" -m everywhere
```

## Power settings

Set these in the printer's web UI under **Power Settings** (the LCD menu does *not* reliably hold them):

| Setting | Set to | Why |
|---|---|---|
| Auto Power Off (AC/DC) | **Off** | Default is 20 min. A till printer must never nap. |
| Auto Power Off (Li-ion) | **Off** | Only matters with the battery pack, but set it anyway. |
| Auto Power On | **Enable** | Comes back by itself after a power cut. |

> These are worth setting, but note they were **not** the cause of the hangs we chased — that was `ipp-usb`.
> A blanked LCD is just burn-in protection; the printer is still awake and `READY` behind it.

## Known gaps

- **Barcodes are not implemented yet.** Text only. Real shelf labels need Code128/EAN — next job.
- **Docker CAN reach it** — `ipp-usb` binds all IPv4 interfaces (`*:60000`), so a container reaches the printer
  at the docker bridge gateway (`172.17.0.1:60000`) or the host's LAN IP. Verified from `banco-app`. What does
  *not* work is `localhost:60000` from inside a container — that's the container's own loopback.
- **A remote Banco cannot print here.** `banco.wolfhold.app` resolves to a different machine, and no server on
  the internet can reach a USB printer on your laptop. Direct printing has to be driven by something on the
  shop LAN — the local Banco instance, or the printer put on the network via its own Ethernet/Wi-Fi.
- Red/black printing, and the printer's P-touch Template mode, are untouched.
