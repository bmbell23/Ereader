"""Per-book metadata enrichment routes (#119).

``POST /api/enrichment/{book_id}/suggest`` — look up a known book from
OpenLibrary + Google Books and return per-field suggestion rows for the Edit Book
compare window. Apply is client-side (reuse ``PUT /api/books/{id}`` +
``POST /api/books/{id}/cover/from-url``), so there is no ``/apply`` here in v1.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..services.metadata_enrichment_service import suggest_metadata

router = APIRouter()


@router.post("/{book_id}/suggest")
async def suggest(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suggested metadata + cover candidates for one book (review-before-apply)."""
    result = suggest_metadata(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return result
