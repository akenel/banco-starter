# Prompt for Nano Banana — Banco login background

## What it is for
A full-screen background image behind the staff login card of a point-of-sale
system, used on a 2160×1440 shop tablet in a Swiss herb-and-fragrance shop
(Artemis Kräuter & Düfte, Luzern). A white card with dark text sits in the
MIDDLE of the screen, and white heading text sits just above it — so the middle
third must stay dark, quiet and low-contrast, or nothing on top of it can be
read.

## The prompt

> A wide 3:2 abstract background for a dark user interface. A deep, rich
> gradient running from emerald green in the upper left, through teal, to
> near-black slate in the lower right. Softly suggested botanical forms —
> six-pointed star-flowers, slender herb leaves and thin stems — emerging from
> the darkness at the LEFT and RIGHT edges and the BOTTOM corners only, like a
> faint watermark just barely catching the light. The entire CENTRE of the image
> is clean, dark and empty, with no detail at all. Very low contrast throughout,
> nothing brighter than a soft moss green. Flat, elegant, modern, minimal — the
> feel of an expensive apothecary label, not a photograph. Smooth, no visible
> grain or noise, no vignette ring.

## Add these as negative / "do not" instructions

> No text, no letters, no words, no numbers, no logo, no signature, no
> watermark text. No cannabis leaves. No people, no hands, no bottles, no jars.
> No bright highlights or glare in the centre. No busy patterns, no mandala, no
> heavy ornament. Nothing photographic.

**The "no text" instruction matters most.** Image models add invented,
misspelled lettering into backgrounds by default, and this one sits under a
login screen in a real shop.

## Size and format
- Ask for **3:2**, then export at **2160 × 1440** (the tablet's exact panel).
- PNG or high-quality JPEG. Keep it under ~600KB — it loads before anyone can
  log in, sometimes over the shop's LTE.
- If it comes out lighter than expected, ask for "darker, lower contrast, more
  negative space in the middle" rather than editing it afterwards.

## Where it goes
`login.html` already reads a `login_bg` value from store settings, so this can
be a per-shop setting rather than something baked into the code.
