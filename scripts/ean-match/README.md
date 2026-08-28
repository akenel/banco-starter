# ean-match — bind real EANs by comparing pictures

**Why.** 4,980 of 5,447 active products carry a minted `200…` barcode that is on no packet
(WORKLIST ⓪). Tamar publishes no EAN on any of its five storefronts. But FourTwenty's feed holds
**11,014 real GTINs with photographs**, and both wholesalers stock the same branded consumables.
So: put the two pictures side by side and let a person decide.

**Proven blind, twice, 2026-08-28** against 116 products Angel had bound off the packet — 88%
correct whenever the twin was on screen, **0 false positives in 12 decoys**. Full numbers and the
five findings: `LESSONS.md`, *"the pictures matched, the RANGE did not"*.

## The rules this tool obeys

- **Never auto-binds.** A human confirms every pair (LESSON #9 — a wrong barcode looks exactly
  like a right one).
- **Never writes to `products.barcode`.** The found EAN belongs in `product_barcodes` as an alias,
  so the minted code and the printed labels keep working.
- **Never discards a multi-pack candidate** — a wholesaler GTIN is often the box of fifty. It is
  ranked down and flagged orange. Measured: a hard `units=1` filter would have thrown away 2 of 82
  correct answers (LESSON pattern #2).
- **Consumables only.** Bongs and grinders have no twins in the feed (12 tested, 0 matched). Their
  minted EAN is the correct answer.

## Pipeline

```
fetchpool2.py   FourTwenty feed images  -> pool2_hashes.pkl + thumbs/   (resumable)
fetchtam.py     Tamar product images    -> tam_hashes.pkl   + thumbs/   (gentle on the live app)
select2.py      rank candidates, compute mutual-best -> cards2.json / truth2.json
sheet2.py       build(...) -> one self-contained HTML review sheet
score2.py       score the downloaded decisions against truth2.json
```

`hash.py` holds dHash / pHash / colour-histogram and the fetch helper.

## Known limitation — read before extending

`hash.py` compares **pixels**. The two catalogues photograph their own stock, so on products known
to be identical only **2 of 14** image pairs were the same file. Pixel hashing scored 57% rank-1
against a 120-image lineup and **50% against 1,761** — it degrades as the pool grows, which is the
wrong direction. The fix is **CLIP-style embeddings** (semantic, not pixel), run once on the laptop.
No box in `MAP.md` has capacity for a model; the laptop does, and this is a one-time batch.

## The ranker — measured, 2026-08-28

Pixel hashing was replaced with **CLIP ViT-B/32 image embeddings** (ONNX, CPU, ~2 min for 3,244
images on 8 cores). Against 24 pairs whose EAN a human had already bound off the packet:

| recipe | top-1 | top-3 | top-8 |
|---|---|---|---|
| dHash + colour + 0.15·name (old) | 54% | 62% | 67% |
| CLIP only | 33% | 58% | 79% |
| **CLIP + 0.35·name** | **75%** | **92%** | **96%** |
| CLIP + name + hash | 75% | 92% | 96% |

Adding the old hash on top of CLIP+name changes **nothing** — it is dropped. CLIP alone is *worse*
at top-1 than the old ranker; the text signal is what makes it work. Neither alone is enough.

### There is no confidence threshold. Do not add one.

Tried and measured, twice:

- **Absolute score** — lowest correct match 0.935, highest score for a product with *no twin at all*
  **1.126**. A floor that removes 15 of 16 hopeless cards also throws away 5 of 18 real ones.
- **Margin (top1 − top2)** — median 0.050 when right vs 0.018 when hopeless, and the ranges overlap
  end to end.

The reason is not a weak model. It is that the high-scoring wrong answers are **real near-twins**:

```
Zigaretten Parisienne Verte        -> Parisienne add.free Verte Box 10
Tabak Beutel Chesterfield Original -> Chesterfield Original Big Pack
Star-Buds Luzern Cali Kush 2.7gr   -> Starbuds Luzern Mini Buds V-Ice
```

Same brand, different format — genuinely almost the same product, and only the packet resolves it.
**A high score means "same family", never "same SKU".** Across three blind rounds a human rejected
**19 of 19** such cards with zero false positives. That is the gate. Never auto-bind.

## Setup (not in git — 352 MB model + venv)

```
python3 -m venv ~/ean-test/venv && ~/ean-test/venv/bin/pip install onnxruntime pillow numpy
curl -sSL -o clip/model.onnx \
  https://huggingface.co/Qdrant/clip-ViT-B-32-vision/resolve/main/model.onnx
~/ean-test/venv/bin/python clipembed.py      # resumable; ~2 min for 3.2k images on 8 cores
```
