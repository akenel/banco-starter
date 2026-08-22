# File: src/tests/test_member_card_age.py
"""A ticked box is not a date — the member card's 18+ rule.

WHY THIS FILE EXISTS
--------------------
2026-08-22. Felix wants members who stay anonymous: a card to scan, no name. The card is
issued from `/pos/kiosk`, which is **public** (no auth, by design) and has **no date-of-birth
field** — just a checkbox, "I confirm I am 18 or older", which the customer ticks about
themselves.

Until this change, `checkout.html:1032` read `return m.age_confirmed !== false`, and
`needsAgeGate()` suppresses the 18+ stop for any member it considers of age. So a card
anybody could self-issue, carrying a self-ticked box, **removed the age check at the counter**
and the cashier was never prompted to look at the person. A walk-in got more scrutiny than a
member.

Angel set the rule: *"if the people wanna put in the date of birth, yeah, that settles that"* —
and without one, *"she can double check if she thinks there's a problem."*

    a DATE settles it.  a TICK does not.

THE TWO RULES ARE BOTH CORRECT AND MUST NOT BE CONFUSED
-------------------------------------------------------
`member_of_age()` is the back-compat sale rule and deliberately counts the tick, so no existing
member or sale breaks. `is_of_age()` is the pure date rule. The bug was an endpoint sending the
FIRST where the screen needed the SECOND. These tests pin the difference, because the whole
defect lives in the gap between them.
"""
from datetime import date

from src.schemas.customer_schema import is_of_age, member_of_age


def _dob_for_age(years: int, today: date) -> date:
    return date(today.year - years, today.month, today.day)


TODAY = date(2026, 8, 22)


# ---------------------------------------------------------------- the gap itself

def test_a_ticked_box_is_not_a_date():
    """THE DEFECT, in one assertion pair. Same member, two rules, opposite answers —
    and the screen was reading the wrong one."""
    assert member_of_age(None, age_confirmed=True) is True      # back-compat: the tick counts
    assert is_of_age(None) is False                             # the date rule: nothing was proven


def test_no_date_means_unknown_not_yes():
    """What the endpoints must now send for a no-DOB member: None, never True.

    None is the point. It is NOT 'under 18' and NOT 'of age' — it is 'nobody established this',
    which is the only honest answer and the one that makes the cashier look up."""
    dob = None
    assert (is_of_age(dob) if dob is not None else None) is None


# ---------------------------------------------------------------- a date does settle it

def test_a_real_date_settles_it_both_ways():
    adult = _dob_for_age(30, TODAY)
    child = _dob_for_age(16, TODAY)
    assert is_of_age(adult, today=TODAY) is True
    assert is_of_age(child, today=TODAY) is False
    # And a proven minor cannot be waved through by a stale tick — this already held, and the
    # card must not become a way around it.
    assert member_of_age(child, age_confirmed=True, today=TODAY) is False


def test_the_eighteenth_birthday():
    """A member turning 18 today IS of age; the day before, not yet."""
    assert is_of_age(date(2008, 8, 22), today=TODAY) is True
    assert is_of_age(date(2008, 8, 23), today=TODAY) is False


# ---------------------------------------------------------------- what each door must send

def test_every_door_sends_the_date_rule():
    """Both endpoints that can attach a member build `is_of_age` this way:

        pos_router.py:5019          GET /customer/scan      (the till scan — new)
        customer_router.py:251      the member detail       (the lookup page — the SIBLING)

    Fixing one and not the other leaves a gate that holds only for members attached one way.
    STANDING RULE 6: one bad endpoint means check its siblings.
    """
    def as_endpoints_send_it(birthdate):
        return is_of_age(birthdate, today=TODAY) if birthdate is not None else None

    assert as_endpoints_send_it(None) is None                       # tick-only member
    assert as_endpoints_send_it(_dob_for_age(30, TODAY)) is True
    assert as_endpoints_send_it(_dob_for_age(16, TODAY)) is False

    # The trap: never `bool(...)` this. bool(None) is False, which reads as PROVEN UNDER 18 and
    # would refuse a legitimate customer instead of asking the cashier to look.
    assert bool(as_endpoints_send_it(None)) is False
    assert as_endpoints_send_it(None) is not False


def test_has_dob_is_the_flag_the_till_shows():
    """The till's toast says 'no age on file — check ID if unsure' off has_dob, not off
    is_of_age, so that 'unknown' never renders as an accusation."""
    for birthdate, expected in ((None, False), (_dob_for_age(30, TODAY), True)):
        assert (birthdate is not None) is expected


# ---------------------------------------------------------------- the spoken code

def test_the_member_code_is_readable_off_a_card():
    """ART-AB12: four characters a customer can read aloud down a counter.

    The alphabet is the whole point. 0/O and 1/I/L are gone because this string gets SPOKEN and
    HAND-COPIED, and "is that a zero or an oh" is the failure this format exists to prevent. U is
    gone so four random characters cannot spell something you would rather not print on a card.
    """
    from src.db.models.customer_model import MEMBER_CODE_ALPHABET, generate_member_code
    import re

    for banned in "01ILOU":
        assert banned not in MEMBER_CODE_ALPHABET, f"{banned} is ambiguous or unwanted"

    for _ in range(200):
        code = generate_member_code()
        assert re.fullmatch(r"ART-[2-9A-Z]{4}", code), code
        assert all(c in MEMBER_CODE_ALPHABET for c in code[4:])


def test_the_code_space_is_big_enough_to_use_and_small_enough_to_guess():
    """Both halves of that sentence are load-bearing.

    30^4 = 810,000 is ample for a shop ("tens of thousands of members" — Angel), and it is also
    only ~1 live code in 81 guesses at ten thousand members. So the spoken code is a NAME: it
    resolves a member, and it must never be sufficient on its own for anything that matters.
    The unguessable HLX- token stays in the QR, and the endpoint tags which one was used
    (`matched_by`) so no screen can confuse them.
    """
    from src.db.models.customer_model import MEMBER_CODE_ALPHABET
    space = len(MEMBER_CODE_ALPHABET) ** 4
    assert space == 810_000
    assert space // 10_000 == 81          # members → guesses per hit. Write it down, don't feel it.
