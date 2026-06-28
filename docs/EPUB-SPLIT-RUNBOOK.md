# EPUB split / make runbook — keeping highlights & bookmarks working

When we extract a single work out of an anthology (or otherwise "make" an EPUB),
the result must stay **anchorable** or the reader can't attach highlights or
bookmarks to it. This is what bit "The Burning Man" (Calibre #1241): 60 pages but
only ~2 anchor points, so highlights/bookmarks had nowhere to land.

## Why it matters — how the reader anchors (don't break this)

The reader (`web/reader.html`) does **not** use EPUB CFIs, element `id`s, or page
numbers. On load it concatenates each spine document's `<body>` and assigns a
monotonic integer `data-anchor="N"` to every **block-level leaf element** it finds:

```
ANCHOR_SELECTOR = 'p, h1, h2, h3, h4, h5, h6, li, blockquote, pre, figure, img, table, hr, dd, dt'
```
(`annotateAnchors` in `reader.html`). **`div` and `span` are deliberately excluded.**

- A **highlight** = `(anchor index, char offset, length)` into that element's text.
- A **bookmark** = the first-visible anchor index.
- Both are recomputed fresh from the DOM on every load, so they survive font-size
  changes and repagination — but they depend entirely on the body text being in
  **real block elements**.

**Failure mode:** if a chapter's body text is one big `<div>` with `<br>` line
breaks (and no `<p>`/headings), the whole chapter collapses to a *single* anchor.
That's the Burning Man signature — text was hand-extracted into flat `<div>`s, so
`querySelectorAll(ANCHOR_SELECTOR)` returns ~1 element per spine doc. There's
nowhere to anchor, so highlights/bookmarks don't work.

**The one structural guarantee:** every split/made EPUB's body text must be marked
up in `<p>` / heading / `<li>` / `<blockquote>` elements — **never a single flat
`<div>`+`<br>` blob.** Multiple spine docs are fine; a nav/toc is nice but not
required; `id`s and CFIs are not needed.

## The split process (anthology → one EPUB per work)

1. **Split on spine/TOC boundaries**, preserving each piece's existing `<p>` markup
   — use Calibre's **EpubSplit** plugin (`calibre-debug -r EpubSplit -- …`) or the
   `epubsplit` CLI. Do **not** hand-copy text into a new flat file (that's what
   produced the broken Burning Man).
2. **Normalize/repair** each output: `ebook-polish --upgrade-book work.epub`
   (fixes manifest/nav, subsets fonts).
3. **If a piece still has flat `<div>`/`<br>` body text**, mark up paragraphs:
   `ebook-convert work.epub work.epub --enable-heuristics` (Calibre's
   "Markup unmarked paragraphs" heuristic). Watch for over/under-splitting; spot
   check.
4. **Anchorability gate (do this BEFORE import):** count
   `p|h1..h6|li|blockquote` elements across the spine docs; reject/flag if the count
   is implausibly low (rule of thumb: < ~10× the number of spine docs). A cheap
   check: `python3 -c` + `zipfile` to read each spine xhtml and count block tags.
5. **Import via the normal acsm / server-mediated pipeline** — never write Calibre's
   `metadata.db` directly (see Calibre-write-safety), and ask before DB writes/rebuilds.

## Scriptability

Mostly scriptable: the split (EpubSplit/epubsplit CLI), the polish/convert pass,
and the anchorability gate (Python `zipfile`/`lxml`/`ebooklib` counting block tags)
all run headless. **No anchor/CFI regeneration is ever needed** — the reader rebuilds
`data-anchor` indices from the DOM each load, so the script only has to guarantee good
`<p>` structure.

Two spots may still need a human:
- **Work-boundary detection** when a single xhtml holds multiple stories (needs
  heuristic or manual split points).
- **Heuristic paragraph-marking** aggressiveness on flat-`<div>` inputs — occasionally
  over/under-splits; a quick spot check is worth it.

Sketch:
```
for each work boundary:
    EpubSplit            -> work.epub          # preserves <p> + nav per piece
    ebook-polish --upgrade-book work.epub      # repair
    n = count(p|h1..h6|li|blockquote in spine docs)
    if n < threshold:                          # flat-div input
        ebook-convert work.epub work.epub --enable-heuristics
        recount; if still low -> flag for manual review
    import via acsm/server pipeline
```

## Repairing an already-broken book (e.g. The Burning Man)

Re-run the existing EPUB through `ebook-convert … --enable-heuristics` (or re-split
properly from the source anthology), verify the block-tag count, and re-import via
the server-mediated pipeline. The old stale auto-bookmarks (anchors 0/1) are harmless
and can be ignored. Gated actions (Calibre import / DB / rebuild) → ask first.
