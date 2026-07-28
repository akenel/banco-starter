#!/usr/bin/env python3
# ============================================================================
# print-label — put words on a Brother QL label, from the command line.
#
# The QL-820NWBc needs NO Brother software on Linux. Debian's `ipp-usb` daemon
# already speaks to it over USB and hands it to CUPS as a normal printer. This
# script just paints a PNG at the exact pixel size of the loaded label and
# hands it to `lp`. That's the whole trick.
#
#   python3 scripts/print-label.py "BANCO" "Shelf 3" "CHF 12.50"
#   python3 scripts/print-label.py --media 62x100 "Big label"
#   python3 scripts/print-label.py --copies 5 "Ticket"
#   python3 scripts/print-label.py --dry-run --out /tmp/x.png "Preview me"
#   python3 scripts/print-label.py --status         # what's the printer doing?
#
# First line is printed big; the rest step down in size. Text is auto-shrunk
# to fit the label, so you can't silently print something chopped off.
#
# Zero new dependencies — Pillow only, already in requirements.txt.
# Exit 0 = the job reached the queue, 1 = it didn't.
# ============================================================================
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is missing.  pip install Pillow   (or: apt install python3-pil)")

DEFAULT_PRINTER = "BancoLabel"
DPI = 300                      # the QL-820NWB's native resolution
MARGIN_MM = 2.5                # keep ink off the die-cut edge

# DK rolls. A length of None means CONTINUOUS tape: you choose how long each
# label is (--length) rather than the die deciding. Die-cut names here match
# the driverless PPD exactly — see `lpoptions -p BancoLabel -l`; continuous
# widths are sent as Custom.WIDTHxLENGTHmm, which that PPD also accepts.
MEDIA = {
    # continuous — length is yours to pick
    "12": (12, None), "29": (29, None), "38": (38, None),
    "50": (50, None), "54": (54, None),
    "62": (62, None),           # DK-22205 / DK-44205 — the shop roll
    # die-cut — length fixed by the die
    "12x12": (12, 12), "17x54": (17, 54), "17x87": (17, 87),
    "23x23": (23, 23), "24x24": (24, 24), "29x42": (29, 42),
    "29x52": (29, 52), "29x54": (29, 54), "29x62": (29, 62),
    "29x90": (29, 90),          # DK-11201 address label — ships in the box
    "38x90": (38, 90), "39x48": (39, 48), "58x58": (58, 58),
    "60x86": (60, 86), "62x100": (62, 100),
}
DEFAULT_MEDIA = "62"            # the 62mm continuous roll the shop runs
DEFAULT_LENGTH_MM = 60          # label length on continuous tape

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")

C = {"red": "\033[31m", "yel": "\033[33m", "grn": "\033[32m",
     "dim": "\033[2m", "b": "\033[1m", "x": "\033[0m"}
if not sys.stdout.isatty():
    C = {k: "" for k in C}


def mm(v):
    """Millimetres -> pixels at the printer's native DPI."""
    return round(v * DPI / 25.4)


