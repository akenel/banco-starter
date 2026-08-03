"""An empty text box is "not given", not a value — and for the UNIQUE columns that is a 500.

Found by Angel in the cashier-shift role-play, 2026-08-03. He was testing B5 ("a member whose
date of birth makes them under 18 is blocked outright") and got:

    PUT https://banco.wolfhold.app/api/v1/customers/0a406015-… 500 (Internal Server Error)

It looked like the age gate rejecting an under-age date of birth, because that is exactly what
he was testing. It had nothing to do with age.

`email`, `instagram` and `qr_code` are UNIQUE and nullable. NULL is exempt from a unique index;
the empty string is not. The edit-profile form posts every box it renders, so a member saved
with the contact boxes left blank stores `''` — and the SECOND such member collides with the
first. IntegrityError, uncaught, 500.

Reproduced on a live database before the fix: first save 200, second save 500. On the dev box
it had never shown up, because there was only ever one member with a blank email.

These pin the coercion at the schema layer, where it belongs — the endpoint never sees ''.
"""
import pytest
from pydantic import ValidationError

from src.schemas.customer_schema import CustomerCreate, CustomerUpdate, member_of_age
from datetime import date


BLANKABLE = ["real_name", "email", "phone", "instagram", "telegram", "whatsapp", "notes"]


@pytest.mark.parametrize("field", BLANKABLE)
def test_a_blank_box_becomes_null_not_empty_string(field):
    """The whole bug in one assertion: '' must never reach a UNIQUE column."""
    m = CustomerUpdate(**{field: ""})
    assert getattr(m, field) is None, f"{field} kept '' — it will collide on a unique index"


@pytest.mark.parametrize("field", BLANKABLE)
def test_whitespace_only_is_also_not_a_value(field):
    """A space typed into a box and left there is still an empty box."""
    assert getattr(CustomerUpdate(**{field: "   "}), field) is None


def test_the_exact_payload_the_edit_form_posts(field=None):
    """Angel's actual case: every contact box empty, an under-18 DOB, tier on Auto."""
    m = CustomerUpdate(handle="xyz", real_name="", email="", instagram="", telegram="",
                       phone="", notes="", birthdate="2016-08-01", age_confirmed=True,
                       loyalty_tier="auto")
    assert m.email is None and m.instagram is None
    assert m.birthdate == date(2016, 8, 1)      # the date itself is kept — only blanks drop
    assert m.handle == "xyz"


def test_create_coerces_too_so_enrolment_cannot_poison_the_index():
    """The 500 surfaced on edit, but enrolment posts the same empty boxes. Fixing only the
    update would leave the first '' to be written by the NEXT new member instead."""
    m = CustomerCreate(handle="newbie", email="", instagram="")
    assert m.email is None and m.instagram is None


def test_a_real_value_is_untouched():
    """The coercion must not be clever. Only blank means blank."""
    m = CustomerUpdate(email="larry@artemis.ch", instagram="@poppie_420", notes="knows his hash")
    assert m.email == "larry@artemis.ch"
    assert m.instagram == "@poppie_420"
    assert m.notes == "knows his hash"


def test_zero_and_false_are_not_blanks():
    """A string that is falsy in Python but meaningful to a human — '0' is a real phone digit."""
    assert CustomerUpdate(phone="0").phone == "0"


def test_the_thing_angel_was_actually_testing_still_holds():
    """B5 itself: a DOB proving under 18 beats a stale age_confirmed=True. The 500 was hiding
    this, not causing it — the rule was right the whole time."""
    assert member_of_age(date(2016, 8, 1), age_confirmed=True, today=date(2026, 8, 3)) is False
    assert member_of_age(date(2000, 1, 1), age_confirmed=False, today=date(2026, 8, 3)) is True
    # legacy members with no DOB still ride on age_confirmed, so nothing breaks
    assert member_of_age(None, age_confirmed=True, today=date(2026, 8, 3)) is True


def test_unset_fields_stay_unset():
    """exclude_unset drives the endpoint's update loop — coercion must not accidentally
    materialise every field and blank a member's real email on an unrelated edit."""
    m = CustomerUpdate(notes="just a note")
    assert "email" not in m.model_dump(exclude_unset=True)
