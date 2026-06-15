"""Data migration script from the original reading tracker."""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greatreads.config import settings
from greatreads.database import create_tables, get_db_session
from greatreads.models import Book, Reading, Inventory


def parse_date(date_str):
    """Parse date string to date object, return None if invalid."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def migrate_data():
    """Migrate data from the original reading tracker database."""
    
    # Check if original database exists
    original_db_path = Path(settings.original_db_path)
    if not original_db_path.exists():
        print(f"❌ Original database not found at: {original_db_path}")
        print("Please update the original_db_path in config.py")
        return False
    
    print(f"📚 Migrating data from: {original_db_path}")
    
    # Create new database tables
    create_tables()
    print("✅ Created new database tables")
    
    # Connect to original database
    original_conn = sqlite3.connect(str(original_db_path))
    original_conn.row_factory = sqlite3.Row
    
    try:
        with get_db_session() as db:
            # Migrate books
            print("📖 Migrating books...")
            books_cursor = original_conn.execute("SELECT * FROM books")
            book_count = 0
            
            for row in books_cursor:
                # Convert row to dict for easier access
                row_dict = dict(row)
                book = Book(
                    id=row_dict['id'],
                    title=row_dict['title'],
                    author_name_first=row_dict.get('author_name_first'),
                    author_name_second=row_dict.get('author_name_second'),
                    author_gender=row_dict.get('author_gender'),
                    word_count=row_dict.get('word_count'),
                    page_count=row_dict.get('page_count'),
                    date_published=parse_date(row_dict.get('date_published')),
                    series=row_dict.get('series'),
                    series_number=row_dict.get('series_number'),
                    genre=row_dict.get('genre'),
                    cover=bool(row_dict.get('cover')) if row_dict.get('cover') is not None else False,
                    isbn_id=row_dict.get('isbn_id'),
                    isbn_10=row_dict.get('isbn_10'),
                    isbn_13=row_dict.get('isbn_13'),
                    asin=row_dict.get('asin'),
                )
                db.add(book)
                book_count += 1
            
            print(f"✅ Migrated {book_count} books")
            
            # Migrate readings
            print("📚 Migrating readings...")
            readings_cursor = original_conn.execute("SELECT * FROM read")
            reading_count = 0
            
            for row in readings_cursor:
                # Convert row to dict for easier access
                row_dict = dict(row)
                reading = Reading(
                    id=row_dict['id'],
                    id_previous=row_dict.get('id_previous'),
                    book_id=row_dict['book_id'],
                    media=row_dict.get('media'),
                    date_started=parse_date(row_dict.get('date_started')),
                    date_finished_actual=parse_date(row_dict.get('date_finished_actual')),
                    rating_horror=row_dict.get('rating_horror'),
                    rating_spice=row_dict.get('rating_spice'),
                    rating_world_building=row_dict.get('rating_world_building'),
                    rating_writing=row_dict.get('rating_writing'),
                    rating_characters=row_dict.get('rating_characters'),
                    rating_readability=row_dict.get('rating_readability'),
                    rating_enjoyment=row_dict.get('rating_enjoyment'),
                    rank=row_dict.get('rank'),
                    days_estimate=row_dict.get('days_estimate'),
                    days_elapsed_to_read=row_dict.get('days_elapsed_to_read'),
                    days_to_read_delta_from_estimate=row_dict.get('days_to_read_delta_from_estimate'),
                    date_est_start=parse_date(row_dict.get('date_est_start')),
                    date_est_end=parse_date(row_dict.get('date_est_end')),
                    reread=bool(row_dict.get('reread', False)),
                    days_estimate_override=bool(row_dict.get('days_estimate_override', False)),
                )
                db.add(reading)
                reading_count += 1
            
            print(f"✅ Migrated {reading_count} readings")
            
            # Migrate inventory
            print("📦 Migrating inventory...")
            try:
                inventory_cursor = original_conn.execute("SELECT * FROM inv")
                inventory_count = 0
                
                for row in inventory_cursor:
                    # Convert row to dict for easier access
                    row_dict = dict(row)

                    # Determine media types owned
                    media_types = []
                    if row_dict.get('owned_audio'):
                        media_types.append('Audio')
                    if row_dict.get('owned_kindle'):
                        media_types.append('Kindle')
                    if row_dict.get('owned_physical'):
                        media_types.append('Physical')

                    # Create inventory entry for each media type owned
                    for media_type in media_types:
                        inventory = Inventory(
                            book_id=row_dict['book_id'],
                            media=media_type,
                            owned=True,
                            location=row_dict.get('location'),
                            notes=f"ISBN-10: {row_dict.get('isbn_10', '')}, ISBN-13: {row_dict.get('isbn_13', '')}" if row_dict.get('isbn_10') or row_dict.get('isbn_13') else None,
                        )
                        db.add(inventory)
                        inventory_count += 1
                    db.add(inventory)
                    inventory_count += 1
                
                print(f"✅ Migrated {inventory_count} inventory entries")
                
            except sqlite3.OperationalError as e:
                if "no such table: inv" in str(e):
                    print("⚠️  No inventory table found in original database")
                else:
                    raise
            
            # Commit all changes
            db.commit()
            print("✅ All data migrated successfully!")
            
            # Print summary
            print("\n📊 Migration Summary:")
            print(f"   Books: {book_count}")
            print(f"   Readings: {reading_count}")
            print(f"   Inventory: {inventory_count if 'inventory_count' in locals() else 0}")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    finally:
        original_conn.close()
    
    return True


def main():
    """Main migration function."""
    print("🔄 Starting data migration...")
    
    if migrate_data():
        print("\n🎉 Migration completed successfully!")
        print(f"New database created at: {settings.database_url}")
        print("\nYou can now start the server with: python scripts/server.py")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