def font(path, size):
    """Load a TrueType face, falling back to Pillow's builtin if DejaVu is gone."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_barcode(code, target_w_px, max_h_px):
    """Render `code` as a barcode, at most target_w_px wide and max_h_px tall.

    EAN-13 for 12/13 digits (the check digit is computed or verified for you),
    Code128 for anything else — that covers internal SKUs like TAM-21796.

    Kept deliberately wide: an EAN-13 needs roughly 31mm at 80% magnification
    before scanners start struggling, so on a 62mm roll we spend the width we
    have rather than shrinking it to look tidy.
    """
    try:
        import barcode
        from barcode.writer import ImageWriter
    except ImportError:
        sys.exit(f"{C['red']}python-barcode is missing.{C['x']}  "
                 "pip install --user python-barcode")

    digits = code.isdigit()
    kind = "ean13" if digits and len(code) in (12, 13) else "code128"
    if kind == "ean13" and len(code) == 13:
        code = code[:12]          # the library recomputes the check digit

    try:
        bc = barcode.get(kind, code, writer=ImageWriter())
        # text_distance must clear module_height or the digits print ON the
        # bars and the scanner reads mush. quiet_zone is the blank margin the
        # spec requires either side — don't trim it to make the label prettier.
        img = bc.render({"module_height": 15.0, "font_size": 10,
                         "text_distance": 5.0, "quiet_zone": 3.0})
    except Exception as e:
        sys.exit(f"{C['red']}Could not encode {code!r} as {kind}: {e}{C['x']}")

    # Fit to width, but a short code (Code128 of a small SKU) is a narrow
    # image — blow that up to full label width and it becomes absurdly tall
    # and swallows the label. So cap the height and re-fit if we hit it.
    w, h = img.size
    new_w, new_h = target_w_px, max(1, round(h * target_w_px / w))
    if new_h > max_h_px:
        new_h = max_h_px
        new_w = max(1, round(w * max_h_px / h))
    return img.resize((new_w, new_h)).convert("L"), bc.get_fullcode()


def fit_lines(draw, lines, box_w, box_h):
    """Choose the biggest font sizes that keep every line inside the label.

    Returns [(text, font, width, height, top)]. The first line is the headline
    (bold, 100%), later lines step down and are regular weight. We shrink the
    whole block together so the relative hierarchy survives.
    """
    scale = 1.0
    while scale > 0.05:
        head = mm(9) * scale
        body = mm(5) * scale
        chosen, total, widest = [], 0, 0
        for i, text in enumerate(lines):
            size = int(head if i == 0 else body)
            if size < 6:
                break
            f = font(FONT_BOLD if i == 0 else FONT_REG, size)
            l, t, r, b = draw.textbbox((0, 0), text or " ", font=f)
            chosen.append((text, f, r - l, b - t, t))
            total += (b - t) + int(size * 0.35)
            widest = max(widest, r - l)
        if len(chosen) == len(lines) and total <= box_h and widest <= box_w:
            return chosen
        scale -= 0.04
    return []


def render(lines, w_mm, h_mm, out_path, code=None):
    """Paint the label and save it as a print-ready PNG at exact media size."""
    w_px, h_px = mm(w_mm), mm(h_mm)
    landscape = h_px > w_px            # normal for a roll: long axis feeds out

    # Draw with the long axis horizontal so text reads naturally, then rotate.
    cw, ch = (h_px, w_px) if landscape else (w_px, h_px)
    canvas = Image.new("L", (cw, ch), 255)
    d = ImageDraw.Draw(canvas)

    pad = mm(MARGIN_MM)
    box_w, box_h = cw - 2 * pad, ch - 2 * pad

    # Reserve the barcode's space BEFORE fitting text, so shrinking text can
    # never eat into it — an unscannable barcode defeats the whole label.
    bc_img = full = None
    if code:
        # Give the barcode at most half the label, so text always has room.
        bc_img, full = make_barcode(code, round(box_w * 0.92), round(box_h * 0.5))
        box_h -= bc_img.height + mm(1.5)
        if box_h < mm(4):
            sys.exit(f"{C['red']}No room for text and a barcode on "
                     f"{w_mm}x{h_mm}mm.{C['x']}  Try a longer --length.")

    chosen = fit_lines(d, lines, box_w, box_h)
    if not chosen:
        sys.exit(f"{C['red']}Text will not fit on a {w_mm}x{h_mm}mm label.{C['x']}  "
                 "Use fewer/shorter lines, or a bigger --media.")

    # Centre the block on both axes — a short label otherwise floats at one end
    # with a big dead gap, which reads as a bug rather than a design.
    block = sum(h + int(f.size * 0.35) for _, f, _, h, _ in chosen)
    y = pad + max(0, (box_h - block) // 2)
    for text, f, w, h, top in chosen:
        x = pad + max(0, (box_w - w) // 2)
        d.text((x, y - top), text, font=f, fill=0)
        y += h + int(f.size * 0.35)

    if bc_img is not None:
        canvas.paste(bc_img, (pad + (box_w - bc_img.width) // 2,
                              ch - pad - bc_img.height))

    if landscape:
        canvas = canvas.rotate(90, expand=True)
    canvas.save(out_path, dpi=(DPI, DPI))
    return canvas.size, full


def run(cmd):
    """Run a command, returning (rc, combined output). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def ipp_usb_alive(timeout=12):
    """True if ipp-usb is actually relaying to the printer right now.

    A dead session still accepts TCP and answers a bare redirect, so we ask
    for real printer attributes — that is the part that goes silent.
    """
    rc, out = run(["ipptool", "-T", str(timeout), "-tv",
                   "ipp://localhost:60000/ipp/print",
                   "/usr/share/cups/ipptool/get-printer-attributes.test"])
    return rc == 0 and "RECEIVED: 0 bytes" not in out and "printer-state" in out


