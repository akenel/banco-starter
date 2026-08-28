import contextvars
import logging
import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Iterator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, event, text
from src.db.models.base import Base
from src.core.config import get_settings

# Import all models so they register with Base.metadata for Alembic
from src.db.models import (  # noqa: F401
    UserModel,
    TeamModel,
    RefreshTokenModel,
    JobModel,
    TaskModel,
    ArtifactModel,
    MessageTaskModel,
    PipelineTaskModel,
    InitializerModel,
    ProductModel,
    TransactionModel,
    LineItemModel,
    # CRACK Loyalty Models
    CustomerModel,
    KBContributionModel,
    CreditTransactionModel,
    # HR/Payroll Models (BLQ Module)
    EmployeeModel,
    TimeEntryModel,
    PayrollRunModel,
    PaySlipModel,
    # Camper & Tour Service Management
    CamperVehicleModel,
    CamperCustomerModel,
    CamperServiceJobModel,
    # QA Testing Dashboard
    QATestResultModel,
    QABugReportModel,
    # LPCX -- La Piazza Compute Exchange
    ComputeJobModel,
    ComputeLedgerModel,
    ComputeTemplateModel,
    ComputeNodeModel,
    BottegaProfileModel,
    BottegaProfileHistoryModel,
)

logger = logging.getLogger("app/db/database.py 🪵️")
logger.setLevel(logging.INFO)
settings = get_settings()

