"""Shelf model — tracks bookshelf/shelf structure independently of book inventory."""

from sqlalchemy import Column, Integer, String, UniqueConstraint

from ..database import Base


class Shelf(Base):
    """A shelf within a bookshelf. Stores display ordering independently of shelf number."""

    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bookshelf = Column(String, nullable=False)
    shelf_number = Column(Integer, nullable=False)
    # position_order controls display order within a bookshelf (can differ from shelf_number
    # after reordering operations).
    position_order = Column(Integer, nullable=False)
    # bookshelf_order controls the display order of the bookshelf itself (across all bookshelves).
    # All shelf rows for the same bookshelf share the same value; defaults to 0 (alphabetical fallback).
    bookshelf_order = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("bookshelf", "shelf_number", name="uq_shelves_bookshelf_number"),
    )

    def __repr__(self) -> str:
        return f"<Shelf bookshelf={self.bookshelf!r} shelf={self.shelf_number} order={self.position_order}>"