def heal_ipp_usb():
    """Restart ipp-usb when its USB session has gone stale.

    THE fault of the driverless path: after ~6-11 minutes idle the daemon
    stops relaying and every job hangs at "now printing" while the printer
    sits there lit and READY. Restarting it fixes it instantly and does not
    involve touching the printer. Needs the sudoers rule in
    scripts/sudoers/banco-label-printer, else this no-ops and we print anyway.
    """
    print(f"  {C['yel']}ipp-usb is not relaying — restarting it{C['x']}")
    if run(["sudo", "-n", "systemctl", "restart", "ipp-usb"])[0] != 0:
        run(["sudo", "-n", "systemctl", "kill", "-s", "KILL", "ipp-usb"])
        if run(["sudo", "-n", "systemctl", "restart", "ipp-usb"])[0] != 0:
            print(f"  {C['red']}could not restart it without a password.{C['x']}  "
                  "Install scripts/sudoers/banco-label-printer, or run:\n"
                  "    sudo systemctl restart ipp-usb")
            return False
    for _ in range(12):                  # it can take a while to come back
        time.sleep(5)
        if ipp_usb_alive():
            print(f"  {C['grn']}back up{C['x']}")
            return True
    print(f"  {C['red']}still not relaying after 60s.{C['x']}  Check the printer is on.")
    return False


def clear_queues(printer):
    """Cancel every stuck job and re-enable every queue. The 'unstick me' button.

    Jobs pile up invisibly when they're sent to a queue that can't reach the
    printer -- classically the temporary `cups-browsed` one, which goes dead
    with "No destination host name supplied". Nothing prints and nothing
    obviously complains, so this clears the lot and turns the queues back on.
    """
    print(f"{C['b']}Jobs found{C['x']}")
    pending = run(["lpstat", "-o"])[1]
    print(pending or "  (none)")

    run(["cancel", "-a", "-x"])
    for q in ("BancoLabel", printer):
        run(["cupsenable", q])

    left = run(["lpstat", "-o"])[1]
    if left:
        print(f"\n{C['yel']}Still queued:{C['x']}\n{left}")
        return 1
    print(f"\n{C['grn']}✅ queues cleared and re-enabled{C['x']}")
    print(run(["lpstat", "-p"])[1] or "")
    return 0


def show_status(printer):
    """Print what CUPS and the printer itself say — the first thing to check."""
    print(f"{C['b']}Queues{C['x']}")
    print(run(["lpstat", "-v"])[1] or "  (none)")

    print(f"\n{C['b']}All queue states{C['x']}")
    states = run(["lpstat", "-p"])[1]
    print(states or "  (none)")
    if "disabled" in states:
        print(f"  {C['yel']}^ a disabled queue swallows jobs silently — "
              f"run with --clear{C['x']}")

    print(f"\n{C['b']}Pending jobs{C['x']}")
    jobs = run(["lpstat", "-o"])[1]
    print(jobs or "  (queue empty)")
    if jobs and printer not in jobs:
        print(f"  {C['yel']}^ these are queued on a DIFFERENT printer than "
              f"{printer} — that's why nothing came out{C['x']}")

    # How we check the hardware depends on which path this queue takes.
    uri = run(["lpstat", "-v", printer])[1]
    print(f"\n{C['b']}Is the printer there?{C['x']}")

    if "usb://" in uri:
        # Direct USB (printer-driver-ptouch). CUPS lists the device only while
        # the printer is attached and powered, so that listing IS the check.
        if "usb://" in run(["lpinfo", "-v"])[1]:
            print(f"  {C['grn']}✅ yes — on USB and visible to CUPS{C['x']}")
        else:
            print(f"  {C['red']}✗ not visible to CUPS.{C['x']}  "
                  "Check the cable, and that the LCD is lit.")
        print(f"\n{C['dim']}Direct USB path — no ipp-usb, so no web page "
              f"at localhost:60000.{C['x']}")
    else:
        # Legacy ipp-usb path. A dead answer here is almost always a stale
        # daemon session, not a sleeping printer — say so, it saves hours.
        rc, out = run(["ipptool", "-tv", "ipp://127.0.0.1:60000/ipp/print",
                       "/usr/share/cups/ipptool/get-printer-attributes.test"])
        if rc != 0 or "RECEIVED: 0 bytes" in out:
            print(f"  {C['red']}✗ ipp-usb is not answering.{C['x']}  "
                  "Usually a stale session, NOT a sleeping printer:\n"
                  "    sudo systemctl restart ipp-usb")
        else:
            print(f"  {C['grn']}✅ yes — awake and answering{C['x']}")
        print(f"\n{C['dim']}Printer's own web page: http://127.0.0.1:60000/{C['x']}")