# ================================================================
# ⚙️ ENGINE DEFINITIONS
# ================================================================
async_engine: Optional[AsyncEngine] = create_async_engine(
    settings.POSTGRES_ASYNC_URI,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

SyncSessionLocal: Optional[sessionmaker] = None

# ================================================================
# 🪪 AUDIT ACTOR — tell the DB *who* is making each change, per request,
# so the audit_log triggers (scripts/db/audit_log_setup.sql) record the real
# user instead of 'system'. verify_token() sets the contextvar on every
# authenticated request; the after_begin event copies it onto each transaction
# as the `app.actor` GUC, which audit_capture() reads. Unauthenticated /
# background / CLI writes leave it unset → they log as 'system'.
# ================================================================
_audit_actor: contextvars.ContextVar = contextvars.ContextVar("audit_actor", default="")


def set_audit_actor(username: Optional[str]) -> None:
    """Per authenticated request: stash WHO, so DB audit triggers attribute the change."""
    try:
        _audit_actor.set((username or "").strip()[:120])
    except Exception:
        pass


@event.listens_for(Session, "after_begin")
def _apply_audit_actor(session, transaction, connection) -> None:
    """On every transaction begin, set app.actor so audit_capture() records the real
    user. Defensive by design — this must NEVER be able to break a real transaction."""
    try:
        actor = _audit_actor.get()
        if actor:
            connection.execute(text("SELECT set_config('app.actor', :a, true)"), {"a": actor})
    except Exception:
        pass

# ================================================================
# 🔗 ASYNC SESSION DEPENDENCY
# ================================================================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

# ================================================================
# 💉 CONTEXT MANAGER
# ================================================================
@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

# ================================================================
# 🧱 INITIALIZATION
# ================================================================
async def init_db_tables() -> None:
    """Ensure all ORM models are registered and create missing tables."""
    async with async_engine.begin() as conn:
        logger.info("Checking database for missing tables and attempting creation...")
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_lightweight_columns()
    logger.info("✅ Database table initialization complete.")


# Idempotent, additive-only column migrations for tables that already exist.
# create_all() only makes MISSING tables -- it never adds columns to a table that
# is already there. These ALTERs run on every env (not debug-gated) and are safe on
# a shared DB: ADD COLUMN IF NOT EXISTS is non-destructive and backward-compatible
# (older code that doesn't select the column is unaffected). Postgres only.
_ADDITIVE_COLUMNS: list[str] = [
    # The join-now offer is the SHOP's number (2026-08-23). Defaults reproduce exactly what was
    # hardcoded before — 10% at the kiosk, 15% on a phone — so this migration changes nothing
    # until Felix changes it. 0 turns the offer off and the kiosk copy follows.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS welcome_discount_kiosk_pct INTEGER NOT NULL DEFAULT 10",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS welcome_discount_phone_pct INTEGER NOT NULL DEFAULT 15",
    # Today "breakdowns" block (2026-06-12): sub-tasks, time, assignee, edit history.
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS parent_id UUID",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS estimate_min INTEGER",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS assignee VARCHAR(100)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS house VARCHAR(60)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS collaborators TEXT",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS history TEXT",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS project VARCHAR(40)",
    "ALTER TABLE bottega_tasks ADD COLUMN IF NOT EXISTS task_key VARCHAR(60)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_parent_id ON bottega_tasks (parent_id)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_assignee ON bottega_tasks (assignee)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_house ON bottega_tasks (house)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_project ON bottega_tasks (project)",
    "CREATE INDEX IF NOT EXISTS ix_bottega_tasks_task_key ON bottega_tasks (task_key)",
    # BYOH (2026-06-16): a node reports its probed capabilities (tools, ram, gpu) so
    # the Provider Console can show the no-surprises "what can this box run" window.
    "ALTER TABLE compute_nodes ADD COLUMN IF NOT EXISTS caps_json TEXT",
    # Feedback screenshots (2026-06-21): the POS 💬 widget can attach an auto-captured
    # screenshot (base64 data-URL) to a backlog item. Heavy text, deferred-loaded.
    "ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS screenshot_data TEXT",
    # Feedback attachments (2026-06-21): the 💬 widget can now attach files (images
    # AND PDFs) chosen from the device or shot with the mobile camera, beyond the
    # single auto-captured screenshot. Stored as a JSON list. Heavy text, deferred.
    "ALTER TABLE backlog_items ADD COLUMN IF NOT EXISTS attachments TEXT",
    # CRM Phase 0 (2026-06-21): age gate + marketing consent on customers (the only
    # compliance must -- 18+; marketing default off per Swiss FADP).
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS age_confirmed BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN NOT NULL DEFAULT FALSE",
    # Age gate — full DOB (2026-07-01): the authoritative 18+ age source on the sale path
    # (walk-in attestation is the other leg). Nullable DATE, NO default -> every existing
    # member row stays NULL and is treated as of-age via age_confirmed (member_of_age()),
    # so this never breaks an existing member or sale. Also carries the birthday-rewards
    # fast-follow. NOTE: the pre-existing `birthday` column (2x-points marketing week) was
    # on the model but had NO ALTER here (create_all never adds columns to an existing
    # table) — added below so an env whose `customers` predated it doesn't 500 on enroll.
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS birthdate DATE",
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS birthday DATE",
    # Kiosk self-signup (2026-07-15): one-time first-order discount + where they enrolled.
    # NOT NULL DEFAULT 0/FALSE so every existing member row is valid (they simply have no
    # welcome discount). signup_source nullable (legacy members enrolled before the kiosk).
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS welcome_discount_pct INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS welcome_discount_used BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE customers ADD COLUMN IF NOT EXISTS signup_source VARCHAR(20)",
    # BL-082 (2026-06-21): the IsottoOrder model grew team-order fields but there was
    # no additive migration -- create_all() never adds columns to an existing table, so
    # any env whose isotto_orders predated these 500'd on insert (seed crash + dead
    # ISOTTO order feature). These are the only two columns the model has that the live
    # table lacked (verified by diffing the model against information_schema).
    "ALTER TABLE isotto_orders ADD COLUMN IF NOT EXISTS is_team_order BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE isotto_orders ADD COLUMN IF NOT EXISTS team_name VARCHAR(200)",
    # BL-96 taxonomy (2026-06-25): product CLASS (behaviour — age/VAT/compliance) on products,
    # and the reclassify enricher's mapping on the reference catalogue (our skeleton category +
    # class + 18+ flag) so adopting a reference item carries category, class AND the age gate.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_class VARCHAR(40) NOT NULL DEFAULT 'standard'",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS our_category VARCHAR(60)",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS our_class VARCHAR(40)",
    "ALTER TABLE reference_products ADD COLUMN IF NOT EXISTS age_restricted BOOLEAN NOT NULL DEFAULT FALSE",
    # BL-35 wholesale-vs-competitor labeling (2026-07-12): what a supplier site's price MEANS —
    # 'wholesale' = your COST, 'retail' = a competitor's MARKET price, 'both'. Every existing
    # supplier backfills to 'wholesale' (they're where you buy); tag the retail/both ones after.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS supplier_role VARCHAR(12) NOT NULL DEFAULT 'wholesale'",
    # Banco store profile (2026-06-22): hours + social links on store_settings.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS opening_hours VARCHAR(500)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS facebook_url VARCHAR(255)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS instagram_url VARCHAR(255)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS founded_year VARCHAR(10)",
    # Fiscal regime seam (PHASE 0, 2026-07-01, Go-Italian): per-tenant regime/currency/locale
    # on store_settings. NOT NULL DEFAULT backfills every existing row to CH (no data step),
    # keeping a CH tenant byte-identical. Defaults are LITERAL-identical to StoreSettingsModel
    # (fiscal_regime='CH' / currency='CHF' / locale='de-CH'). Same proven VARCHAR(N) NOT NULL
    # DEFAULT idiom as product_class above.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS fiscal_regime VARCHAR(8) NOT NULL DEFAULT 'CH'",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS currency VARCHAR(8) NOT NULL DEFAULT 'CHF'",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS locale VARCHAR(12) NOT NULL DEFAULT 'de-CH'",
    # N-rate VAT table editor (Piece C, 2026-07-01, Go-Italian): the tenant's editable rate menu as
    # a JSON string on store_settings. NULLABLE, DEFAULT NULL — every existing row stays NULL and the
    # VAT engine falls back to the CH config default table, so a CH shop is BYTE-IDENTICAL to today.
    # Only persisted when the shop opens the Settings → Tax editor and saves. Additive TEXT, same
    # proven idiom as the JSON blobs above (caps_json / attachments).
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS vat_rates TEXT",
    # 🌍-1 payments seam (2026-07-18): the electronic terminal provider per store. NOT NULL
    # DEFAULT 'manual' backfills every existing row to today's behaviour (no terminal, cashier
    # takes payment by hand) — byte-identical. 'worldline' lights up the seam in M2. Same proven
    # VARCHAR(N) NOT NULL DEFAULT idiom as fiscal_regime above. See docs/SPEC-payments-seam.md.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS payment_provider VARCHAR(16) NOT NULL DEFAULT 'manual'",
    # Currency plan-rates (2026-07-13): flat FX table {base, rates, as_of} for showing a foreign
    # supplier price in the shop's currency (Near Dark EUR → ≈ CHF). NULLABLE — NULL falls back to
    # currency.DEFAULT_FX, so a shop is byte-identical until it sets its own plan rates. Same
    # additive TEXT-JSON idiom as vat_rates.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS fx_rates TEXT",
    # Shop's own SKU prefix for house/no-supplier goods (receiving mints PREFIX-#### from it).
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS house_sku_prefix VARCHAR(8)",
    # was created via create_all only → drifted (missing on banco_staging, caused a 500 on every
    # store_settings read). Idempotent here so every env converges on deploy.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS default_markup_pct NUMERIC(5,2) NOT NULL DEFAULT 50.0",
    # Short links for scannable QR (2026-07-13): the postcard QR encodes /p/{short_code} instead of
    # the full /pos/products/{uuid}/postcard so the QR stays low-density → scans reliably even printed
    # ~20mm on a label. short_code minted lazily on first postcard render, unique among non-nulls
    # (Postgres counts NULLs distinct → backfill is a no-op). qr_scan_count/qr_last_scanned_at make the
    # QR trackable (a scan bumps the counter) — free analytics off every label.
    # DEPARTMENT KEYS (2026-08-07, docs onboarding/ai-coach/SPEC-department-keys.md). Selling the
    # ~30% of stock with no barcode: a line with product_id NULL + a department bucket. Both are
    # NULLABLE with no default, so every existing line item and every catalog line rung after this
    # is byte-identical -- the columns simply stay NULL. `catalog_miss` itself is a NEW table and
    # so is made by create_all(); only these two columns need an ALTER.
    "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS department_code VARCHAR(8)",
    "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS unresolved_barcode VARCHAR(64)",
    "CREATE INDEX IF NOT EXISTS ix_line_items_department_code ON line_items (department_code)",
    # The honest "no" for the cost done-flag (2026-08-21). Nullable, no default: every existing
    # row stays byte-identical and simply carries NULL, which reads as "nobody has answered yet".
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS no_cost_reason VARCHAR(32)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS short_code VARCHAR(16)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_scan_count INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_last_scanned_at TIMESTAMPTZ",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_products_short_code ON products (short_code)",
    # Offline outbox idempotency (P2.1, 2026-06-29): the atomic create-sale endpoint keys
    # on a client-generated UUID so a replayed sale (network retry / offline outbox sync)
    # is adopted exactly once, never double-rung. Nullable (legacy 3-step sales have none);
    # the index is UNIQUE among non-null values — Postgres counts NULLs as distinct, so the
    # backfill is a no-op and existing rows never collide. (Mirrors TransactionModel.client_uuid.)
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS client_uuid UUID",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_client_uuid ON transactions (client_uuid)",
    # Multi-currency tender (Block 1, 2026-07-18): foreign-cash detail on the sale. All nullable —
    # NULL = paid in the home currency, byte-identical to today. total/subtotal/tax stay home currency;
    # amount_tendered/change_given are the home-currency equivalents. See docs/SPEC-multi-currency-tender.md.
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tender_currency VARCHAR(8)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tender_amount NUMERIC(12,2)",
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS tender_rate NUMERIC(12,6)",
    # Swiss 5-rappen cash rounding (2026-08-03). NOT NULL DEFAULT 0 is TRUE for every existing
    # row, not merely convenient: nothing was ever rounded before this shipped, so 0.00 is the
    # honest value and no backfill is needed. `total` stays "what was actually charged" — this
    # only records how far the cash rounding moved it, so a receipt can say `Rounding -0.04`
    # rather than leaving an unexplained rappen in the drawer. Postgres 11+ adds a defaulted
    # NOT NULL column without rewriting the table, so this is fast on a live shop.
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS rounding_adjustment NUMERIC(10,2) NOT NULL DEFAULT 0",
    # THE CASH BOX IS THE SHOP'S (2026-08-03) — onboarding/12-the-cash-box.md.
    # One physical box, one open shift, everybody sells into it. user_id/username keep their
    # column names but now mean "opened by" rather than "owner", so NO data migration is
    # needed: only the meaning changed, and the schema never enforced the old one.
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS reconciled_by VARCHAR(100)",
    # The blind count + the reveal. All nullable — every shift closed before this simply has
    # no morning-reveal story, which is the truth, not a gap to backfill.
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS opening_expected NUMERIC(10,2)",
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS opening_variance NUMERIC(10,2)",
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS opening_note TEXT",
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS previous_shift_id UUID",
    # The forced close (§5). counted_verified DEFAULT TRUE is TRUE for history: every shift
    # closed before this existed was closed by a person with the box in front of them. The one
    # exception on prod (pam's administrative close) is corrected explicitly below.
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS counted_verified BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE cash_shifts ADD COLUMN IF NOT EXISTS forced_close BOOLEAN NOT NULL DEFAULT FALSE",
    # Retro-flag the ONE row that was closed without anybody counting it (prod, 2026-08-03
    # 14:12). §5 says the fact belongs in a column, not in prose — so put it there rather than
    # leaving the note as the only record. Matches on the note text so it can never hit a real
    # count, and is a no-op on every other environment.
    "UPDATE cash_shifts SET counted_verified = FALSE, forced_close = TRUE "
    "WHERE variance_note LIKE 'ADMINISTRATIVE CLOSE - THE DRAWER WAS NEVER PHYSICALLY COUNTED.%' "
    "AND counted_verified IS TRUE",
    # A drop is not petty cash (§7.3): money leaves the drawer but not the business, so it must
    # never be booked as an expense. A code, not free text — correct by construction.
    "ALTER TABLE cash_movements ADD COLUMN IF NOT EXISTS reason_code VARCHAR(20)",
    # The baseline (§6): what the box is INTENDED to carry, as opposed to what is in it now.
    # Nullable — an unconfigured shop gets no guard rather than a guessed one.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS cash_box_float NUMERIC(10,2)",
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS cash_box_float_note TEXT",
    # Shop-configurable variance tolerance. NULL = the 0.20 legacy default, so nothing changes
    # for an existing shop until somebody sets it. ±0.05 (one coin) only became achievable once
    # cash totals started rounding to 0.05 at checkout.
    "ALTER TABLE store_settings ADD COLUMN IF NOT EXISTS cash_tolerance NUMERIC(10,2)",
    # Artemis enriched-catalog foundation (2026-06-30, migration 010): store the enriched
    # record losslessly on products + a per-language translations table (the latter is a
    # NEW table, created by create_all() — only the column adds need ALTERs here).
    # Flat hierarchy (group + category on the row; full path in tags + artemis_path) — §9.1.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS product_group VARCHAR(60)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS age_reason VARCHAR(80)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode_is_internal BOOLEAN NOT NULL DEFAULT FALSE",
    # §6a rich metadata + verbatim source facets (lossless), and enrichment provenance.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS attributes JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS raw_facets JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_confidence JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_flags JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS enrichment_meta JSONB",
    # BL-26: per-product quantity-break (tier) pricing — [{min_qty, unit_price}, ...].
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS price_tiers JSONB",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS tier_mode VARCHAR(12)",
    # BL-18: description-backfill rotation marker (stamped on every scrape attempt).
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS description_checked_at TIMESTAMPTZ",
    # BL-17: image-backfill rotation marker (stamped on every hotlink-migration attempt).
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS image_checked_at TIMESTAMPTZ",
    # Source provenance / parity link (§9.6 'View on Artemis') + §6d translation seam.
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_system VARCHAR(40)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_id VARCHAR(64)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_lang VARCHAR(8)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS artemis_path VARCHAR(255)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS needs_translation BOOLEAN NOT NULL DEFAULT FALSE",
    # §6c SHARE rail permalink (QR target).
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS qr_url VARCHAR(500)",
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS work_note TEXT",
    "CREATE INDEX IF NOT EXISTS ix_products_product_group ON products (product_group)",
    "CREATE INDEX IF NOT EXISTS ix_products_source_id ON products (source_id)",
    # Supplier Registry (2026-06-30, migration 011): formalize each import SOURCE as a
    # supplier row keyed by a unique SKU prefix (TAM-=Tamar/Artemis, FTW-=FourTwenty,
    # future CSV/manual). The `suppliers` table already exists (legacy Sourcing System,
    # created by create_all) — these are the additive registry columns. Prefix is the
    # authoritative key: 2-3 uppercase letters, UNIQUE (the index below backstops the
    # Pydantic validator), nullable so legacy rows (420/WR/ND/Hem) carry none.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS prefix VARCHAR(3)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(40)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_name VARCHAR(120)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)",
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50)",
    # Succession/handoff: VAT + named contact so the supplier isn't trapped in one head.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS vat_number VARCHAR(50)",
    # Trade discount off retail (%, 0-100). Receiving auto-fills cost = retail × (1 − pct/100)
    # — the Ecolution deal (pay 70% of Sylvie's Etsy shelf price). Nullable = no deal set.
    "ALTER TABLE suppliers ADD COLUMN IF NOT EXISTS trade_discount_pct DOUBLE PRECISION",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_suppliers_prefix ON suppliers (prefix)",
    # 18+ EVIDENCE (2026-08-12) — the age gate always worked; it just never left a
    # record. _assert_age_cleared() rejects an unverified 18+ sale with 400 on both
    # sale paths, returns the method it used, and both call sites threw that away —
    # so the only trace was an app log line that rotates and dies on restart.
    # These two columns turn a control into evidence. Both NULLABLE with no default:
    # a legacy row must stay NULL rather than be retro-labelled with a check nobody
    # performed. (age_check_event is a new table, so create_all() makes it.)
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS age_check_outcome VARCHAR(24)",
    "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS was_age_restricted BOOLEAN",
    "CREATE INDEX IF NOT EXISTS ix_transactions_age_check ON transactions (age_check_outcome)",
    "CREATE INDEX IF NOT EXISTS ix_line_items_age_restricted ON line_items (was_age_restricted) WHERE was_age_restricted",
    # 18+ REFUSALS point at the CART, not a transaction number (2026-08-12, after the
    # sandbox run). age_check_event.txn_ref was being filled from /sales with a number
    # that is only allocated at COMMIT — a refused attempt never commits, so the next
    # sale took the number and the refusal appeared to belong to a stranger's purchase
    # (12 of 13, three of them with no 18+ line at all). client_uuid is the true handle
    # on an attempt and survives the error in the till's sessionStorage, so a refusal
    # and the retry that follows it carry the same one. Joins transactions.client_uuid.
    "ALTER TABLE age_check_event ADD COLUMN IF NOT EXISTS cart_ref VARCHAR(64)",
    "CREATE INDEX IF NOT EXISTS ix_age_check_event_cart ON age_check_event (cart_ref)",
    # BL-90b (2026-08-28): an alias barcode never said WHAT it was. Two gaps that matter.
    #
    # `kind` — the table's own docstring already anticipated "the retail EAN plus a
    # logistics/case code", but stored both identically, so nothing could tell the packet's
    # code from the code on the box of fifty. Backfilled 'retail' because that is what every
    # existing alias is: a code a human scanned off something in their hand.
    #
    # `pack_qty` — how many units the code covers. A WHOLESALER's GTIN is often the outer:
    # measured on the FourTwenty feed, 888 rows carry a code for 2+ units and ~a third of the
    # paper rows are boxes of 16/20/24/50. Binding one of those to a single packet makes the
    # till ring up a box. NULL = unknown, 1 = a single item.
    #
    # `source` — 'scanned' (a person held the packet) vs 'image-match' (a picture said so and
    # a person agreed). This is what lets shelf intake CLOSE THE LOOP: when a real packet
    # later resolves to an image-matched alias, the packet has just proved the guess and it
    # can be promoted. Without it, "which of my barcodes has never been near a physical
    # product?" is unanswerable, and that is the honest quality number for the catalogue.
    # Backfilled 'scanned' — every alias that exists today came from a gun.
    "ALTER TABLE product_barcodes ADD COLUMN IF NOT EXISTS kind VARCHAR(16) NOT NULL DEFAULT 'retail'",
    "ALTER TABLE product_barcodes ADD COLUMN IF NOT EXISTS pack_qty INTEGER",
    "ALTER TABLE product_barcodes ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'scanned'",
    "ALTER TABLE product_barcodes ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMPTZ",
    "ALTER TABLE product_barcodes ADD COLUMN IF NOT EXISTS evidence TEXT",
]


