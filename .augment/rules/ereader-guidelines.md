---
type: always
description: GreatReads agent guidelines — pointer to the canonical docs
---

# GreatReads — agent guidelines

This file used to carry the full project reference, but it drifted badly out of
date (it described the pre-merge `:8091` Flask world). **It is no longer the
source of truth.** Don't add long-form reference here — it will just rot again.

## Canonical sources (read these instead)

- **`CLAUDE.md`** (repo root) — working rules, current runtime layout, ports,
  the container rebuild/re-stage flow, and rollback notes. This is the canonical
  onboarding doc.
- **GitHub Issues** — plans, scope, status, and the backlog. Per `CLAUDE.md`,
  issues are the source of truth for work-to-be-done; do not create standalone
  planning `.md` files.
- **The code itself** — for API surface, schemas, and integration contracts,
  read the live code rather than trusting a doc:
  - Unified FastAPI app (`:8092`, container `greatreads_ereader`):
    `greatreads/src/greatreads/` — GreatReads routes/models plus the absorbed
    Ereader API in `ereader_api.py`.
  - Reader / player / library frontends: `web/reader.html`, `web/player.js`,
    `web/index.html` (served bare-metal on `:8090` by `web/serve.py`).
  - Android WebView wrapper + `window.Android` JS bridge:
    `simple-app/app/src/main/java/com/ereader/simple/MainActivity.java`.
- **`docs/RECOVERY.md`** — recovery checklist when the app is broken.

## Quick orientation

- `:8092` — unified app (library/TBR/journal/stats + the canonical SQLite DB +
  the absorbed Ereader `/api/...` routes). Container; code is baked in, so code
  changes need a rebuild (see `CLAUDE.md`).
- `:8090` — `web/serve.py`, static reader files + `/greatreads/` reverse proxy
  (bare-metal; slated to fold into `:8092` — GitHub issue #8).
- `:8091` — **retired** (#22). Nothing listens there; don't restart it.

If something here is wrong, fix `CLAUDE.md` (not this file) and keep this a
short pointer.
