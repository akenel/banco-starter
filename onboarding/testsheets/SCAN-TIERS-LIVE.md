# Scan tiers — the live half-hour test

**Where:** https://banco.wolfhold.app/pos → Scan → Barcode
**Date built:** 2026-08-21 · every control code below was verified against the live shop that day.

**Nothing here rings a sale.** Tier 1 drops an item in the cart — just empty the cart when you're
done. The only thing that writes to the catalogue is if *you* press create.

---

## Part A — four control codes, two minutes

Type each into the barcode box and press Enter. This proves the machinery is alive before you
start on real packets, so a surprise later means something real and not a broken deploy.

| # | Type this | What should happen | ✅ / ✗ |
|---|---|---|---|
| A1 | `42425700` | **Straight into the cart** — Gizeh King Size Slim. No banner, no strip. | |
| A2 | `9783037886977` | **Panel opens** "Not on file — find it first", search box already says **101 Gründe Cannabis zu lieben** | |
| A3 | `4260641140046` | Amber banner + department strip, then a moment later a **blue offer** appears: 📚 *from Kings Castle* · **actiTube Aktivkohlefilter - Slim (50Stk.)** with a photo and an orange wholesaler warning | |
| A4 | `7640000000001` | Amber banner + department strip. **No offer, ever.** Nobody knows this code. | |

**A3 is the new thing.** Watch that the strip appears *first* and the offer arrives *after* —
nothing should jump under your finger.

---

## Part B — ten real packets off the shelf

This is the part I can't do and you can. **Pick them at random** — grab whatever is nearest,
not the ones you remember fighting with. That's the whole point: my sample was biased because
it only contained things somebody had already managed to bind.

Scan each one and write down which of these four happened:

```
1  IN THE CART             it was already bound. Nothing to do.
2  PANEL, WITH A NAME      our reference knew it (FourTwenty)
3  OFFER, blue box         Kings Castle knew it
4  NOTHING BUT THE STRIP   nobody knows it
```

| # | Packet (a word is enough) | Code if easy | 1 / 2 / 3 / 4 |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |

---

## What I'm actually asking

**The tally, not a verdict.** Four numbers — how many landed in 1, 2, 3, 4.

My measurement said roughly 40% for tiers 1+2 and ~56% with Kings Castle, from a sample I
already told you was biased. Yours isn't. If you get eight in a row that nobody knows, that is
the answer and I want it — it means the next thing to build is a second wholesale feed, not
more matching.

## Two things worth flagging if you see them

- **A wrong name offered confidently.** Tap the photo, look at the pack size. Kings Castle sells
  cases — the name can be right and the *thing* be a 10-pack. If the offer names something that
  isn't what you're holding, that's the one bug class this shop keeps paying for. Tell me.
- **The offer arriving after you already tapped a department.** It shouldn't move anything, but
  if it feels like it does, say so — that's a design call, not a bug report.