# Idempotent DDL that must exist on EVERY env (the migration-not-gated lesson:
# this was only ever set up on local, so POS fuzzy search 500'd on staging/prod).
# CREATE EXTENSION / OR REPLACE FUNCTION are safe to re-run on a shared DB.
_DDL_MIGRATIONS: list[str] = [
    # Custom POS line items (manual catalog entry, product-as-change treats) carry no
    # product_id -- the name lives in notes and the price is sent by the till. Drop the
    # NOT NULL so they can be stored. Idempotent (no-op once already nullable).
    "ALTER TABLE line_items ALTER COLUMN product_id DROP NOT NULL",
    # Giveaway flag: a 'treat' is a real product given free (zero revenue) but it
    # leaves inventory -- flagged so reports/accounting can track COGS for tax.
    "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS is_giveaway BOOLEAN NOT NULL DEFAULT FALSE",
    # (The Treats catalog INSERT moved to _DEMO_DDL below -- it is demo *content*,
    #  gated by HX_SEED_DEMO so the Banco Day-One sandbox boots with an empty shop.)
    # pg_trgm powers similarity() for the POS product search.
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    # GIN trigram index keeps fuzzy/ILIKE name search fast on a big (thousands) catalog.
    "CREATE INDEX IF NOT EXISTS ix_products_name_trgm ON products USING gin (name gin_trgm_ops)",
    # Category list for the search filter (the /search/categories endpoint expects this
    # view; it was missing -> 500, same pattern as search_products).
    """
    CREATE OR REPLACE VIEW product_categories AS
    SELECT category, count(*) AS product_count, avg(price) AS avg_price
    FROM products
    WHERE is_active = true AND category IS NOT NULL AND category <> ''
    GROUP BY category
    """,
    # Fuzzy + substring product search used by GET /api/v1/pos/search.
    """
    CREATE OR REPLACE FUNCTION public.search_products(
        search_term text, category_filter text DEFAULT NULL::text, limit_rows integer DEFAULT 50)
     RETURNS TABLE(id uuid, sku character varying, barcode character varying, name character varying,
        category character varying, price numeric, stock_quantity integer, image_url character varying, relevance real)
     LANGUAGE plpgsql
    AS $function$
    BEGIN
        RETURN QUERY
        SELECT p.id, p.sku, p.barcode, p.name, p.category, p.price, p.stock_quantity, p.image_url,
            similarity(p.name, search_term) AS relevance
        FROM products p
        WHERE p.is_active = true
            AND (
                p.name ILIKE '%' || search_term || '%'
                OR p.sku ILIKE '%' || search_term || '%'
                OR p.barcode ILIKE '%' || search_term || '%'
                OR similarity(p.name, search_term) > 0.1
            )
            AND (category_filter IS NULL OR p.category ILIKE '%' || category_filter || '%')
        ORDER BY
            CASE WHEN p.name ILIKE search_term || '%' THEN 0 ELSE 1 END,
            similarity(p.name, search_term) DESC, p.name
        LIMIT limit_rows;
    END;
    $function$
    """,
    # CRM Phase 0 (2026-06-21): the transactions.customer_id FK was pointing at users.id
    # (staff) -- WRONG; a loyalty sale belongs to a CRM customer. Repoint it to
    # customers.id. Idempotent: only acts if the correct FK isn't already present, so it
    # drops whatever wrong FK is on customer_id and adds the right one exactly once.
    """
    DO $$
    DECLARE badcon text; has_good boolean;
    BEGIN
        SELECT EXISTS (
            SELECT 1 FROM pg_constraint con
            JOIN pg_class fr ON fr.oid = con.confrelid
            JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
            WHERE con.conrelid = 'transactions'::regclass AND con.contype = 'f'
              AND a.attname = 'customer_id' AND fr.relname = 'customers'
        ) INTO has_good;
        IF NOT has_good THEN
            SELECT con.conname INTO badcon
            FROM pg_constraint con
            JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
            WHERE con.conrelid = 'transactions'::regclass AND con.contype = 'f'
              AND a.attname = 'customer_id' LIMIT 1;
            IF badcon IS NOT NULL THEN
                EXECUTE format('ALTER TABLE transactions DROP CONSTRAINT %I', badcon);
            END IF;
            ALTER TABLE transactions
                ADD CONSTRAINT transactions_customer_id_customers_fkey
                FOREIGN KEY (customer_id) REFERENCES customers(id);
        END IF;
    END $$;
    """,
    # BL-84 (2026-06-21): Felix asked for a bank-transfer payment type (invoice/IBAN
    # paid into the shop account). payment_method is a native PG enum whose labels are
    # the Python enum NAMES (CASH, VISA, ...), so the new label is 'BANK_TRANSFER'.
    # ADD VALUE IF NOT EXISTS is idempotent; PG 12+ allows it inside a transaction.
    "ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'BANK_TRANSFER'",
    # Supplier Registry seed (migration 011): the two known import sources. This is
    # FOUNDATION config (not demo content), so it lives here in the always-run block —
    # banco runs HX_SEED_DEMO=false, so _DEMO_DDL would skip it. Idempotent on the
    # unique prefix. `code` is the legacy NOT NULL unique column — mirror the prefix.
    # LZ stays a RESERVED internal code (not a row); the receiving 'LZ-' lazy-create
    # path already covers internal/manual items.
    """
    INSERT INTO suppliers (id, code, prefix, name, source_url, adapter_type, country,
        lead_time_days_min, lead_time_days_max, quality_rating, swiss_certified,
        is_active, supplier_role, created_at, updated_at)
    VALUES
      (gen_random_uuid()::text,'TAM','TAM','Tamar Trade GmbH','https://www.artemisluzern.ch','tamar','CH',1,5,'A',true,true,'wholesale',now(),now()),
      (gen_random_uuid()::text,'FTW','FTW','FourTwenty','https://fourtwenty.ch','magento','CH',1,5,'A',false,true,'both',now(),now())
    ON CONFLICT (prefix) DO NOTHING
    """,
]


