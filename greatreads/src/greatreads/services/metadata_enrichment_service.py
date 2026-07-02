"""Per-book metadata enrichment (#119).

Query OpenLibrary + Google Books for ONE known book, merge the best value per
field, cross-reference the two sources, and return per-field suggestion rows for
the Edit Book "Request metadata" compare window.

Thin v1 — no house-style normalization (that's #69). **Read-only:** this module
never writes. The client applies accepted values via the existing
``PUT /api/books/{id}`` and ``POST /api/books/{id}/cover/from-url`` endpoints.

Provider strategy (per #119): no fixed primary. Each source is queried at most
once, then per field we take the best value — OpenLibrary for the *original*
publish year and covers, Google for genre; either for pages/series #/cover — and
**cross-reference**: when both agree the row is badged "confirmed by both"; when
they disagree both candidates are offered so the user picks. Results are cached
briefly to protect Google's daily quota against repeat opens.
"""

import os
import time
from typing import Optional

from sqlalchemy.orm import Session

from ..models.book import Book
from ..models.inventory import Inventory
from ..discovery.google_books_client import GoogleBooksClient
from ..discovery.openlibrary_client import OpenLibraryClient
from ..discovery.itunes_client import ITunesClient

# book_id -> (fetched_at, payload). Re-opening the compare window within the TTL
# reuses the fetch instead of spending another Google quota unit.
_CACHE: dict[int, tuple[float, dict]] = {}
_CACHE_TTL = 6 * 3600  # 6 hours

_OL = "OpenLibrary"
_GB = "Google Books"
_AP = "Apple Books"


def _first(seq, pred):
    for x in seq:
        if pred(x):
            return x
    return None


def _iso_date(year: Optional[int], full: Optional[str] = None) -> Optional[str]:
    """Normalize a provider date to an ISO ``YYYY-MM-DD`` string for the Date
    column. Prefer a full date when the source has one; else ``year-01-01``."""
    if full and len(full) >= 10 and full[4] == "-" and full[7] == "-":
        return full[:10]
    if isinstance(year, int) and year > 0:
        return f"{year:04d}-01-01"
    return None


def _date_display(iso: Optional[str]) -> Optional[str]:
    """Show a year-only value (``YYYY-01-01``, our fill for a bare year) as the
    bare year; show a real full date as-is."""
    if not iso:
        return None
    return iso[:4] if iso.endswith("-01-01") else iso


def _google_fields(isbn: Optional[str], title: str, author: str, api_key: str) -> dict:
    """One Google Books lookup (ISBN if present, else title+author), merged across
    the returned editions into the best value per field."""
    gb = GoogleBooksClient(api_key=api_key)
    editions: list[dict] = []
    try:
        if isbn:
            one = gb.get_book_by_isbn(isbn)
            editions = [one] if one else []
        if not editions and title:
            editions = gb.get_editions(title, author)
    except Exception:
        editions = []
    if not editions:
        return {}

    years = [e["year"] for e in editions if isinstance(e.get("year"), int)]
    pages = _first(editions, lambda e: e.get("page_count"))
    cats = _first(editions, lambda e: e.get("categories"))
    snum = _first(editions, lambda e: e.get("series_number") is not None)
    thumb = _first(editions, lambda e: e.get("thumbnail"))
    ref = _first(editions, lambda e: e.get("google_books_id"))

    # A single-edition ISBN hit can carry a full publish date; a title+author
    # sweep spans reprints, so take the earliest year (closest to original).
    if isbn and len(editions) == 1:
        e0 = editions[0]
        date = _iso_date(e0.get("year"), e0.get("published_date"))
    else:
        date = _iso_date(min(years) if years else None)

    return {
        "date": date,
        "page_count": pages.get("page_count") if pages else None,
        "genre": (cats.get("categories") or [None])[0] if cats else None,
        "series_number": snum.get("series_number") if snum else None,
        "cover_url": thumb.get("thumbnail") if thumb else None,
        "ref": ref.get("google_books_id") if ref else None,
    }


