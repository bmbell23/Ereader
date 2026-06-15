"""Bookshelves API routes — physical shelf management."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.book import Book
from ..models.inventory import Inventory
from ..models.shelf import Shelf

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _inv_to_book_entry(inv: Inventory) -> Dict[str, Any]:
    book = inv.book
    return {
        "inventory_id": inv.id,
        "book_id": inv.book_id,
        "title": book.title if book else None,
        "author": book.author if book else None,
        "cover": book.cover if book else False,
        "series": book.series if book else None,
        "series_number": book.series_number if book else None,
        "shelf_bookshelf": inv.shelf_bookshelf,
        "shelf_shelf": inv.shelf_shelf,
        "shelf_position": inv.shelf_position,
        "location": inv.location,
    }


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------

@router.get("/")
async def get_bookshelves(db: Session = Depends(get_db)):
    """Return all bookshelf labels ordered by bookshelf_order then alphabetically."""
    rows = (
        db.query(Shelf.bookshelf, func.min(Shelf.bookshelf_order).label("bs_order"))
        .group_by(Shelf.bookshelf)
        .order_by("bs_order", Shelf.bookshelf)
        .all()
    )
    labels = [r[0] for r in rows if r[0]]
    count_rows = (
        db.query(Inventory.shelf_bookshelf, func.count(Inventory.id))
        .filter(
            Inventory.owned_physical == True,
            Inventory.shelf_bookshelf.isnot(None),
        )
        .group_by(Inventory.shelf_bookshelf)
        .all()
    )
    counts = {r[0]: r[1] for r in count_rows}
    return {"bookshelves": labels, "counts": counts}


@router.get("/unlocated")
async def get_unlocated_books(db: Session = Depends(get_db)):
    """Return physical books that have no shelf coordinates assigned."""
    invs = (
        db.query(Inventory)
        .options(joinedload(Inventory.book))
        .filter(
            Inventory.owned_physical == True,
            Inventory.shelf_bookshelf.is_(None),
        )
        .all()
    )
    return [_inv_to_book_entry(i) for i in invs]


@router.get("/search/books")
async def search_physical_books(
    q: str = "",
    exclude_bookshelf: Optional[str] = None,
    exclude_shelf: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Search physical books to add to a shelf.

    Matches by title/author, returns each book's current location, and excludes
    books already on the target shelf. Used by the per-shelf "+" add-book modal.
    """
    query = (
        db.query(Inventory)
        .options(joinedload(Inventory.book))
        .join(Book, Inventory.book_id == Book.id)
        .filter(Inventory.owned_physical == True)
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            Book.title.ilike(like)
            | Book.author_name_first.ilike(like)
            | Book.author_name_second.ilike(like)
            | Book.series.ilike(like)
        )
    invs = query.order_by(Book.series, Book.series_number, Book.title).limit(50).all()

    excl_bs = exclude_bookshelf if exclude_bookshelf else None
    results = []
    for inv in invs:
        if (
            excl_bs is not None
            and exclude_shelf is not None
            and inv.shelf_bookshelf == excl_bs
            and inv.shelf_shelf == exclude_shelf
        ):
            continue
        results.append(_inv_to_book_entry(inv))
    return results


