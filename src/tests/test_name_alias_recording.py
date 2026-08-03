"""The packet name survives the merge — the missing half of the alias loop.

Since 2026-07-31 `_name_match_candidates` searches `product_translations.name` alongside
`products.name`, which is what lets a `black` search find a `schwarz` row. But nothing ever
WROTE that column: the only writer was `ensure_description`, and it fills names as a side
effect of fetching descriptions from Tamar. So the reader shipped pointed at a table that,
for a hand-captured product, was always empty.

The name it should have been reading is the one `POST /catalog/merge` was throwing away.
The retiring row is the hand-made one — somebody stood at a counter with the box and typed
what it said, in the language it said it in:

    keep     Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz   (TAM-20350, imported)
    retire   Blow Pre-built CBD Joint Pure "V1" 1 pc. black        (hand-made, real EAN)

The merge moves the EAN across and deactivates the twin. Everything else it owned moves;
the English name was dropped on the floor at the exact moment we finally knew which product
it belonged to.

These pin the rules that stop the fix from destroying better data than it brings.
"""
import uuid

import pytest
from sqlalchemy import select

from src.db.models.product_model import ProductModel, ProductTranslationModel
from src.services.product_translations import record_name_alias

DE = 'Blow vorgebauter CBD Joint Pure "V1" 1 Stk. schwarz'
EN = 'Blow Pre-built CBD Joint Pure "V1" 1 pc. black'


async def _make_product(db, name: str) -> ProductModel:
    p = ProductModel(sku=f"TAM-{uuid.uuid4().hex[:6]}", name=name, price=9.90)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def _skins(db, product) -> list[ProductTranslationModel]:
    return list((await db.execute(
        select(ProductTranslationModel).where(
            ProductTranslationModel.product_id == product.id))).scalars().all())


@pytest.mark.asyncio
async def test_the_english_packet_name_is_recorded_against_the_german_row(db_session):
    """The whole point: after this, searching the product in English finds it."""
    keep = await _make_product(db_session, DE)

    out = await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    assert out["recorded"] is True
    skins = await _skins(db_session, keep)
    assert len(skins) == 1
    assert skins[0].name == EN
    assert skins[0].provenance == "operator"
    # ONE column. A name alias knows nothing about the description and must not invent one.
    assert skins[0].description is None


@pytest.mark.asyncio
async def test_a_confident_german_name_is_filed_as_german_and_not_flagged(db_session):
    """`_guess_base_lang` commits to 'de' on a German function word ("mit"), so that is
    knowledge, not a guess — and knowledge is not stamped needs_review."""
    keep = await _make_product(db_session, "Gizeh King Size Slim")

    out = await record_name_alias(
        db_session, keep, "Gizeh Blättchen mit Aktivkohle Filter, Packung")
    await db_session.commit()

    assert out["lang"] == "de"
    assert out["assumed_lang"] is False
    assert (await _skins(db_session, keep))[0].needs_review is False


@pytest.mark.asyncio
async def test_an_assumed_language_is_flagged_rather_than_claimed(db_session):
    """`_guess_base_lang` only ever commits to German. Everything else falls to 'en' as an
    ASSUMPTION — and the codebase's standing rule is never to claim authority on a guess, so
    it lands needs_review. A French packet name filed under 'en' is then visible as suspect
    instead of quietly serving French to English users."""
    keep = await _make_product(db_session, DE)

    out = await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    assert out["lang"] == "en" and out["assumed_lang"] is True
    assert (await _skins(db_session, keep))[0].needs_review is True