def main():
    ap = argparse.ArgumentParser(
        description="Print a text label on a Brother QL series label printer.")
    ap.add_argument("lines", nargs="*", help="lines of text; the first is the headline")
    ap.add_argument("-p", "--printer", default=DEFAULT_PRINTER, help=f"CUPS queue (default: {DEFAULT_PRINTER})")
    ap.add_argument("-m", "--media", default=DEFAULT_MEDIA, help=f"roll size (default: {DEFAULT_MEDIA})")
    ap.add_argument("-l", "--length", type=int, default=DEFAULT_LENGTH_MM,
                    help=f"label length in mm on continuous tape (default: {DEFAULT_LENGTH_MM})")
    ap.add_argument("-c", "--barcode", metavar="CODE",
                    help="print a scannable barcode: EAN-13 for 12/13 digits, else Code128")
    ap.add_argument("-n", "--copies", type=int, default=1, help="how many labels")
    ap.add_argument("--out", help="where to write the PNG (default: a temp file)")
    ap.add_argument("--dry-run", action="store_true", help="render the PNG but do not print")
    ap.add_argument("--status", action="store_true", help="show printer status and exit")
    ap.add_argument("--clear", action="store_true",
                    help="cancel every stuck job and re-enable the queues, then exit")
    ap.add_argument("--no-heal", action="store_true",
                    help="don't auto-restart a stale ipp-usb before printing")
    ap.add_argument("--list-media", action="store_true", help="list known label sizes and exit")
    args = ap.parse_args()

    if args.list_media:
        for name, (w, h) in MEDIA.items():
            if h is None:
                note = "  <- the shop roll (DK-44205)" if name == DEFAULT_MEDIA else ""
                print(f"  {name:<8} {w}mm continuous — length via --length{note}")
            else:
                print(f"  {name:<8} {w}mm x {h}mm die-cut")
        return 0

    if args.clear:
        return clear_queues(args.printer)

    if args.status:
        show_status(args.printer)
        return 0

    if not args.lines:
        ap.error("give me at least one line of text (or use --status / --list-media)")

    if args.media not in MEDIA:
        sys.exit(f"{C['red']}Unknown media {args.media!r}.{C['x']}  "
                 f"Try: {', '.join(MEDIA)}")
    w_mm, h_mm = MEDIA[args.media]
    if h_mm is None:                     # continuous tape — we pick the length
        h_mm = args.length

    out = args.out or os.path.join(tempfile.mkdtemp(prefix="banco-label-"), "label.png")
    size, full = render(args.lines, w_mm, h_mm, out, code=args.barcode)
    bc_note = f"  barcode {full}" if full else ""
    print(f"{C['dim']}rendered {size[0]}x{size[1]}px "
          f"({w_mm}x{h_mm}mm @ {DPI}dpi){bc_note} -> {out}{C['x']}")

    if args.dry_run:
        print(f"{C['yel']}--dry-run: not printed.{C['x']}  Open it to check, then drop --dry-run.")
        return 0

    if not shutil.which("lp"):
        sys.exit(f"{C['red']}`lp` not found — CUPS isn't installed.{C['x']}  apt install cups-client")

    # The option names differ per driver, so pick them from the queue's URI.
    #
    #   ipp://…        CUPS driverless ("everywhere") via ipp-usb  -> media=
    #   usb://…        printer-driver-ptouch, direct USB           -> PageSize=
    #
    # We run the driverless path. printer-driver-ptouch 1.6 lists the
    # QL-820NWB as "recommended" but never printed a single label on it —
    # every job came back "Wrong roll type / check the print data" for all
    # four MediaType x PageSize combinations, while the printer itself
    # reported the roll correctly. Old driver, newer printer. Don't re-try it
    # without a newer ptouch-driver release.
    # Continuous rolls have no PPD name of their own — ask for a custom size
    # of the roll's width by the length we chose.
    continuous = MEDIA[args.media][1] is None
    size = f"Custom.{w_mm}x{h_mm}mm" if continuous else f"{args.media}mm"

    uri = run(["lpstat", "-v", args.printer])[1]

    # On the driverless path, make sure ipp-usb is actually relaying before we
    # hand CUPS a job — otherwise it queues, says "now printing", and hangs.
    if "usb://" not in uri and not args.no_heal:
        if not ipp_usb_alive():
            heal_ipp_usb()

    if "usb://" in uri:
        opts = ["-o", f"PageSize={size}", "-o", "MediaType=Labels",
                "-o", "AutoCut=True"]
    else:
        opts = ["-o", f"media={size}", "-o", "CutMedia=EndOfPage"]

    rc, msg = run(["lp", "-d", args.printer, "-n", str(args.copies)] + opts + [out])
    if rc != 0:
        print(f"{C['red']}✗ could not queue the job{C['x']}\n{msg}", file=sys.stderr)
        print(f"\n{C['dim']}Try: python3 scripts/print-label.py --status{C['x']}", file=sys.stderr)
        return 1

    n = args.copies
    print(f"{C['grn']}✅ queued {n} label{'s' if n != 1 else ''} on {args.printer}{C['x']}  "
          f"{C['dim']}({msg}){C['x']}")
    print(f"{C['dim']}Nothing came out? The printer sleeps. Check the LCD is lit, "
          f"then: python3 scripts/print-label.py --status{C['x']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