# Demo *content* DDL -- skipped when HX_SEED_DEMO=false (the Banco Day-One sandbox),
# so the shop boots empty. Everything in _DDL_MIGRATIONS above is schema/infra and
# always runs; only seed rows live here.
_DEMO_DDL: list[str] = [
    # Seed the Treats catalog so giveaways decrement real stock + carry a cost.
    # Idempotent (ON CONFLICT on the unique sku). gen_random_uuid() is built-in (PG13+).
    """
    INSERT INTO products (id, sku, name, description, price, cost, stock_quantity,
        stock_alert_threshold, category, is_active, is_age_restricted, vending_compatible,
        sync_override, barcode_is_internal, product_class, needs_translation, created_at, updated_at)
    VALUES
      (gen_random_uuid(),'TREAT-LOLLIPOP','Lollipop','Treat / giveaway',0.50,0.10,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now()),
      (gen_random_uuid(),'TREAT-STICKER','Sticker','Treat / giveaway',0.30,0.05,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now()),
      (gen_random_uuid(),'TREAT-PAPERS','Rolling Papers','Treat / giveaway',0.60,0.15,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now()),
      (gen_random_uuid(),'TREAT-GUMMY','CBD Gummy','Treat / giveaway',0.45,0.12,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now()),
      (gen_random_uuid(),'TREAT-LIGHTER','Lighter','Treat / giveaway',1.50,0.40,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now()),
      (gen_random_uuid(),'TREAT-GRINDERCARD','Grinder Card','Treat / giveaway',1.80,0.50,200,20,'Treats',true,false,false,false,false,'standard',false,now(),now())
    ON CONFLICT (sku) DO NOTHING
    """,
]


