# The anonymous member card — spec, 2026-08-22

*Written the evening of 2026-08-22 at Angel's ask. **Spec'd, not scheduled.** Everything below
about the current state was measured on Felix's box that night, not remembered.*

---

## The ask

Angel, relaying Felix: *"nobody wants to give their name, but show a barcode or QR code to scan
would be better — like the Coop or Migros membership cards."*

He is describing **Supercard / Cumulus**: the card *is* the identity. Nobody says a name out loud
at the counter, the cashier scans a code, and the account is found. For a headshop the privacy
argument is not a nicety — it is most of the reason a customer would say yes at all.

---

## Most of this is already built, and it has never been used

| Piece | Where | State |
|---|---|---|
| `customers.qr_code` | `varchar(32)`, **UNIQUE**, nullable | column exists |
| `generate_qr_code()` → `HLX-` + 8 hex | `customer_model.py:471` | written |
| `POST /customer/{id}/generate-qr` | `pos_router.py:5046` | manager/admin only |
| `GET /customer/scan?code=` | `pos_router.py:4967` | **no auth — *"the code is the secret"*** |
| Kiosk signup mints one and prints it | `pos_router.py:11864`, `kiosk.html:151` | written |
| Checkout attaches a member | `checkout.html:1350` | working — 6 of 50 sales carry one |

**And the form already agrees with Felix.** On `/pos/customer-lookup` only **`Handle *`** is
required; Real Name, Email, Phone and Date of birth are every one of them optional
(`customer_lookup.html:96–134`). *An anonymous member is already legal in this data model.*
Nothing needs to change in the schema to allow one.

### The gap, measured on prod

```
18 customers  ·  0 with a qr_code  ·  15 with a real_name
```

**The generator has never once been called for a real member**, and `scan.html` — the till itself —
has no member concept at all. Checkout links *away* to a screen where you **type** a handle.

So: built, wired, and empty. The same shape as `reference_products`, which sat at 0 rows on every
machine for the project's whole life. **Pattern 1 — green on every layer a test can reach.**

---

## The decision that matters: a date of birth is not a name

The member is **load-bearing for the age gate.** `transaction_model.py:107` records how each sale
cleared 18+, and the rungs are not equal:

```
not_required      no age-restricted line in this basket
member_dob        customer on file whose birthdate proves 18+   ← strongest
member_confirmed  on file, age_confirmed ticked, NO birthdate — "a tick, not a document"
cashier_attest    cashier confirmed ID at the counter (walk-in)
```

An anonymous card carrying **no** birthdate drops every regular to `member_confirmed`, which the
model's own comment calls a tick rather than a document. That would quietly weaken the compliance
posture the whole of 2026-08-10 → 08-13 was spent building.

**It does not have to.** Coop knows your birthday and essentially nothing else. A card can carry
**a code and a date of birth and nothing more** — no name, no email, no phone — and that is both
fully anonymous *and* the strongest rung on the ladder.

### Which is also the pitch, and the pitch is not loyalty

Nobody accepts a card for a discount they do not yet understand. But today a regular buying tobacco
gets the 18+ stop **every single time**. With a DOB on the card:

> **"Scan this and we never have to ask for your ID again."**

That is a cashier win as much as a customer one — it removes a modal from the most common basket in
the shop — and it is the sentence that gets the card into a pocket. The loyalty tier is a bonus
riding along, not the reason.

---

## What would actually need building

1. **Mint codes for the 18 existing members.** One script run; the generator is already written.
2. **A member-scan path at the till.** *This is the only item with real thinking in it.* The
   endpoint exists and needs no auth; the till has no way to reach it. Structurally the same as
   the barcode bind already shipped — a scan that resolves, or does not.
3. **Something to print.** `product_label.html`, `product_labels_batch.html` and `postcard.html`
   exist; there is no member-card template. ⚠️ May be gated on the label printing still being
   wired up — check before promising a plastic card.
4. **A signup that asks for exactly two things** — pick a code, give a birthdate. Nothing else.

---

## Risks and open questions — read before scheduling

- **A card only helps if it is carried.** A QR on a phone screen beats plastic for that, and costs
  nothing to print. Consider phone-first, plastic later.
- **`GET /customer/scan` has no auth, deliberately — *"the code is the secret."*** That is a
  reasonable design for a loyalty lookup and a **poor** one for something that clears an age gate.
  `HLX-` + 8 hex is 4 bn codes, so guessing is not the worry; **shoulder-surfing and screenshots
  are.** Decide explicitly whether a scanned card alone may clear 18+, or whether it clears
  loyalty and the cashier still eyeballs the person. *Recommend: the card clears the gate, because
  a control nobody uses is worth nothing — but the decision should be written down, not inherited.*
- **A stored DOB is still personal data under the FADP**, name or no name. Lower risk, not zero.
  Worth one sanity check with whoever advises Felix before it is on a card in a customer's pocket.
- **`CustomerModel` is full of inherited monster-repo furniture** — `crack_level`, `crack_team`,
  `kbs_written`, `kb_credits_earned`, a `CRACK` docstring. Harmless (all defaulted or nullable) but
  it is noise in every screen that renders a member, and it will read as strange to a shop owner
  cloning this. Not a blocker; worth a tidy pass someday.
- **This has NOT been discussed with Felix beyond the sentence at the top.** The DOB requirement in
  particular is a real ask of a customer who came in wanting to give nothing. Test the sentence
  *"scan this and we never ask for your ID again"* on him before building anything.
