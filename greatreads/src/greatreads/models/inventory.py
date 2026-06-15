"""Inventory model."""

from typing import Optional, List
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from ..database import Base


class Inventory(Base):
    """Book inventory database model."""

    __tablename__ = 'inv'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    owned_audio = Column(Boolean, default=False)
    owned_ebook = Column(Boolean, default=False)
    owned_physical = Column(Boolean, default=False)
    # Graphic Audio / dramatized-adaptation tracking.
    # graphic_audio=1  -> the audio version is a GA dramatization.
    # owned_in_library=0 -> GA title matched another GR book but author didn't;
    #                       flagged for review, excluded from owned_audio count.
    graphic_audio = Column(Boolean, default=False)
    owned_in_library = Column(Boolean, default=True)
    date_purchased = Column(Date)
    location = Column(String)
    # 3-coordinate physical location system:
    #   shelf_bookshelf  : bookshelf label (e.g. "A", "B")
    #   shelf_shelf      : shelf number on that bookshelf (e.g. 1, 2)
    #   shelf_position   : position of the book on that shelf (1-based, left to right)
    shelf_bookshelf = Column(String)
    shelf_shelf = Column(Integer)
    shelf_position = Column(Integer)
    read_status = Column(String)
    read_count = Column(Integer)
    isbn_10 = Column(String(10))
    isbn_13 = Column(String(13))

    # Relationships
    book = relationship("Book", back_populates="inventory")

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        # Calculate owned media types
        owned_media = []
        if self.owned_audio:
            owned_media.append("Audio")
        if self.owned_ebook:
            owned_media.append("Ebook")
        if self.owned_physical:
            owned_media.append("Physical")

        return {
            "id": self.id,
            "book_id": self.book_id,
            "owned_audio": self.owned_audio,
            "owned_ebook": self.owned_ebook,
            "owned_physical": self.owned_physical,
            "owned_media": owned_media,
            "date_purchased": self.date_purchased.isoformat() if self.date_purchased else None,
            "location": self.location,
            "shelf_bookshelf": self.shelf_bookshelf,
            "shelf_shelf": self.shelf_shelf,
            "shelf_position": self.shelf_position,
            "read_status": self.read_status,
            "read_count": self.read_count,
            "isbn_10": self.isbn_10,
            "isbn_13": self.isbn_13,
            # Include book data for convenience
            "book": self.book.to_dict() if self.book else None,
        }


# Pydantic models for API
class InventoryBase(BaseModel):
    """Base inventory schema."""
    book_id: int
    owned_audio: bool = False
    owned_ebook: bool = False
    owned_physical: bool = False
    date_purchased: Optional[date] = None
    location: Optional[str] = None
    shelf_bookshelf: Optional[str] = None
    shelf_shelf: Optional[int] = None
    shelf_position: Optional[int] = None
    read_status: Optional[str] = None
    read_count: Optional[int] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None


class InventoryCreate(InventoryBase):
    """Schema for creating inventory entries."""
    pass


class InventoryUpdate(BaseModel):
    """Schema for updating inventory entries."""
    book_id: Optional[int] = None
    owned_audio: Optional[bool] = None
    owned_ebook: Optional[bool] = None
    owned_physical: Optional[bool] = None
    date_purchased: Optional[date] = None
    location: Optional[str] = None
    shelf_bookshelf: Optional[str] = None
    shelf_shelf: Optional[int] = None
    shelf_position: Optional[int] = None
    read_status: Optional[str] = None
    read_count: Optional[int] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None


class InventoryResponse(BaseModel):
    """Schema for inventory responses."""
    id: int
    book_id: int
    owned_audio: bool = False
    owned_ebook: bool = False
    owned_physical: bool = False
    owned_media: List[str]
    date_purchased: Optional[date] = None
    location: Optional[str] = None
    shelf_bookshelf: Optional[str] = None
    shelf_shelf: Optional[int] = None
    shelf_position: Optional[int] = None
    read_status: Optional[str] = None
    read_count: Optional[int] = None
    isbn_10: Optional[str] = None
    isbn_13: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle owned_media computation."""
        owned_media = []
        if obj.owned_audio:
            owned_media.append("Audio")
        if obj.owned_ebook:
            owned_media.append("Ebook")
        if obj.owned_physical:
            owned_media.append("Physical")

        return cls(
            id=obj.id,
            book_id=obj.book_id,
            owned_audio=obj.owned_audio,
            owned_ebook=obj.owned_ebook,
            owned_physical=obj.owned_physical,
            owned_media=owned_media,
            date_purchased=obj.date_purchased,
            location=obj.location,
            shelf_bookshelf=obj.shelf_bookshelf,
            shelf_shelf=obj.shelf_shelf,
            shelf_position=obj.shelf_position,
            read_status=obj.read_status,
            read_count=obj.read_count,
            isbn_10=obj.isbn_10,
            isbn_13=obj.isbn_13
        )
