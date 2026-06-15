"""External import tracking model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from ..database import Base


class ExternalImport(Base):
    """Tracks books imported or linked from external library sources (Calibre, ABS)."""

    __tablename__ = 'external_imports'

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)          # 'calibre' or 'audiobookshelf'
    external_id = Column(String, nullable=False)      # Calibre int ID or ABS UUID
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    action = Column(String, nullable=False)           # 'created' or 'linked'
    imported_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    book = relationship("Book")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "external_id": self.external_id,
            "book_id": self.book_id,
            "action": self.action,
            "imported_at": self.imported_at.isoformat() if self.imported_at else None,
        }


class ExternalImportCreate(BaseModel):
    source: str
    external_id: str
    book_id: int
    action: str  # 'created' or 'linked'


class ExternalImportResponse(BaseModel):
    id: int
    source: str
    external_id: str
    book_id: int
    action: str
    imported_at: Optional[datetime] = None

    class Config:
        from_attributes = True

