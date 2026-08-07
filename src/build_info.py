"""Build stamp for the status bar -- the version + the git SHA actually deployed.

The container only mounts `src/` (not `.git`), and the staging/prod deploy is a
`git checkout <files> + docker restart` (no rebuild), so we can't rely on running
git inside the container or on an env var (restart keeps the old env). The robust
source is a deploy-written stamp file under the mounted `src/` tree, with sensible
fallbacks. Resolved order:

  1. HELIX_GIT_SHA env var        (if a deploy chooses to inject it)
  2. src/static/build-sha.txt     (written by the deploy into the mounted tree)
  3. live `git rev-parse`         (works in local dev where .git is present)
  4. "dev"                        (last resort -- never crashes the status bar)

Computed once and cached so it costs nothing per request.
"""
import hashlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from src import __version__

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
_STAMP = _SRC_DIR / "static" / "build-sha.txt"


@lru_cache(maxsize=1)
def get_version() -> str:
    """#3 (opt-B): a REAL auto build number — 'bNNN' from the git commit count stamped at deploy —
    so it ticks up every single deploy and can never go stale, instead of a hardcoded '3.3.0'.
    Falls back to CalVer (YY.MM.DD from the build date), then __version__, in local dev."""
    lines = _stamp_lines()
    if len(lines) >= 3 and lines[2].strip().isdigit():
        return "b" + lines[2].strip()
    d = get_build_date()
    if d:
        try:
            from datetime import datetime
            return datetime.fromisoformat(d).strftime("%y.%m.%d")
        except Exception:
            pass
    return __version__


def _stamp_lines() -> list:
    """Lines of the deploy stamp file, or []. Line 1 = sha, line 2 = ISO build date."""
    try:
        if _STAMP.exists():
            return [ln.strip() for ln in _STAMP.read_text().splitlines() if ln.strip()]
    except Exception:
        pass
    return []


@lru_cache(maxsize=1)
def get_git_sha() -> str:
    sha = (os.environ.get("HELIX_GIT_SHA") or "").strip()
    if sha:
        return sha[:7]
    lines = _stamp_lines()
    if lines:
        return lines[0][:7]
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(_REPO_ROOT), text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out or "dev"
    except Exception:
        return "dev"


@lru_cache(maxsize=1)
def get_build_date() -> str:
    """ISO date of the deployed build. From env, then stamp line 2, then the
    HEAD commit date (local dev), then "" (never crashes the status bar)."""
    d = (os.environ.get("HELIX_BUILD_DATE") or "").strip()
    if d:
        return d
    lines = _stamp_lines()
    if len(lines) >= 2:
        return lines[1]
    try:
        out = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", "HEAD"],
            cwd=str(_REPO_ROOT), text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out
    except Exception:
        return ""


@lru_cache(maxsize=1)
def get_build_date_short() -> str:
    """Numeric freshness for the bar — 'dd/mm HH:MM' (e.g. 29/06 14:52), when the change occurred,
    from the build date, or '' (#3 opt-B: date + TIME so we can track how fast the loop heals)."""
    d = get_build_date()
    if not d:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(d)
        return f"{dt.day:02d}/{dt.month:02d} {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return d[:10]


# ── Static-asset cache busting (2026-08-07) ────────────────────────────────────────────────
# Angel, after four straight rebuilds: "labels are not language sensitive -- do i need a
# container refresh or something special?" He did not. Two cache layers were both pinning a
# month-old bundle:
#
#   1. base.html linked `pos-i18n.js?v=20260701` — a HAND-TYPED version, i.e. one nobody ever
#      bumps. The browser HTTP cache had no reason to refetch.
#   2. The service worker serves /static/ CACHE-FIRST with no expiry and only evicts when
#      CACHE_NAME changes. CACHE_NAME is the git sha — which inside the container is "dev",
#      because there is no .git and no env stamp. Constant across every build, forever.
#
# sw.js already carried a comment about exactly this failure ("a deployed JS fix would verify
# green on the server and still never reach the till") — it was half-fixed, because the stamp
# it depends on does not vary in the environment most people run.
#
# So derive the version from THE FILE ITSELF. mtime+size, hashed. It cannot go stale, needs no
# build discipline, no env var and no script anybody has to remember to run, and it behaves
# identically in dev and prod. A file that did not change keeps its URL and stays cached.
_ASSET_V_CACHE: dict = {}


def asset_version(rel_path: str) -> str:
    """Short content-ish version for a file under src/static — for `?v=` cache busting.

    Keyed on (mtime_ns, size), which changes on every real edit and on every image rebuild.
    Cached per process: the file cannot change under a running container, and this is called
    on every page render.
    """
    if rel_path in _ASSET_V_CACHE:
        return _ASSET_V_CACHE[rel_path]
    v = "dev"
    try:
        p = _REPO_ROOT / "src" / "static" / rel_path.lstrip("/")
        st = p.stat()
        v = hashlib.sha1(f"{st.st_mtime_ns}:{st.st_size}".encode()).hexdigest()[:10]
    except Exception:
        pass                       # a missing asset must never 500 a page render
    _ASSET_V_CACHE[rel_path] = v
    return v


@lru_cache(maxsize=1)
def static_bundle_version() -> str:
    """One version for the whole /static/pos + /static tree — the service worker's cache key.

    The SW caches many files under one CACHE_NAME, so the key has to move when ANY of them
    changes, not just when git does. Falls back to the sha alone if the tree cannot be walked.
    """
    try:
        h = hashlib.sha1()
        root = _REPO_ROOT / "src" / "static"
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix in (".js", ".css", ".json", ".webmanifest"):
                st = p.stat()
                h.update(f"{p.relative_to(root)}:{st.st_mtime_ns}:{st.st_size}".encode())
        return f"{get_git_sha()}-{h.hexdigest()[:10]}"
    except Exception:
        return get_git_sha() or "dev"
