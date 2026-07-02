"""GreatReads → Libby engine proxy (#142).

Thin, normalized proxy over the headless "Libby engine" sidecar (the `libby-web`
Flask app on :5007). Keeps all Libby secrets (the chip identity, per-library
website credentials) server-side — the browser only ever talks to GreatReads,
never to the engine directly.

v1 (MVP-1, token self-service slice) exposes:
  - GET  /api/libby/status  → chip/token health (linked?, card count, token exp +
                              seconds remaining, can_fulfill) plus engine
                              reachability and a normalized traffic-light `state`.
  - POST /api/libby/relink  → re-link the chip from a phone-generated code
                              (engine runs get_chip() + clone_by_code() + sync()).

Later #142 milestones (search, borrow/download, holds, cards/credentials) add
more endpoints here over the same engine.
"""

import logging
import os

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# The engine stays bound to the host; the GreatReads container reaches it via the
# host gateway (same mechanism as Calibre/ABS — see extra_hosts in the ereader
# compose). Overridable so a future compose-network alias (http://libby-web:5007)
# can be swapped in without a code change.
LIBBY_ENGINE_URL = os.environ.get("LIBBY_ENGINE_URL", "http://host.docker.internal:5007").rstrip("/")

_DAY = 86400
# Match §5: warn (amber badge) when the token expires within ~2 days; critical
# (red) within ~1 day; dead once expired.
_WARN_SECONDS = 2 * _DAY
_CRITICAL_SECONDS = _DAY


def _health_state(engine_reachable: bool, status: dict) -> str:
    """Normalize the engine status into a traffic-light state the UI can render
    directly: unreachable | dead | critical | warn | ok | unknown."""
    if not engine_reachable:
        return "unreachable"
    seconds_left = status.get("seconds_left")
    if seconds_left is None:
        return "unknown"
    if seconds_left <= 0:
        return "dead"
    if seconds_left < _CRITICAL_SECONDS:
        return "critical"
    if seconds_left < _WARN_SECONDS or not status.get("linked"):
        return "warn"
    return "ok"


@router.get("/status")
async def libby_status(current_user: User = Depends(get_current_user)):
    """Return normalized Libby chip/token health for the Books-page widget.

    Always returns 200: when the engine is unreachable we report
    `engine_reachable:false` / `state:"unreachable"` so the UI degrades to a clear
    "engine down" message instead of erroring.
    """
    engine_reachable = True
    raw: dict = {}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{LIBBY_ENGINE_URL}/api/status")
            resp.raise_for_status()
            raw = resp.json()
    except Exception as exc:
        logger.warning("libby_status: engine unreachable at %s: %s", LIBBY_ENGINE_URL, exc)
        engine_reachable = False

    state = _health_state(engine_reachable, raw)
    return {
        "engine_reachable": engine_reachable,
        "state": state,
        # `stale` == the Libby button should show a warning badge (§5).
        "stale": state in {"unreachable", "dead", "critical", "warn"},
        "linked": bool(raw.get("linked")),
        "cards": raw.get("cards"),
        "exp": raw.get("exp"),
        "seconds_left": raw.get("seconds_left"),
        "can_fulfill": bool(raw.get("can_fulfill")),
        "prbn": raw.get("prbn"),
        "accounts": raw.get("accounts"),
        "sync_error": raw.get("sync_error"),
    }


class RelinkRequest(BaseModel):
    code: str


@router.post("/relink")
async def libby_relink(
    payload: RelinkRequest = Body(...),
    current_user: User = Depends(get_current_user),
):
    """Re-link the Libby chip from an 8-char phone code (Libby → Settings → Copy
    to Another Device). Proxies to the engine's POST /api/relink."""
    code = (payload.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Missing code — paste the 8-character code from Libby → Settings → Copy to Another Device.")

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{LIBBY_ENGINE_URL}/api/relink", json={"code": code})
    except Exception as exc:
        logger.warning("libby_relink: engine unreachable at %s: %s", LIBBY_ENGINE_URL, exc)
        raise HTTPException(status_code=502, detail="Libby engine is unreachable — is the libby-web service running?")

    try:
        data = resp.json()
    except Exception:
        data = {}

    if resp.status_code >= 400 or not data.get("ok"):
        detail = data.get("error") or "Re-link failed. Double-check the code (it expires within a few minutes) and try again."
        raise HTTPException(status_code=resp.status_code if resp.status_code >= 400 else 502, detail=detail)

    return {
        "ok": True,
        "cards": data.get("cards"),
        "loans": data.get("loans"),
        "holds": data.get("holds"),
        "exp": data.get("exp"),
        "seconds_left": data.get("seconds_left"),
        "logged_in": data.get("logged_in"),
    }