@pytest.mark.asyncio
async def test_an_existing_name_is_never_overwritten(db_session):
    """A real per-language skin outranks an alias scraped off a retiring twin. Overwriting is
    how a good translation gets replaced by whatever someone typed at a till in a hurry."""
    keep = await _make_product(db_session, DE)
    db_session.add(ProductTranslationModel(
        product_id=keep.id, lang="en", name="Blow Pre-rolled CBD Joint Pure V1 black",
        description="The proper English description.", provenance="source", needs_review=False))
    await db_session.commit()

    out = await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    assert out["recorded"] is False and "not overwritten" in out["why"]
    skins = await _skins(db_session, keep)
    assert len(skins) == 1
    assert skins[0].name == "Blow Pre-rolled CBD Joint Pure V1 black"
    assert skins[0].description == "The proper English description."
    assert skins[0].provenance == "source"       # not restamped 'operator'


@pytest.mark.asyncio
async def test_a_blank_name_on_an_existing_skin_is_filled_without_disturbing_it(db_session):
    """The common real shape: `ensure_description` already cached a machine-translated
    description with name=NULL. Fill the hole, touch nothing else — in particular do not
    restamp provenance, which describes that row's DESCRIPTION, not our name."""
    keep = await _make_product(db_session, DE)
    db_session.add(ProductTranslationModel(
        product_id=keep.id, lang="en", name=None,
        description="Machine-translated text.", provenance="machine", needs_review=True))
    await db_session.commit()

    out = await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    assert out["recorded"] is True
    skins = await _skins(db_session, keep)
    assert len(skins) == 1
    assert skins[0].name == EN
    assert skins[0].description == "Machine-translated text."
    assert skins[0].provenance == "machine"


@pytest.mark.asyncio
async def test_the_same_name_in_different_dress_is_not_an_alias(db_session):
    """Case and punctuation carry no new information, and a row that teaches the search
    nothing is just a row to maintain. NOTE this is a LITERAL comparison, not the DE↔EN
    folding used for matching — folding here would discard the exact alias we came for."""
    keep = await _make_product(db_session, 'Gizeh King Size Slim')

    for variant in ("gizeh king size slim", "GIZEH  King-Size Slim!", "Gizeh King Size Slim"):
        assert await record_name_alias(db_session, keep, variant) is None
    assert await _skins(db_session, keep) == []


@pytest.mark.asyncio
async def test_recording_the_same_alias_twice_is_a_no_op(db_session):
    keep = await _make_product(db_session, DE)
    await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    out = await record_name_alias(db_session, keep, EN)
    await db_session.commit()

    assert out["recorded"] is False and out["why"] == "already recorded"
    assert len(await _skins(db_session, keep)) == 1


@pytest.mark.asyncio
async def test_nothing_to_record_is_not_an_error(db_session):
    """A retiring row with no name at all must not blow up a merge that is otherwise fine."""
    keep = await _make_product(db_session, DE)
    for empty in (None, "", "   ", "<br/>"):
        assert await record_name_alias(db_session, keep, empty) is None


@pytest.mark.asyncio
async def test_dry_run_reports_the_plan_and_writes_nothing(db_session):
    """This is what feeds the merge's `dry_run` plan, and the merge's whole promise is that a
    dry run touches nothing — including here."""
    keep = await _make_product(db_session, DE)

    out = await record_name_alias(db_session, keep, EN, dry_run=True)
    await db_session.commit()

    assert out == {"recorded": True, "lang": "en", "name": EN,
                   "assumed_lang": True, "dry_run": True}
    assert await _skins(db_session, keep) == []


@pytest.mark.asyncio
async def test_it_does_not_commit_so_a_failed_merge_takes_it_down_too(db_session):
    """The alias must live or die with the merge that produced it. If it committed on its own,
    a merge that then hit the barcode-conflict 409 and rolled back would leave a name recorded
    against a product that never absorbed the twin."""
    keep = await _make_product(db_session, DE)
    pid = keep.id                      # the rollback expires the instance; the row still exists

    await record_name_alias(db_session, keep, EN)
    await db_session.rollback()

    left = (await db_session.execute(select(ProductTranslationModel).where(
        ProductTranslationModel.product_id == pid))).scalars().all()
    assert list(left) == []
