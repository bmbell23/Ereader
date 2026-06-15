"""User settings model."""

from typing import Optional
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel

from ..database import Base


class UserSettings(Base):
    """User settings database model."""

    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True)
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(String, nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
        }


# Pydantic models for API
class UserSettingsBase(BaseModel):
    """Base user settings schema."""
    setting_key: str
    setting_value: str


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings."""
    pass


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    setting_value: str


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings responses."""
    id: int

    class Config:
        from_attributes = True


class ReadingSpeedsSettings(BaseModel):
    """Schema for reading speeds settings."""
    ebook_wpd: int = 15000
    physical_wpd: int = 12000
    audio_wpd: int = 25000

    class Config:
        from_attributes = True

