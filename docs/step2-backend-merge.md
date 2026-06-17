# Step 2 — Combine the Ereader backend into the GreatReads process

**Status:** scoped, not started. Execute in a fresh session.
**Prereqs done:** FastAPI port (#18), dead-code cleanup (#19), API namespace
collision rename (#20 — Ereader catalog/media now live at `/api/catalog*` +
`/api/ebooks*`, collision-free with GreatReads' `/api/library*` + `/api/books*`).

This is step 2 of the backend merge (b). Steps 3 (collapse the self-hop) and 4
(retire the JSON dual-write) are **explicitly deferred** — see the end.

---

## 1. Goal

Today the Ereader app is **3 runtime surfaces**:

| Port | What | How |
|---|---|---|
| `:8090` | `web/serve.py` — static reader files + `/greatreads/` reverse proxy | bare-metal |
| `:8091` | `backend/app.py` — FastAPI: Calibre/ABS catalog, covers, downloads, HLS, highlights, progress, summaries | bare-metal, `uvicorn --reload` |
| `:8092` | `greatreads_ereader` container — FastAPI: library/TBR/journal/stats + the SQLite DB | Docker |

Step 2 folds **`:8091` into the `:8092` container** so the two FastAPI apps run
as **one process**. After this step the runtime is `:8090` (static+proxy) +
`:8092` (the unified app). `:8091` is retired. `:8090` is folded in later (#8).

Direction is locked (see memory): consolidate **onto GreatReads**, so the
GreatReads app absorbs the Ereader routes (not the reverse).

---

## 2. How the reader reaches the API today (important context)

- `web/reader.html`, `web/player.js`, `web/index.html` define
  `API_URL = 'http://100.69.184.113:8091/api'` and append paths
  (`${API_URL}/catalog`, `${API_URL}/ebooks/{id}/download`, …).
- Cover/thumbnail URLs are built **server-side** in app.py as
  `http://{PUBLIC_HOST}/api/ebooks/{id}/cover` (`PUBLIC_HOST` default
  `100.69.184.113:8091`) and embedded in the `/api/catalog` response.
- The reader page is served from `:8090` but already calls the API on `:8091`
  — i.e. **the reader is already cross-origin today**, relying on app.py's
  `CORSMiddleware(allow_origins=["*"])`. The merged app has the same CORS, so
  pointing the reader at `:8092` introduces **no new CORS situation**.

So the cutover switch is purely: change `:8091` → `:8092` in two places
(`API_URL` in the frontend, `PUBLIC_HOST` for server-built URLs).

---

## 3. Target architecture

```
phone / browser
   │
   ├── :8090  web/serve.py
   │      ├── /                → 302 /greatreads/tbr
   │      ├── /reader.html …   → static files (the reader UI)
   │      └── /greatreads/*    → proxy → :8092  (GreatReads pages, same-origin, cookies)
   │
   └── :8092  greatreads_ereader  container  ◀── unified FastAPI app
          ├── GreatReads routers   /api/books, /api/readings, /api/library, /api/stats …
          ├── GreatReads pages     /tbr /library /journal /stats /settings /highlights
          ├── Ereader routers      /api/catalog, /api/ebooks, /api/audiobooks,
          │                        /api/highlights, /api/progress, /api/summaries,
          │                        /api/series, /api/saga, /api/booklinks, /api/fetch,
          │                        /api/greatreads/*, /api/health, /api/version, /api/build-stamp
          └── talks out to:
               ├── Calibre  HTTP  http://host.docker.internal:8083   (covers, downloads, search)
               ├── ABS      HTTP  http://host.docker.internal:13378  (audiobook covers, HLS)
               └── greatreads.db   /app/data/greatreads.db           (already mounted)
```

The reader's `API_URL` becomes `http://100.69.184.113:8092/api` (or, later in
#8, a same-origin path via the `:8090` proxy — deferred to keep step 2 small).

---

## 4. Integration mechanism

Convert `backend/app.py` from a standalone `FastAPI()` app into an **`APIRouter`
module inside the GreatReads package**, then `include_router` it in
`greatreads/src/greatreads/main.py`. This keeps every route at its exact
current path and reuses GreatReads' existing CORS + middleware + uvicorn.

`packages = ["greatreads"]` in pyproject means the module **must live under
`src/greatreads/`** to be importable in the container.

---

## 5. Exact code changes

### 5A. New module `greatreads/src/greatreads/ereader_api.py` (from `backend/app.py`)

Copy `backend/app.py` to `greatreads/src/greatreads/ereader_api.py`, then:

1. **Imports:** remove `from fastapi import FastAPI, ...` app bits; keep
   `Request, Response, HTTPException`; add `from fastapi import APIRouter`;
   keep `from fastapi.responses import JSONResponse, StreamingResponse`.
   Remove `from fastapi.middleware.cors import CORSMiddleware` and
   `import uvicorn` (parent app owns CORS + the server).
2. **App → router:** replace
   ```python
   app = FastAPI()
   app.add_middleware(CORSMiddleware, ...)
   ```
   with
   ```python
   router = APIRouter()
   ```
3. **Decorators:** `@app.get(` → `@router.get(`, `@app.post(` → `@router.post(`,
   etc. (33 routes). `sed -i 's/@app\./@router./g'` then spot-check.
4. **Drop the run block:** delete `if __name__ == '__main__':` … `uvicorn.run(...)`
   at the bottom (keep the Calibre-connection startup prints only if you move
   them into a logged startup hook — otherwise delete them too).
5. **Make two hardcoded paths env-overridable** (they currently resolve
   relative to `__file__`, which moves inside the container):
   ```python
   # was: SUMMARIES_DIR = os.path.join(os.path.dirname(__file__), 'summaries')
   SUMMARIES_DIR = os.environ.get('EREADER_SUMMARIES_DIR',
                                  os.path.join(os.path.dirname(__file__), 'summaries'))
   # was: VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt')
   VERSION_FILE = os.environ.get('EREADER_VERSION_FILE',
                                 os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt'))
   ```
   (`DATA_DIR`/`EREADER_DATA_DIR`, `GREATREADS_DB`, `CALIBRE_URL`, `ABS_*`,
   `PUBLIC_HOST`, `GREATREADS_URL` are **already** env-overridable — no code change.)
6. Everything else (the 46 helper functions, the cache, the locks) is unchanged.

> **Keep `backend/app.py` in place and runnable on `:8091` for now** — it's the
> rollback until the merged container is proven. Delete it in a follow-up.

### 5B. `greatreads/src/greatreads/main.py`

```python
from .routes import books, readings, chains, library, ...   # existing
from . import ereader_api                                    # NEW
...
app.include_router(bookshelves.router, prefix="/api/bookshelves", tags=["bookshelves"])
app.include_router(ereader_api.router, tags=["ereader"])     # NEW — routes already carry /api/...
```

No prefix: the Ereader routes already include their full `/api/...` paths.
No auth dependency (matches their current open behavior; main.py adds no global
auth gate, so this is consistent).

### 5C. `greatreads/pyproject.toml`

Add `requests` (app.py uses `requests`, not GreatReads' `httpx`):
```toml
dependencies = [
    ...
    "requests>=2.31.0",   # NEW — Ereader catalog/cover/HLS calls
]
```

### 5D. `greatreads/Dockerfile`

Bake in the summaries data + version file (the only Ereader assets that aren't
code). After `COPY src ./src`:
```dockerfile
COPY ereader-assets/summaries /app/ereader/summaries
COPY ereader-assets/version.txt /app/ereader/version.txt
```
Stage those into `greatreads/ereader-assets/` first (build context = `greatreads/`):
```
greatreads/ereader-assets/summaries/      ← copy of backend/summaries/*.json (~2.3MB)
greatreads/ereader-assets/version.txt     ← copy of repo-root version.txt
```
(Alternatively symlink/copy at build time via the deploy script. Keep these in
sync with the originals, or — cleaner — have the deploy script copy them.)

### 5E. `greatreads/docker-compose.ereader.yml`

Add to `environment:` (the Calibre/ABS HTTP endpoints + Ereader paths):
```yaml
      # --- Ereader backend (absorbed from :8091) ---
      - CALIBRE_URL=http://host.docker.internal:8083
      - CALIBRE_LIBRARY=library
      - ABS_URL=http://host.docker.internal:13378
      - ABS_PUBLIC_URL=http://100.69.184.113:13378   # phone-facing, for HLS track URLs
      - ABS_LIBRARY_ID=<same as backend/abs.env>
      - PUBLIC_HOST=100.69.184.113:8092              # phone-facing host for cover/HLS URLs
      - GREATREADS_URL=http://127.0.0.1:8006         # self-hop, in-process port (inlined in step 3)
      - EREADER_DATA_DIR=/app/data                   # JSON fallbacks land beside greatreads.db
      - GREATREADS_DB=/app/data/greatreads.db        # the DB app.py reads/writes
      - EREADER_SUMMARIES_DIR=/app/ereader/summaries
      - EREADER_VERSION_FILE=/app/ereader/version.txt
    env_file:
      - ./.ereader.env                               # ABS_TOKEN (secret) — gitignored, see 5F
    extra_hosts:
      - "host.docker.internal:host-gateway"          # lets the container reach :8083/:13378
```
Docker 28.2.2 supports `host-gateway`; host already publishes Calibre `:8083`
and ABS `:13378` on `0.0.0.0` (both return 200 from the host).

### 5F. Secret handling — `greatreads/.ereader.env` (gitignored)

`ABS_TOKEN` must not be committed. Create `greatreads/.ereader.env`:
```
ABS_TOKEN=<value from backend/abs.env>
```
Add `greatreads/.ereader.env` to `.gitignore`. (`backend/abs.env` is already
gitignored; this mirrors it for the container via `env_file`.)

### 5G. Frontend cutover — `web/reader.html`, `web/player.js`, `web/index.html`

Single change in each: the API base host port `8091` → `8092`.
```js
const API_URL = 'http://100.69.184.113:8092/api';   // was :8091
```
(`web/reader.html` line ~1613, `web/player.js` line ~8, `web/index.html` line
~845; also `reader.html` has a bare `http://100.69.184.113:8091/api/build-stamp`
at ~1533 — change that too.) Server-built cover/HLS URLs follow `PUBLIC_HOST`
(set to `:8092` in 5E), so no other frontend edits.

### 5H. Retire `:8091`

`backend/app.py` on `:8091` is bare-metal via `backend/run.sh` (`uvicorn
app:app --reload`) and is **not** under any watchdog (keep-alive.sh only manages
`:8090`). So retiring it = stop the process, stop launching it:
- Stop the running uvicorn (`pkill -f "uvicorn app:app"`).
- Leave `run.sh`/`app.py` in the tree as rollback for now; remove in a follow-up.
- `web/keep-alive.sh` health-probes `:8090/index.html` only — **no change needed**
  (verify it has no `:8091` reference before cutover).

---

## 6. Env-var mapping (current `:8091` value → in-container value)

| Var | `:8091` (bare-metal) | In-container (`:8092`) | Why it changes |
|---|---|---|---|
| `CALIBRE_URL` | `http://localhost:8083` | `http://host.docker.internal:8083` | localhost is the container, not the host |
| `ABS_URL` | `http://localhost:13378` | `http://host.docker.internal:13378` | same |
| `ABS_PUBLIC_URL` | `http://100.69.184.113:13378` | unchanged | already phone-facing |
| `ABS_TOKEN` / `ABS_LIBRARY_ID` | from `backend/abs.env` | via `.ereader.env` | secret moves to container |
| `PUBLIC_HOST` | `100.69.184.113:8091` | `100.69.184.113:8092` | cover/HLS URLs point at the merged port |
| `GREATREADS_URL` | `http://127.0.0.1:8092` | `http://127.0.0.1:8006` | self-call is now in-process port |
| `EREADER_DATA_DIR` | `backend/data` | `/app/data` | mounted, writable, beside the DB |
| `GREATREADS_DB` | `../greatreads/data/greatreads.db` | `/app/data/greatreads.db` | container path |
| `EREADER_SUMMARIES_DIR` | `backend/summaries` | `/app/ereader/summaries` | baked into image |
| `EREADER_VERSION_FILE` | `../version.txt` | `/app/ereader/version.txt` | baked into image |

---

## 7. Risks & edge cases

1. **Container → host networking.** If `host.docker.internal` doesn't resolve,
   fall back to the Tailscale host IP directly: `CALIBRE_URL=http://100.69.184.113:8083`,
   `ABS_URL=http://100.69.184.113:13378` (containers on a bridge can route to the
   host IP). Verify with `docker exec greatreads_ereader curl -sf http://host.docker.internal:8083/ajax/library-info`.
2. **File permissions.** Container user is `greatreads` (uid 1000); the `./data`
   bind mount is owned by host `brandon` (also uid 1000), so JSON-fallback writes
   to `/app/data` should succeed. Verify a `PUT /api/progress` round-trip writes
   without `PermissionError`.
3. **Sync vs async.** app.py's handlers are sync `def` using blocking `requests`;
   FastAPI runs them in a threadpool (default 40). Fine for single-user load, but
   the 3s cold `/api/catalog` ties up a threadpool slot — acceptable, note it.
4. **Schedulers.** The container runs `ENABLE_SCHEDULERS=true` (auto-sync every
   15 min + midnight recalc). The absorbed routes don't add schedulers; no change.
5. **Self-hop is now circular** (`GREATREADS_URL=127.0.0.1:8006` calls the same
   app over HTTP). Works, but it's why step 3 inlines it. Confirm the finish /
   start-next flows still work post-merge.
6. **`reload=True` in `scripts/server.py`** watches `/app/src`; code is baked in
   so nothing changes — harmless, but it means the new `ereader_api.py` must be
   under `/app/src/greatreads/` (it will be, via `COPY src ./src`).
7. **Asset drift.** `ereader-assets/summaries` + `version.txt` are copies; if the
   originals change they must be re-staged. Prefer having the deploy script copy
   `backend/summaries` → `greatreads/ereader-assets/summaries` before build.

---

## 8. Test plan (in order)

1. **Build:** `docker compose -p greatreads_ereader -f greatreads/docker-compose.ereader.yml up -d --build` (USER runs this — never auto-rebuild prod).
2. **Inside container:** `docker exec greatreads_ereader curl -sf localhost:8006/api/catalog | head` ; `.../api/ebooks/<id>/cover -o /dev/null -w '%{http_code}'` ; `.../api/audiobooks` ; `.../api/health`.
3. **Reachability:** `docker exec greatreads_ereader curl -sf http://host.docker.internal:8083/ajax/library-info` and `:13378/ping`.
4. **From host:** `curl :8092/api/catalog`, compare book count to old `:8091` (should match) — diff against a capture taken before cutover.
5. **GreatReads unbroken:** `curl :8092/health`, load `:8090/greatreads/tbr`, `/library`, `/stats`.
6. **Data round-trips:** `PUT /api/progress/_test_` → `GET` → `DELETE`; create/list/delete a `_test_` highlight.
7. **Phone (USER):** open the reader — covers render, a book opens, EPUB download works, an audiobook plays (HLS), highlights + progress save, finish-book + start-next work.
8. Only after all green: stop `:8091`.

Capture a baseline **before** cutover: `curl :8091/api/catalog > /tmp/catalog-8091.json` so step 4 can diff byte-for-byte.

## 9. Rollback

Nothing is destructive. To revert:
- Restart `:8091`: `cd backend && ./run.sh` (app.py + run.sh untouched).
- Point the frontend back: `API_URL` / build-stamp `:8092` → `:8091` in the 3 files.
- The GreatReads container keeps running; the added routes are inert if unused.
`backend/app.py` is retained specifically so this is a 2-minute revert.

## 10. Explicitly deferred (NOT in step 2)

- **Step 3 — collapse the self-hop.** The 7 `GREATREADS_URL` HTTP calls
  (`/api/chains/recalculate`, `/api/readings/*`, `.../tbr`, `.../start`) become
  direct calls into GreatReads' `readings`/`chains` services. Removes the
  circular `127.0.0.1:8006` round-trip.
- **Step 4 — retire the JSON dual-write.** Once stable in one process, drop the
  best-effort `highlights.json`/`progress.json` writes; SQLite is the single
  source of truth. Keep a one-time export script.
- **#8 — fold in `web/serve.py`** (static + proxy) so the reader is served by the
  same app (same-origin, kills the unsupervised `:8090` process + keep-alive
  watchdog), then point `API_URL` at a same-origin relative path.
- **Delete `backend/app.py` + `run.sh`** once the merge is proven.
