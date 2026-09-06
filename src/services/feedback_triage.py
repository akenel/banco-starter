"""Hypercare Triage Brain (PoC-1) — turn a messy user feedback ticket into a clean one.

A user fires the 💬 button with a half-formed title, a vague description and a screenshot.
This reads all of it (text + metadata + a VISION scan of the screenshot) and rewrites it into
ONE clean ticket: a sharp title, a clear description, a type + severity guess, a confidence, and
— if it can't tell what they mean — `decipherable=false` + a list of questions to send back.

The original is NEVER touched; the caller stores this as a BacklogActivity (dual-version audit).

Uses the existing BYO-brain (`src/llm.run_llm`, Ollama local/Turbo) + vision engine
(`src/services/vision`). Degrades gracefully: if a brain is unavailable, returns a clearly-marked
fallback so the cron never crashes and the human just reads the raw ticket.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from src.llm import run_llm
from src.llm.targets import turbo_or_local
from src.services.vision import VisionDomain, analyze_image

logger = logging.getLogger(__name__)

# Triage rewrites text + reads one screenshot — a capable model on Turbo if configured,
# else whatever local Ollama has. The recipe owns its default model (BYO-brain rule).
_TRIAGE_MODEL_TURBO = "gpt-oss:120b"
_TRIAGE_MODEL_LOCAL = "llama3.2:3b"

# --- VISION lens: describe a POS screenshot for a bug report (not a product photo) ----------
def _coerce_shot(d: dict) -> dict:
    g = lambda k: (str(d.get(k) or "").strip())[:600]
    return {"screen": g("screen"), "visible": g("visible"), "anomalies": g("anomalies")}

TRIAGE_VISION = VisionDomain(
    name="feedback_triage",
    prompt=(
        "You are looking at a screenshot from the 'Banco' point-of-sale web app, attached to a "
        "user bug report. "
        # BANCO'S OWN FURNITURE. On 2026-09-06, off its very first real ticket, the
        # model asked whether "the red circular icon with three dots at the bottom
        # right" was a UI artifact. That is the 💬 button — the one that FILED the
        # ticket. It is on every screen, so without this every ticket in a 34-screen
        # walk would have burned a clarifying question on our own chrome.
        "These are PERMANENT parts of every Banco screen and are never faults: a round "
        "red 💬 speech-bubble button floating over the page (the feedback button — it is "
        "draggable, so it can sit anywhere, often over content); a dark bar along the top "
        "showing the time, a build number like b707, the user and a language selector; and "
        "a dark navigation bar along the bottom with Scan, Cart, Catalog, Customers and My "
        "Day. Never report any of these as an anomaly. "
        # AN EMPTY STATE IS USUALLY CORRECT. The old prompt listed "an empty state" as
        # an anomaly outright, so the model flagged an un-triaged panel that was
        # empty precisely because it had not been triaged yet. "No transactions
        # found" on a quiet day is the screen working.
        "An empty panel or an empty list is usually CORRECT — a till with no sales shows "
        "no sales. Only call emptiness an anomaly if something clearly should have been "
        "there and is not. "
        # THE THING THE STATIC CHECKS CANNOT SEE. scripts/prove-one-box-one-language.py
        # finds every untranslated string exactly and for free; what it cannot do is
        # judge a translation that EXISTS. That is what a picture is for.
        # ZOOM MAKES A LIAR OF THE PICTURE. On 2026-09-06 Angel walked ten screens
        # with his browser zoomed out (Pixel ratio 0.5-0.8) and triage reported
        # "CHF ?'28?'.95", "13R", "5R" and a franc figure "missing its decimal
        # separator" — every one an artifact of a 3840px page squeezed into 1600
        # and JPEG'd, not a defect. A model that cannot tell mush from a bug will
        # file bugs about mush, and those are expensive: they look exactly like the
        # real ones.
        "THE SCREENSHOT MAY BE LOSSY. The context includes a Pixel ratio. If it is "
        "below 1 the browser was zoomed OUT and the image has been downscaled twice, "
        "so fine detail is unreliable: do NOT report garbled characters, stray "
        "letters, missing decimal points or odd spacing inside numbers as defects — "
        "say instead that the capture is too coarse to judge and ask for a "
        "screenshot at 100% zoom. Layout, language and wording are still fair game. "
        "LANGUAGE MATTERS ON THIS SCREEN. The whole interface should be in ONE language. "
        "If some text is in a different language from the rest, say so and quote the exact "
        "words. Also flag text that is cut off, overlapping, or spilling out of its button "
        "or box. "
        "Reply with ONLY a JSON object: "
        '{"screen": which screen/area this is (e.g. Catalog, Receipt, Checkout, Reports), '
        '"visible": a one-line summary of what is on screen, '
        '"anomalies": anything that looks WRONG, broken, misaligned, an error message, mixed '
        "languages, or text that is cut off — or empty string if nothing looks wrong}."
    ),
    coerce=_coerce_shot,
)

# --- Structured output schema for the clean ticket (Ollama enforces this) -------------------
_CLEAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "type": {"type": "string", "enum": ["bug", "idea", "question", "cosmetic", "other"]},
        "severity": {"type": "string", "enum": ["blocking", "annoying", "cosmetic"]},
        "area": {"type": "string"},
        "confidence": {"type": "number"},
        "decipherable": {"type": "boolean"},
        "questions": {"type": "array", "items": {"type": "string"}},
        "duplicate_of": {"type": "integer"},
    },
    "required": ["title", "description", "type", "severity", "confidence", "decipherable",
                 "duplicate_of"],
}

_SYSTEM = (
    "You are the QA triage assistant for the Banco point-of-sale app. Users (cashiers, the shop "
    "owner) fire quick feedback with a rough title, a vague description, and usually a screenshot. "
    "Rewrite their report into ONE clean, professional ticket an engineer can act on. Rules: keep "
    "their MEANING, never invent features they didn't ask for; write a crisp imperative title and "
    "a clear 2-4 sentence description; classify type + severity; set `area` to the screen if known; "
    "give a 0..1 confidence. If you genuinely can't tell what they want, set decipherable=false and "
    "put 1-3 specific questions in `questions`. "
    # ─────────────────────────────────────────────────────────────────────────────
    # THE REPORTER CAN BE WRONG, AND UNTIL 2026-09-06 THIS PROMPT DID NOT ALLOW IT.
    #
    # BL-019: Angel opened /pos/scan — a screen with zero untranslated strings,
    # every key resolving in Italian — and filed "IT A8 · scan / Checking this
    # screen for language problems." Triage returned:
    #
    #     "Fix Italian translation errors on Scan screen … displays incorrect or
    #      inconsistent Italian wording."   bug · conf 0.92
    #
    # It quoted NOTHING, because there was nothing to quote. It took the
    # reporter's framing and handed it back as a confirmed defect, at 92%. The
    # vision pass had returned an empty `anomalies` and the model overrode it.
    #
    # That is the failure mode that would ruin this in a shop: a cashier files
    # "this looks weird", triage confirms a bug that does not exist, and the
    # owner's backlog fills with phantoms nobody can reproduce. Compare BL-018 on
    # the same day, where three exact strings the reporter never typed were named
    # off the screenshot at 96% — THAT is what a real finding looks like. The
    # difference between them is quoted evidence, so that is what the rules below
    # are built on.
    # ─────────────────────────────────────────────────────────────────────────────
    "NOT EVERY REPORT IS A DEFECT, and saying so is a correct outcome — never a "
    "failure. The reporter is telling you what they noticed, which may be right, "
    "may be a misunderstanding, or may be them checking a screen that is fine. "
    "EVIDENCE RULE: a finding must name what is wrong — quote the exact text, or "
    "describe the specific element. If you cannot quote or point at anything, you "
    "do not have a finding, no matter how confident the reporter sounds. "
    "If the description is vague AND the screenshot shows no anomaly, do NOT "
    "assert a defect: say plainly what was checked and that nothing was found, set "
    "type to 'Question', set confidence to 0.3 or below, and ask the reporter to "
    "point at the exact words or the exact spot. "
    "CONFIDENCE MEASURES EVIDENCE, NOT AGREEMENT. High confidence means you can "
    "quote the problem. Echoing the reporter's own sentence back with no specifics "
    "is a 0.2, not a 0.9. "
    "DEDUP: you may be given a list of EXISTING OPEN tickets. If this report is essentially the "
    "SAME underlying problem as one of them, set `duplicate_of` to that ticket's number; otherwise "
    "set `duplicate_of` to 0. Only call it a duplicate if it's clearly the same issue, not merely "
    "the same screen. Output JSON only."
)


def _fmt_meta(metadata: Any) -> str:
    if not metadata:
        return ""
    if isinstance(metadata, str):
        return metadata[:800]
    try:
        keep = {k: metadata[k] for k in ("path", "env", "build", "user", "platform", "viewport",
                                         "sales_today", "health", "online") if k in metadata}
        return json.dumps(keep)[:800]
    except Exception:
        return str(metadata)[:800]


async def triage_feedback(
    *,
    title: str,
    description: str = "",
    metadata: Any = None,
    screenshot: Optional[bytes] = None,
    screenshot_mime: str = "image/png",
    existing: Optional[list] = None,
) -> dict:
    """Messy ticket in → clean ticket out. Returns:
        {clean: {...schema...}, vision: {screen,visible,anomalies}|None,
         model, tokens, ai: bool, note: str|None}
    Never raises for brain/transport issues — returns ai=False + a note instead."""
    # 1) VISION scan of the screenshot (best-effort).
    vision = None
    if screenshot:
        try:
            # Vision provider is configurable; default Gemini (the shop's Snap-&-fill provider).
            # Lights up when BH_GOOGLE_API_KEY is set; degrades gracefully otherwise. (Turbo
            # hosts the text model but not a vision one, so ollama isn't a working default here.)
            res = await analyze_image(screenshot, screenshot_mime, domain=TRIAGE_VISION,
                                      provider=os.getenv("BANCO_VISION_PROVIDER", "gemini"))
            vision = res.get("data")
            if res.get("note"):
                logger.info("triage vision note: %s", res["note"])
        except Exception as e:  # noqa: BLE001
            logger.warning("triage vision failed: %s", e)

    # 2) Build the rewrite prompt from everything we know.
    parts = [f"RAW TITLE: {title or '(none)'}", f"RAW DESCRIPTION: {description or '(none)'}"]
    meta = _fmt_meta(metadata)
    if meta:
        parts.append(f"SYSTEM METADATA: {meta}")
    if vision:
        parts.append("SCREENSHOT (vision): " + json.dumps(vision))
    if existing:
        listing = "; ".join(f"[#{e['n']}] {e['title']}" for e in existing[:30])
        parts.append("EXISTING OPEN TICKETS (for dedup): " + listing)
    user_prompt = "\n".join(parts) + "\n\nReturn the clean ticket as JSON."

    # 3) Rewrite via the BYO-brain with an enforced schema.
    try:
        target = turbo_or_local(_TRIAGE_MODEL_TURBO, _TRIAGE_MODEL_LOCAL)
        result = await run_llm(user_prompt, target=target, system=_SYSTEM, schema=_CLEAN_SCHEMA)
        clean = json.loads(result.text)
        return {"clean": clean, "vision": vision, "model": result.model,
                "tokens": result.tokens, "ai": True, "note": None}
    except Exception as e:  # noqa: BLE001 — brain down / bad JSON → graceful fallback
        logger.warning("triage rewrite failed: %s", e)
        return {
            "clean": {
                "title": (title or "Untitled feedback")[:120],
                "description": description or "(no description)",
                "type": "other", "severity": "annoying",
                "area": (vision or {}).get("screen", ""),
                "confidence": 0.0, "decipherable": False,
                "questions": ["AI triage was unavailable — please review the raw ticket by hand."],
                "duplicate_of": 0,
            },
            "vision": vision, "model": "", "tokens": 0, "ai": False,
            "note": f"AI unavailable ({type(e).__name__})",
        }


# --- Resolution summary: the whole ticket as a 3-4 sentence story a busy owner can skim ------
_RESOLUTION_SYSTEM = (
    "You write the RESOLUTION for a small shop's feedback ticket — so a busy owner can read 3-4 "
    "short sentences and understand the whole story without digging into the details. Use plain, "
    "concrete, friendly words. NO jargon, NO bullet points — ONE short paragraph. Cover, in order: "
    "what the person reported, what we understood/decided, what was actually done (mention the code "
    "change / commit short-hash if there was one), and the outcome (fixed and confirmed, or no "
    "change was needed, or it was withdrawn). Write it like a little story someone can read at a "
    "glance. 3-4 sentences, nothing more. Stick to the facts in the history — never invent a step "
    "(like a confirmation or a close) that isn't there."
)


async def summarize_resolution(story_lines: list) -> dict:
    """Turn an ordered list of plain story beats → one Lego-language resolution paragraph.
    Always returns SOMETHING readable: falls back to joining the beats if the brain is down."""
    beats = [s for s in (story_lines or []) if s]
    story = "\n".join(f"- {s}" for s in beats)
    try:
        target = turbo_or_local(_TRIAGE_MODEL_TURBO, _TRIAGE_MODEL_LOCAL)
        result = await run_llm("Ticket history (oldest first):\n" + story +
                               "\n\nWrite the resolution paragraph.",
                               target=target, system=_RESOLUTION_SYSTEM)
        text = (result.text or "").strip()
        if text:
            return {"text": text, "model": result.model, "ai": True}
    except Exception as e:  # noqa: BLE001 — brain down → a plain, still-useful fallback
        logger.warning("resolution summary failed: %s", e)
    return {"text": " ".join(beats) or "This report has been closed.", "model": "", "ai": False}
