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

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is missing.  pip install Pillow   (or: apt install python3-pil)")

DEFAULT_PRINTER = "BancoLabel"
DPI = 300                      # the QL-820NWB's native resolution
MARGIN_MM = 2.5                # keep ink off the die-cut edge

# Die-cut DK rolls the QL-820NWB advertises, as width x length in mm.
# `lpoptions -p BancoLabel -l` prints this same list from the printer itself.
MEDIA = {
    "12x12": (12, 12), "17x54": (17, 54), "17x87": (17, 87),
    "23x23": (23, 23), "24x24": (24, 24), "29x42": (29, 42),
    "29x52": (29, 52), "29x54": (29, 54), "29x62": (29, 62),
    "29x90": (29, 90),          # DK-11201 address label — ships in the box
    "38x90": (38, 90), "39x48": (39, 48), "58x58": (58, 58),
    "60x86": (60, 86), "62x100": (62, 100),
}
DEFAULT_MEDIA = "29x90"

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


def render(lines, w_mm, h_mm, out_path):
    """Paint the label and save it as a print-ready PNG at exact media size."""
    w_px, h_px = mm(w_mm), mm(h_mm)
    landscape = h_px > w_px            # normal for a roll: long axis feeds out

    # Draw with the long axis horizontal so text reads naturally, then rotate.
    cw, ch = (h_px, w_px) if landscape else (w_px, h_px)
    canvas = Image.new("L", (cw, ch), 255)
    d = ImageDraw.Draw(canvas)

    pad = mm(MARGIN_MM)
    box_w, box_h = cw - 2 * pad, ch - 2 * pad
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

    if landscape:
        canvas = canvas.rotate(90, expand=True)
    canvas.save(out_path, dpi=(DPI, DPI))
    return canvas.size


def run(cmd):
    """Run a command, returning (rc, combined output). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def show_status(printer):
    """Print what CUPS and the printer itself say — the first thing to check."""
    print(f"{C['b']}Queues{C['x']}")
    print(run(["lpstat", "-v"])[1] or "  (none)")
    print(f"\n{C['b']}{printer}{C['x']}")
    print(run(["lpstat", "-p", printer])[1] or "  (not found)")
    print(f"\n{C['b']}Pending jobs{C['x']}")
    print(run(["lpstat", "-o"])[1] or "  (queue empty)")
    # 127.0.0.1, NOT localhost: `localhost` resolves to ::1 first here and
    # ipp-usb listens on IPv4 only, so a browser on `localhost` spins forever.
    print(f"\n{C['dim']}Printer's own web page: http://127.0.0.1:60000/{C['x']}")


def main():
    ap = argparse.ArgumentParser(
        description="Print a text label on a Brother QL series label printer.")
    ap.add_argument("lines", nargs="*", help="lines of text; the first is the headline")
    ap.add_argument("-p", "--printer", default=DEFAULT_PRINTER, help=f"CUPS queue (default: {DEFAULT_PRINTER})")
    ap.add_argument("-m", "--media", default=DEFAULT_MEDIA, help=f"label size (default: {DEFAULT_MEDIA})")
    ap.add_argument("-n", "--copies", type=int, default=1, help="how many labels")
    ap.add_argument("--out", help="where to write the PNG (default: a temp file)")
    ap.add_argument("--dry-run", action="store_true", help="render the PNG but do not print")
    ap.add_argument("--status", action="store_true", help="show printer status and exit")
    ap.add_argument("--list-media", action="store_true", help="list known label sizes and exit")
    args = ap.parse_args()

    if args.list_media:
        for name, (w, h) in MEDIA.items():
            note = "  <- DK-11201, in the box" if name == DEFAULT_MEDIA else ""
            print(f"  {name:<8} {w}mm x {h}mm{note}")
        return 0

    if args.status:
        show_status(args.printer)
        return 0

    if not args.lines:
        ap.error("give me at least one line of text (or use --status / --list-media)")

    if args.media not in MEDIA:
        sys.exit(f"{C['red']}Unknown media {args.media!r}.{C['x']}  "
                 f"Try: {', '.join(MEDIA)}")
    w_mm, h_mm = MEDIA[args.media]

    out = args.out or os.path.join(tempfile.mkdtemp(prefix="banco-label-"), "label.png")
    size = render(args.lines, w_mm, h_mm, out)
    print(f"{C['dim']}rendered {size[0]}x{size[1]}px "
          f"({w_mm}x{h_mm}mm @ {DPI}dpi) -> {out}{C['x']}")

    if args.dry_run:
        print(f"{C['yel']}--dry-run: not printed.{C['x']}  Open it to check, then drop --dry-run.")
        return 0

    if not shutil.which("lp"):
        sys.exit(f"{C['red']}`lp` not found — CUPS isn't installed.{C['x']}  apt install cups-client")

    rc, msg = run(["lp", "-d", args.printer, "-n", str(args.copies),
                   "-o", f"media={args.media}mm", "-o", "CutMedia=EndOfPage", out])
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