async def _ensure_lightweight_columns() -> None:
    """Run the additive ALTERs above. Each is independent and forgiving -- one failure
    (e.g. table not created yet on a brand-new DB) must not block the others or boot."""
    seed_demo = os.getenv("HX_SEED_DEMO", "true").strip().lower() not in ("false", "0", "no")
    statements = _ADDITIVE_COLUMNS + _DDL_MIGRATIONS + (_DEMO_DDL if seed_demo else [])
    for stmt in statements:
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text(stmt))
        except Exception as e:  # pragma: no cover - defensive, never block startup
            logger.warning(f"additive migration skipped ({stmt[:60].strip()}...): {e}")

# ================================================================
# 🧹 CLEANUP
# ================================================================
async def close_async_engine() -> None:
    await async_engine.dispose()
    logger.info("Async engine disposed.")

# ================================================================
# 🧮 SYNC ENGINE (Celery, scripts)
# ================================================================
def create_sync_engine(url: str = settings.POSTGRES_SYNC_URI):
    logger.info("Initializing sync database engine...")
    return create_engine(url, echo=settings.DB_ECHO, pool_pre_ping=True)

@contextmanager
def get_db_session_sync() -> Iterator[Session]:
    global SyncSessionLocal
    if SyncSessionLocal is None:
        engine = create_sync_engine()
        SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