def _openlibrary_fields(isbn: Optional[str], title: str, author: str, author_last: str) -> dict:
    """OpenLibrary: the work's original publish year (always, keyless), plus
    pages + cover from the edition when an ISBN is available.

    Search by the author's *last name* rather than the full stored name: this
    library stores initials packed ("JRR", "JK"), which OpenLibrary's author
    match misses, whereas a last-name query ("Tolkien") reliably hits. (Proper
    house-style author normalization is #69; this is just a better query key.)"""
    olc = OpenLibraryClient()
    year = None
    edition: dict = {}
    try:
        if title:
            year = olc.first_publish_year(title, author_last or author)
        if isbn:
            edition = olc.edition_by_isbn(isbn) or {}
    except Exception:
        pass
    return {
        "date": _iso_date(year),
        "page_count": edition.get("pages"),
        "cover_url": edition.get("cover_url"),
    }


def _build_field(field: str, label: str, current, raw_candidates, is_cover=False) -> Optional[dict]:
    """Dedupe candidates by their apply-value; when the same value comes from more
    than one source, collapse to one row badged as agreed ("confirmed by both")."""
    merged: list[dict] = []
    for c in raw_candidates:
        if not c:
            continue
        key = c.get("url") if is_cover else c.get("value")
        if key in (None, ""):
            continue
        existing = _first(
            merged, lambda m: (m.get("url") if is_cover else m.get("value")) == key
        )
        if existing:
            if c["source"] not in existing["sources"]:
                existing["sources"].append(c["source"])
                existing["agree"] = True
        else:
            merged.append({**c, "sources": [c["source"]], "agree": False})
    if not merged:
        return None
    for m in merged:
        m["source"] = " + ".join(m.pop("sources"))
    return {
        "field": field,
        "label": label,
        "current": current,
        "is_cover": is_cover,
        "candidates": merged,
    }


def suggest_metadata(db: Session, book_id: int) -> Optional[dict]:
    """Return the compare-window payload for one book, or None if it doesn't exist."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None

    cached = _CACHE.get(book_id)
    if cached and (time.time() - cached[0]) < _CACHE_TTL:
        return cached[1]

    title = (book.title or "").strip()
    author = book.author or ""
    author_last = (book.author_name_second or "").strip()

    # Prefer an ISBN from inventory as the precise lookup key; most records
    # (and all Unowned ones) have none → fall back to title+author.
    isbn = None
    for inv in db.query(Inventory).filter(Inventory.book_id == book_id).all():
        cand = (inv.isbn_13 or inv.isbn_10 or "").strip()
        if cand:
            isbn = cand
            break

    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
    g = _google_fields(isbn, title, author, api_key) if api_key else {}
    o = _openlibrary_fields(isbn, title, author, author_last)
    # Apple Books — cover only, free/keyless, usually the highest-res candidate (#130).
    try:
        apple_cover = ITunesClient().cover_by_title_author(title, author) if title else None
    except Exception:
        apple_cover = None

    def cand(value, source, display=None, url=None):
        if value in (None, "") and not url:
            return None
        return {"value": value, "display": (display if display is not None else value),
                "source": source, "url": url}

    cur_date = book.date_published.isoformat() if book.date_published else None
    fields = [
        _build_field(
            "date_published", "Published", _date_display(cur_date),
            [cand(o.get("date"), _OL, _date_display(o.get("date"))),
             cand(g.get("date"), _GB, _date_display(g.get("date")))],
        ),
        _build_field(
            "page_count", "Pages", book.page_count,
            [cand(g.get("page_count"), _GB),
             cand(o.get("page_count"), _OL)],
        ),
        _build_field(
            "series_number", "Series #", book.series_number,
            [cand(g.get("series_number"), _GB)],
        ),
        _build_field(
            "genre", "Genre", book.genre,
            [cand(g.get("genre"), _GB)],
        ),
        _build_field(
            "cover", "Cover", bool(book.cover),
            [cand(None, _AP, "Apple Books cover", url=apple_cover),
             cand(None, _OL, "OpenLibrary cover", url=o.get("cover_url")),
             cand(None, _GB, "Google cover", url=g.get("cover_url"))],
            is_cover=True,
        ),
    ]

    payload = {
        "book_id": book_id,
        "query": {"mode": "isbn" if isbn else "title_author",
                  "isbn": isbn, "title": title, "author": author},
        "providers": {"google": bool(api_key and g), "openlibrary": bool(o),
                      "apple": bool(apple_cover)},
        "fields": [f for f in fields if f],
    }
    _CACHE[book_id] = (time.time(), payload)
    return payload
