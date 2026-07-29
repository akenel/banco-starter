#!/usr/bin/env python3
# ============================================================================
# make-leaf-mark — draw a hemp leaf as a clean square PNG for the QR centre.
#
#   python3 scripts/make-leaf-mark.py                       # default green
#   python3 scripts/make-leaf-mark.py --colour "#1a4d2e"    # Banco green
#   python3 scripts/make-leaf-mark.py --out src/static/artemis-mark.png
#
# WHY DRAW IT rather than use the shop's logo: the middle of a 15mm QR is about
# 4mm across. A logo lockup (symbol + shop name) renders its wordmark at ~0.5mm
# there and reads as a grey smudge — measured on the real Artemis logo. A bold
# SILHOUETTE survives that size; lettering never will.
#
# Generated rather than downloaded so it is ours, scales to any size, recolours
# to any shop's brand, and has no licence attached to it.
#
# Zero dependencies beyond Pillow, which is already required.
# ============================================================================
import argparse
import math

from PIL import Image, ImageDraw

# (angle from vertical°, length×, width×) — a hemp leaf is 7 leaflets: one
# upright, then three symmetric pairs getting shorter and dropping toward
# horizontal. The asymmetry in width is what stops it reading as a starfish.
LEAFLETS = [
    (0,    1.00, 0.150),
    (34,   0.90, 0.140),
    (66,   0.72, 0.125),
    (96,   0.48, 0.105),
]
TEETH = 7          # serrations per edge — the sawtooth that says "hemp"


def leaflet(cx, cy, angle_deg, length, half_width):
    """One serrated leaflet as a polygon, radiating from (cx, cy)."""
    a = math.radians(angle_deg - 90)          # -90 so 0° points up
    ux, uy = math.cos(a), math.sin(a)         # along the spine
    px, py = -uy, ux                          # across it

    def at(t, w):
        """t = 0..1 along the spine, w = offset across it."""
        return (cx + ux * length * t + px * w,
                cy + uy * length * t + py * w)

    # Leaflet profile: narrow at the base, widest at ~35%, tapering to a point.
    def width_at(t):
        if t < 0.35:
            return half_width * (t / 0.35) ** 0.65
        return half_width * (1 - (t - 0.35) / 0.65) ** 0.80

    pts = [at(0.02, 0)]
    # up the right edge, cutting teeth
    for i in range(TEETH):
        t0 = 0.10 + (0.88 * i / TEETH)
        t1 = 0.10 + (0.88 * (i + 0.5) / TEETH)
        pts.append(at(t0, width_at(t0)))              # tooth tip (outer)
        pts.append(at(t1, width_at(t1) * 0.55))       # notch (inner)
    pts.append(at(1.0, 0))                            # the point
    # back down the left edge, mirrored
    for i in reversed(range(TEETH)):
        t1 = 0.10 + (0.88 * (i + 0.5) / TEETH)
        t0 = 0.10 + (0.88 * i / TEETH)
        pts.append(at(t1, -width_at(t1) * 0.55))
        pts.append(at(t0, -width_at(t0)))
    return pts


def draw_leaf(size=512, colour="#3aa757", outline="#ffffff", supersample=4):
    """Render the leaf centred in a transparent square."""
    S = size * supersample
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    cx, cy = S / 2, S * 0.60          # sit the origin low: leaflets fan upward
    reach = S * 0.52
    ow = max(1, int(S * 0.006))       # thin white keyline separates the lobes

    for ang, ln, hw in LEAFLETS:
        for sign in ((0,) if ang == 0 else (1, -1)):
            pts = leaflet(cx, cy, ang * sign, reach * ln, reach * hw)
            d.polygon(pts, fill=colour, outline=outline, width=ow)

    # short stem
    d.line([(cx, cy), (cx, cy + reach * 0.22)], fill=colour, width=int(S * 0.018))

    # trim to content, then pad back to a true square so it centres cleanly
    img = img.crop(img.getchannel("A").getbbox())
    s = max(img.size)
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sq.paste(img, ((s - img.width) // 2, (s - img.height) // 2), img)
    return sq.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Draw a hemp leaf mark for the QR centre.")
    ap.add_argument("--out", default="src/static/leaf-mark.png")
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--colour", default="#3aa757", help="leaf fill, e.g. #1a4d2e")
    a = ap.parse_args()
    draw_leaf(a.size, a.colour).save(a.out)
    print(f"wrote {a.out}  ({a.size}x{a.size}, {a.colour})")
