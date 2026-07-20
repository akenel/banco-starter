"""
Backup cockpit — read-only status of the shop's "own your data" B2 backups.

This powers the Settings → Backup tab. Two jobs, both SAFE to expose to an admin:

  1. config()   — is the backup wired? Reports which B2 vars are present and whether the
                  GPG passphrase is set. NEVER returns a secret: the key id is masked to its
                  last 4 chars, the app key + passphrase are reported as booleans only.
  2. check()    — a LIVE probe of the shop's own bucket via Backblaze's native REST API
                  (plain HTTPS — no b2 CLI needed in the container). Proves the credentials
                  work and lists the recent backups so the owner can SEE their data is safe
                  in the cloud and how fresh the newest copy is (the "are backups actually
                  running?" alarm).

SECURITY: secrets live in .env (entered via scripts/init-banco.py getpass) and reach this
process as env vars. They are used to talk to B2 and are NEVER written to the DB, logged, or
returned to the browser. The backup ITSELF encrypts the DB, so storing the backup's own key
inside the DB would be a circular leak — see docs/SPEC / the Settings backup tab note.

Creating a backup and restoring one stay as host-side scripts (backup-to-b2.sh /
restore-from-b2.sh) — they need pg_dump + gpg + the docker socket, which the app container
deliberately does not have. The cockpit surfaces the exact commands instead of pretending to
run host operations it can't run securely.
"""
from __future__ import annotations

import os
import base64
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_B2_AUTH_URL = "https://api.backblazeb2.com/b2api/v3/b2_authorize_account"
_BACKUP_PREFIX = "banco/"


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _mask_tail(s: str, keep: int = 4) -> str:
    """Show only the last `keep` chars of a secret-ish id (never the whole thing)."""
    if not s:
        return ""
    if len(s) <= keep:
        return "•" * len(s)
    return "•" * (len(s) - keep) + s[-keep:]


def config() -> dict:
    """Instant, no-network view of whether backups are wired. No secrets returned."""
    key_id = _env("B2_KEY_ID")
    app_key = _env("B2_APP_KEY")
    bucket = _env("B2_BUCKET")
    gpg = _env("BACKUP_GPG_PASSPHRASE")
    configured = bool(key_id and app_key and bucket and gpg)
    missing = [
        name for name, val in (
            ("B2_KEY_ID", key_id), ("B2_APP_KEY", app_key),
            ("B2_BUCKET", bucket), ("BACKUP_GPG_PASSPHRASE", gpg),
        ) if not val
    ]
    return {
        "configured": configured,
        "bucket": bucket,                    # a bucket name is not a secret
        "key_id_masked": _mask_tail(key_id),  # last 4 only
        "app_key_set": bool(app_key),        # bool only — never the value
        "gpg_set": bool(gpg),                # bool only — never the value
        "missing": missing,
    }


async def check() -> dict:
    """
    LIVE probe of the shop's bucket via the B2 native REST API. Returns backup freshness +
    the recent file list. Never raises — errors come back as {ok: False, error: "..."}.
    """
    cfg = config()
    if not (cfg["bucket"] and _env("B2_KEY_ID") and _env("B2_APP_KEY")):
        return {"ok": False, "error": "B2 is not configured in .env (run scripts/init-banco.py)."}

    key_id = _env("B2_KEY_ID")
    app_key = _env("B2_APP_KEY")
    bucket = cfg["bucket"]

    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            # 1) authorize — HTTP Basic (keyId:appKey). Proves the credentials are valid.
            basic = base64.b64encode(f"{key_id}:{app_key}".encode()).decode()
            r = await c.get(_B2_AUTH_URL, headers={"Authorization": f"Basic {basic}"})
            if r.status_code != 200:
                return {"ok": False, "error": "B2 rejected the key (check B2_KEY_ID / B2_APP_KEY)."}
            auth = r.json()
            storage = (auth.get("apiInfo") or {}).get("storageApi") or {}
            api_url = storage.get("apiUrl")
            token = auth.get("authorizationToken")
            account_id = auth.get("accountId")
            bucket_id = storage.get("bucketId")       # present when the key is bucket-restricted
            if not api_url or not token:
                return {"ok": False, "error": "B2 authorized but returned no API URL (unexpected)."}

            hdr = {"Authorization": token}

            # 2) resolve bucketId if the key is account-wide (not restricted to one bucket)
            if not bucket_id:
                rb = await c.post(
                    f"{api_url}/b2api/v3/b2_list_buckets",
                    headers=hdr, json={"accountId": account_id, "bucketName": bucket},
                )
                if rb.status_code == 200:
                    buckets = rb.json().get("buckets") or []
                    if buckets:
                        bucket_id = buckets[0].get("bucketId")
                if not bucket_id:
                    return {"ok": False,
                            "error": f"Connected, but bucket '{bucket}' was not found for this key."}

            # 3) list the backup files (newest first is not guaranteed; we sort)
            rl = await c.post(
                f"{api_url}/b2api/v3/b2_list_file_names",
                headers=hdr,
                json={"bucketId": bucket_id, "prefix": _BACKUP_PREFIX, "maxFileCount": 100},
            )
            if rl.status_code != 200:
                # authorize worked but listing didn't — usually a read-capability gap
                return {"ok": False,
                        "error": "Connected, but this key can't list files (needs listFiles capability)."}
            files = rl.json().get("files") or []
    except httpx.HTTPError as e:
        logger.warning("B2 backup check network error: %s", type(e).__name__)
        return {"ok": False, "error": "Could not reach Backblaze B2 (network?). Try again."}
    except Exception as e:  # never leak internals to the UI
        logger.exception("B2 backup check failed")
        return {"ok": False, "error": f"Unexpected error talking to B2 ({type(e).__name__})."}

    now_ms = datetime.now(timezone.utc).timestamp() * 1000.0
    rows = []
    for f in files:
        name = f.get("fileName") or ""
        if name.endswith("/"):   # skip folder placeholder entries
            continue
        ts = float(f.get("uploadTimestamp") or 0)
        age_h = round((now_ms - ts) / 3_600_000.0, 1) if ts else None
        rows.append({
            "name": name.split("/")[-1],
            "size_mb": round(float(f.get("contentLength") or 0) / 1_048_576.0, 2),
            "age_hours": age_h,
            "uploaded": datetime.fromtimestamp(ts / 1000.0, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "",
        })
    rows.sort(key=lambda x: x["uploaded"], reverse=True)

    newest_age = rows[0]["age_hours"] if rows else None
    # Freshness verdict for the alarm light: green <36h, amber <8d, else stale/none.
    if not rows:
        freshness = "none"
    elif newest_age is not None and newest_age <= 36:
        freshness = "fresh"
    elif newest_age is not None and newest_age <= 24 * 8:
        freshness = "aging"
    else:
        freshness = "stale"

    return {
        "ok": True,
        "bucket": bucket,
        "count": len(rows),
        "newest_age_hours": newest_age,
        "freshness": freshness,
        "backups": rows[:12],   # newest dozen is plenty for the cockpit
    }
