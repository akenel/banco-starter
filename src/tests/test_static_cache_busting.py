"""A shipped fix must actually reach the till.

2026-08-07. Angel, after I had rebuilt and redeployed four times: *"labels are not language
sensitive -- do i need a container refresh or something special?"* He did not. The code was
correct and deployed; his browser was still running a bundle from the first of July.

TWO CACHE LAYERS, BOTH PINNED:

  1. `base.html` linked `pos-i18n.js?v=20260701` — a hand-typed version string, which means one
     nobody ever bumps. The browser had no reason to refetch.
  2. The service worker serves /static/ CACHE-FIRST with no expiry and only evicts when
     CACHE_NAME changes. CACHE_NAME was the git sha — which is `"dev"` inside the container,
     because there is no .git and no env stamp. Constant across every build, forever.

The most damning part: `sw.js` already carried a comment about exactly this — *"a deployed JS
fix would verify green on the server and still never reach the till"* — written on 2026-07-31.
It was half-fixed, because the stamp it relied on does not vary in the environment most people
actually run. A fix that depends on a build step somebody has to remember is not a fix.

Both versions now come from the FILES: mtime+size, hashed. Nothing to remember, nothing to bump,
identical in dev and prod. These tests exist so the hand-typed version cannot come back.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "pos"
STATIC = ROOT / "static"


def _template_files():
    return sorted(TEMPLATES.glob("*.html"))


def test_no_static_asset_carries_a_hand_typed_version():
    """The exact bug: `?v=20260701`. A literal date or a `v185` is a version somebody has to
    remember to change, and the evidence says nobody does — this one sat unchanged for five
    weeks while the file behind it moved repeatedly."""
    offenders = []
    for f in _template_files():
        for m in re.finditer(r'(?:src|href)="[^"]*\?v=([^"&]+)"', f.read_text(encoding="utf-8")):
            v = m.group(1)
            if "asset_v" in v or "{{" in v:
                continue                      # computed — fine
            offenders.append(f"{f.name}: ?v={v}")
    assert not offenders, (
        "hand-typed asset versions found — use ?v={{ asset_v('pos/thing.js') }} so the URL "
        f"changes when the file does:\n  " + "\n  ".join(offenders))


def test_the_i18n_bundle_is_versioned_at_all():
    """It is the file that broke, and the one most likely to change without anyone thinking
    about caching — every new string lands in it."""
    s = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    m = re.search(r'pos-i18n\.js\?v=\{\{\s*asset_v\(', s)
    assert m, "pos-i18n.js is not cache-busted from the file — a new string will not reach a device"


def test_asset_version_changes_when_the_file_changes(tmp_path, monkeypatch):
    """The whole promise, tested rather than assumed."""
    import src.build_info as bi

    target = STATIC / "pos" / "pos-i18n.js"
    v1 = bi.asset_version("pos/pos-i18n.js")
    assert v1 and v1 != "dev", "no version derived for a file that exists"

    # touch it (restore the original mtime afterwards — this is a real repo file)
    st = target.stat()
    try:
        import os
        os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
        bi._ASSET_V_CACHE.clear()
        v2 = bi.asset_version("pos/pos-i18n.js")
    finally:
        import os
        os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns))
        bi._ASSET_V_CACHE.clear()
    assert v2 != v1, "the version did not move when the file did — the cache would never clear"


def test_a_missing_asset_never_crashes_a_page_render():
    """This runs on every page render. It must degrade, never 500 the till."""
    import src.build_info as bi
    assert bi.asset_version("pos/does-not-exist.js") == "dev"


def test_the_service_worker_key_tracks_the_static_tree_not_just_git():
    """CACHE_NAME is the ONLY thing that evicts stale /static/ from a device that has been here
    before. Tied to the git sha alone it was the literal string 'dev' in every container."""
    import src.build_info as bi
    v = bi.static_bundle_version()
    assert v and v != "dev", f"bundle version is not usable: {v!r}"
    assert "-" in v, f"expected '<sha>-<tree hash>', got {v!r}"
    assert len(v.split("-")[-1]) >= 8, "the tree hash is too short to be meaningful"


def test_the_sw_route_stamps_the_bundle_version():
    """Reads the route, not the file on disk: sw.js ships with a placeholder and is only useful
    once the route substitutes it."""
    src = (ROOT / "routes" / "pos_router.py").read_text(encoding="utf-8")
    assert "static_bundle_version()" in src, \
        "the service-worker route no longer stamps the static-tree version"
    assert '__BANCO_BUILD__' in (STATIC / "pos" / "sw.js").read_text(encoding="utf-8"), \
        "sw.js lost its placeholder — CACHE_NAME would be a constant again"
