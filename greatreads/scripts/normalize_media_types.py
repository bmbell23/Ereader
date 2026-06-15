#!/usr/bin/env python3
"""Script to normalize legacy media types in the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greatreads.database import get_db_session
from greatreads.models.reading import Reading


def normalize_media_types():
    """Normalize all legacy media types in the database."""
    with get_db_session() as db:
        # Find all readings with legacy media types
        readings = db.query(Reading).filter(
            Reading.media.in_(['Hardcover', 'hardcover', 'Audiobook', 'audiobook'])
        ).all()
        
        if not readings:
            print("No readings with legacy media types found.")
            return
        
        print(f"Found {len(readings)} readings with legacy media types:")
        
        for reading in readings:
            old_media = reading.media
            
            # Normalize
            if reading.media.lower() == 'hardcover':
                reading.media = 'Physical'
            elif reading.media.lower() == 'audiobook':
                reading.media = 'Audio'
            
            print(f"  - Reading ID {reading.id}: {old_media} -> {reading.media}")
        
        # Commit changes
        db.commit()
        print(f"\nSuccessfully normalized {len(readings)} readings.")


if __name__ == "__main__":
    normalize_media_types()