@router.get("/series/books")
async def get_series_books(
    series: str,
    exclude_bookshelf: Optional[str] = None,
    exclude_shelf: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return all physical books in a series, ordered by series_number.

    Used by the "add whole series" action so the full series can be added even
    when it exceeds the search result cap. Excludes books already on the target shelf.
    """
    invs = (
        db.query(Inventory)
        .options(joinedload(Inventory.book))
        .join(Book, Inventory.book_id == Book.id)
        .filter(Inventory.owned_physical == True, Book.series == series)
        .order_by(Book.series_number, Book.title)
        .all()
    )
    excl_bs = exclude_bookshelf if exclude_bookshelf else None
    results = []
    for inv in invs:
        if (
            excl_bs is not None
            and exclude_shelf is not None
            and inv.shelf_bookshelf == excl_bs
            and inv.shelf_shelf == exclude_shelf
        ):
            continue
        results.append(_inv_to_book_entry(inv))
    return results


# ---------------------------------------------------------------------------
# Write endpoints — books
# ---------------------------------------------------------------------------

class MoveRequest(BaseModel):
    inventory_id: int
    shelf_bookshelf: str
    shelf_shelf: int
    shelf_position: int


class MoveBulkRequest(BaseModel):
    inventory_ids: List[int]
    shelf_bookshelf: str
    shelf_shelf: int


def _resequence(db: Session, bookshelf: str, shelf: int) -> None:
    """Renumber shelf_position 1..N for all books on a shelf, preserving order."""
    books = (
        db.query(Inventory)
        .filter(
            Inventory.shelf_bookshelf == bookshelf,
            Inventory.shelf_shelf == shelf,
        )
        .order_by(Inventory.shelf_position, Inventory.id)
        .all()
    )
    for idx, b in enumerate(books, start=1):
        b.shelf_position = idx


@router.put("/move")
async def move_book(req: MoveRequest, db: Session = Depends(get_db)):
    """Move a book to a target bookshelf/shelf/position.

    Uses a list-rebuild approach: pull the ordered list of the target shelf
    (excluding the moved book), insert the moved book at the requested index,
    then renumber positions sequentially on both the source and target shelves.
    Auto-creates a shelf row in the shelves table if the target doesn't exist yet.
    """
    inv = db.query(Inventory).filter(Inventory.id == req.inventory_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory entry not found")

    new_bs = req.shelf_bookshelf
    new_shelf = req.shelf_shelf
    old_bs = inv.shelf_bookshelf
    old_shelf = inv.shelf_shelf

    # Ensure the target shelf exists in the structure table.
    target_shelf_row = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == new_bs, Shelf.shelf_number == new_shelf)
        .first()
    )
    if not target_shelf_row:
        max_order = (
            db.query(func.max(Shelf.position_order))
            .filter(Shelf.bookshelf == new_bs)
            .scalar()
        ) or 0
        db.add(Shelf(bookshelf=new_bs, shelf_number=new_shelf, position_order=max_order + 1))

    # Ordered list of books currently on the target shelf, excluding the moved book.
    target_books = (
        db.query(Inventory)
        .filter(
            Inventory.shelf_bookshelf == new_bs,
            Inventory.shelf_shelf == new_shelf,
            Inventory.id != req.inventory_id,
        )
        .order_by(Inventory.shelf_position, Inventory.id)
        .all()
    )

    # Clamp insert index into a valid range (1-based position).
    new_pos = max(1, min(req.shelf_position, len(target_books) + 1))

    # Insert the moved book at the requested index and renumber the target shelf.
    target_books.insert(new_pos - 1, inv)
    inv.shelf_bookshelf = new_bs
    inv.shelf_shelf = new_shelf
    for idx, b in enumerate(target_books, start=1):
        b.shelf_position = idx

    # Compact the source shelf if the book moved off it.
    if old_bs != new_bs or old_shelf != new_shelf:
        if old_bs is not None and old_shelf is not None:
            _resequence(db, old_bs, old_shelf)

    db.commit()
    return {"ok": True}


@router.put("/move-bulk")
async def move_books_bulk(req: MoveBulkRequest, db: Session = Depends(get_db)):
    """Append multiple books (in the given order) to the end of a target shelf.

    Used by the per-shelf "+" modal's "add whole series" action. Books already on
    the target shelf are skipped; source shelves the books came from are compacted.
    Auto-creates the target shelf row if it doesn't exist yet.
    """
    if not req.inventory_ids:
        return {"ok": True, "moved": 0}

    new_bs = req.shelf_bookshelf
    new_shelf = req.shelf_shelf

    # Ensure the target shelf exists in the structure table.
    target_shelf_row = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == new_bs, Shelf.shelf_number == new_shelf)
        .first()
    )
    if not target_shelf_row:
        max_order = (
            db.query(func.max(Shelf.position_order))
            .filter(Shelf.bookshelf == new_bs)
            .scalar()
        ) or 0
        db.add(Shelf(bookshelf=new_bs, shelf_number=new_shelf, position_order=max_order + 1))

    # Current end-of-shelf position on the target.
    max_pos = (
        db.query(func.max(Inventory.shelf_position))
        .filter(Inventory.shelf_bookshelf == new_bs, Inventory.shelf_shelf == new_shelf)
        .scalar()
    ) or 0

    source_shelves = set()
    moved = 0
    for inv_id in req.inventory_ids:
        inv = db.query(Inventory).filter(Inventory.id == inv_id).first()
        if not inv:
            continue
        # Skip books already on the target shelf.
        if inv.shelf_bookshelf == new_bs and inv.shelf_shelf == new_shelf:
            continue
        if inv.shelf_bookshelf is not None and inv.shelf_shelf is not None:
            source_shelves.add((inv.shelf_bookshelf, inv.shelf_shelf))
        max_pos += 1
        inv.shelf_bookshelf = new_bs
        inv.shelf_shelf = new_shelf
        inv.shelf_position = max_pos
        moved += 1

    # Compact each source shelf the books were pulled from.
    for bs, sh in source_shelves:
        if (bs, sh) != (new_bs, new_shelf):
            _resequence(db, bs, sh)

    db.commit()
    return {"ok": True, "moved": moved}


# ---------------------------------------------------------------------------
# Write endpoints — structure (bookshelves & shelves)
# ---------------------------------------------------------------------------

class CreateBookshelfRequest(BaseModel):
    label: str


class RenameBookshelfRequest(BaseModel):
    new_label: str


class ReorderBookshelvesRequest(BaseModel):
    order: List[str]  # full ordered list of bookshelf labels, e.g. ["B", "A", "C"]


class ReorderShelvesRequest(BaseModel):
    shelf_a: int
    shelf_b: int


class MoveShelfRequest(BaseModel):
    shelf_number: int
    target_bookshelf: str


@router.post("/bookshelf")
async def create_bookshelf(req: CreateBookshelfRequest, db: Session = Depends(get_db)):
    """Create a new bookshelf (with an initial empty shelf 1)."""
    label = req.label.strip()
    if not label:
        raise HTTPException(status_code=400, detail="Label cannot be empty")
    existing = db.query(Shelf).filter(Shelf.bookshelf == label).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Bookshelf '{label}' already exists")
    max_bs_order = db.query(func.max(Shelf.bookshelf_order)).scalar() or 0
    db.add(Shelf(bookshelf=label, shelf_number=1, position_order=1, bookshelf_order=max_bs_order + 1))
    db.commit()
    return {"ok": True, "bookshelf": label}


@router.post("/{bookshelf}/shelf")
async def add_shelf(bookshelf: str, db: Session = Depends(get_db)):
    """Append a new shelf to an existing bookshelf."""
    max_shelf = (
        db.query(func.max(Shelf.shelf_number))
        .filter(Shelf.bookshelf == bookshelf)
        .scalar()
    )
    if max_shelf is None:
        raise HTTPException(status_code=404, detail=f"Bookshelf '{bookshelf}' not found")
    max_order = (
        db.query(func.max(Shelf.position_order))
        .filter(Shelf.bookshelf == bookshelf)
        .scalar()
    ) or 0
    next_num = max_shelf + 1
    db.add(Shelf(bookshelf=bookshelf, shelf_number=next_num, position_order=max_order + 1))
    db.commit()
    return {"ok": True, "shelf_number": next_num}


@router.put("/{bookshelf}/reorder-shelves")
async def reorder_shelves(bookshelf: str, req: ReorderShelvesRequest, db: Session = Depends(get_db)):
    """Swap the display order of two shelves within a bookshelf."""
    shelf_a = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == bookshelf, Shelf.shelf_number == req.shelf_a)
        .first()
    )
    shelf_b = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == bookshelf, Shelf.shelf_number == req.shelf_b)
        .first()
    )
    if not shelf_a or not shelf_b:
        raise HTTPException(status_code=404, detail="One or both shelves not found")
    shelf_a.position_order, shelf_b.position_order = shelf_b.position_order, shelf_a.position_order
    db.commit()
    return {"ok": True}


@router.put("/{bookshelf}/move-shelf")
async def move_shelf_to_bookshelf(bookshelf: str, req: MoveShelfRequest, db: Session = Depends(get_db)):
    """Move an entire shelf (and all its books) to a different bookshelf.

    The shelf is appended at the end of the target bookshelf with a fresh shelf
    number; each book keeps its shelf_position so the books stay in order.
    """
    src_bs = bookshelf
    target_bs = req.target_bookshelf
    if src_bs == target_bs:
        raise HTTPException(status_code=400, detail="Source and target bookshelf are the same")

    shelf_row = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == src_bs, Shelf.shelf_number == req.shelf_number)
        .first()
    )
    if not shelf_row:
        raise HTTPException(status_code=404, detail="Shelf not found")

    if not db.query(Shelf).filter(Shelf.bookshelf == target_bs).first():
        raise HTTPException(status_code=404, detail=f"Bookshelf '{target_bs}' not found")

    # Append at the end of the target bookshelf with a fresh shelf number / order.
    new_shelf_num = ((
        db.query(func.max(Shelf.shelf_number)).filter(Shelf.bookshelf == target_bs).scalar()
    ) or 0) + 1
    new_order = ((
        db.query(func.max(Shelf.position_order)).filter(Shelf.bookshelf == target_bs).scalar()
    ) or 0) + 1

    # Repoint all books on the shelf, preserving their existing shelf_position.
    books = (
        db.query(Inventory)
        .filter(Inventory.shelf_bookshelf == src_bs, Inventory.shelf_shelf == req.shelf_number)
        .all()
    )
    for b in books:
        b.shelf_bookshelf = target_bs
        b.shelf_shelf = new_shelf_num

    # Move the shelf structure row itself.
    shelf_row.bookshelf = target_bs
    shelf_row.shelf_number = new_shelf_num
    shelf_row.position_order = new_order

    db.commit()
    return {"ok": True, "target_bookshelf": target_bs, "shelf_number": new_shelf_num}


@router.put("/bookshelf/{label}/rename")
async def rename_bookshelf(label: str, req: RenameBookshelfRequest, db: Session = Depends(get_db)):
    """Rename a bookshelf label. Updates all shelves and book inventory rows."""
    old = label.strip()
    new = req.new_label.strip()
    if not new:
        raise HTTPException(status_code=400, detail="Label cannot be empty")
    if old == new:
        return {"ok": True, "label": new}
    if not db.query(Shelf).filter(Shelf.bookshelf == old).first():
        raise HTTPException(status_code=404, detail=f"Bookshelf '{old}' not found")
    if db.query(Shelf).filter(Shelf.bookshelf == new).first():
        raise HTTPException(status_code=409, detail=f"Bookshelf '{new}' already exists")
    db.query(Shelf).filter(Shelf.bookshelf == old).update({"bookshelf": new})
    db.query(Inventory).filter(Inventory.shelf_bookshelf == old).update({"shelf_bookshelf": new})
    db.commit()
    return {"ok": True, "label": new}


@router.put("/reorder-bookshelves")
async def reorder_bookshelves_endpoint(req: ReorderBookshelvesRequest, db: Session = Depends(get_db)):
    """Set the display order of bookshelves. `order` is the full ordered list of labels."""
    for idx, label in enumerate(req.order, start=1):
        db.query(Shelf).filter(Shelf.bookshelf == label).update({"bookshelf_order": idx})
    db.commit()
    return {"ok": True}


@router.get("/{bookshelf}")
async def get_bookshelf(bookshelf: str, db: Session = Depends(get_db)):
    """Return all shelves and their books for a given bookshelf label.

    Shelf order is determined by the shelves table (position_order), not shelf_number,
    so reordering is reflected here immediately.
    """
    shelves_list = (
        db.query(Shelf)
        .filter(Shelf.bookshelf == bookshelf)
        .order_by(Shelf.position_order)
        .all()
    )
    if not shelves_list:
        raise HTTPException(status_code=404, detail=f"Bookshelf '{bookshelf}' not found")

    all_invs = (
        db.query(Inventory)
        .options(joinedload(Inventory.book))
        .filter(
            Inventory.owned_physical == True,
            Inventory.shelf_bookshelf == bookshelf,
        )
        .order_by(Inventory.shelf_shelf, Inventory.shelf_position, Inventory.id)
        .all()
    )

    books_by_shelf: Dict[int, List[Dict]] = {}
    for inv in all_invs:
        shelf_num = inv.shelf_shelf or 0
        books_by_shelf.setdefault(shelf_num, []).append(_inv_to_book_entry(inv))

    return {
        "bookshelf": bookshelf,
        "shelves": [
            {"shelf": s.shelf_number, "books": books_by_shelf.get(s.shelf_number, [])}
            for s in shelves_list
        ],
    }
