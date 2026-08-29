"""Build the Filters & Tips review sheet — run 1."""
import json, os, sys
SP = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, SP)
WORK = os.environ.get("EAN_WORK", os.path.join(SP, "work"))
import sheet3

cards = json.load(open(os.path.join(WORK, "cards_filters.json")))

INTRO = """Same job as the papers deck: <b>is the picture on the right the same product as the
one on the left?</b> Hover a thumbnail to enlarge it; click any of the six guesses to swap it in.
<br><br>
<b>Filters are the hardest category yet</b> — a 6mm tip photographs exactly like an 8mm one, so
<u>the picture will not decide this and it is not supposed to</u>. The <span style="color:#c0392b">red
words</span> in the two titles are the discriminator: the size in mm and the count in the packet.
When the numbers disagree, it is <b>✗ No match</b> however alike the photos look.
<br><br>
The measurement says the right answer is <b>on your screen</b> when it exists at all — 15 of 15
known rows landed in the top 3. So a card where nothing looks right is genuinely a
<b>✗ No match</b>, not a failure to look hard enough.
<br><br>
<b>Nothing is locked.</b> Click a different option or ↺ clear on any card, any time. Stop at any
sitting break and come back — your answers are saved in this browser under this run's own key.
<br><br>
<span style="opacity:.75">27 of these 252 cards are rows you already bound off a real packet.
They are shuffled in and look identical to the rest. Some have a twin in the feed and some have
none at all — so the run scores both whether you find what is there and whether you decline what
is not.</span>"""

# Sitting breaks — Angel works ~40 at a time. A visible stopping place beats a scrollbar.
sections, per = {}, 40
for k in range(0, len(cards), per):
    lo, hi = k + 1, min(k + per, len(cards))
    sections[cards[k]["i"]] = (f"sitting {k//per + 1} &nbsp;·&nbsp; cards {lo}–{hi} of {len(cards)}"
                               + ("" if k else " &nbsp;·&nbsp; start here"))

out = os.path.join(WORK, "ean-filters-run1.html")
size = sheet3.build(cards, out, "Filters & Tips — run 1", INTRO, sections, run_id="filters")
print(f"{out}  {size/1e6:.1f} MB  {len(cards)} cards  {len(sections)} sittings")
