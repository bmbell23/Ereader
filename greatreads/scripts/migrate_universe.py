"""Migration script to add universe column and extract universe from series names."""

import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from greatreads.database import get_db_session, engine
from greatreads.models import Book
from sqlalchemy import text


def extract_universe_and_series(series_name: str) -> tuple[str | None, str]:
    """
    Extract universe and series from a series name.
    
    Examples:
        "Cosmere (Mistborn)" -> ("Cosmere", "Mistborn")
        "Maasverse (Throne of Glass)" -> ("Maasverse", "Throne of Glass")
        "The Wandering Inn (Volume 1)" -> ("The Wandering Inn", "Volume 1")
        "Harry Potter" -> (None, "Harry Potter")
    
    Returns:
        Tuple of (universe, series) where universe may be None
    """
    if not series_name:
        return None, series_name
    
    # Pattern to match "Universe (Series)" format
    match = re.match(r'^(.+?)\s*\((.+?)\)$', series_name)
    
    if match:
        universe = match.group(1).strip()
        series = match.group(2).strip()
        return universe, series
    
    # No universe found
    return None, series_name


def migrate_universe():
    """Add universe column and migrate existing data."""
    
    print("🔄 Starting universe migration...")
    
    # Step 1: Add universe column to the database
    print("\n📊 Adding universe column to books table...")
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(books)"))
            columns = [row[1] for row in result]
            
            if 'universe' in columns:
                print("✅ Universe column already exists")
            else:
                conn.execute(text("ALTER TABLE books ADD COLUMN universe VARCHAR"))
                conn.commit()
                print("✅ Universe column added successfully")
    except Exception as e:
        print(f"❌ Error adding universe column: {e}")
        return False
    
    # Step 2: Migrate data
    print("\n📚 Migrating series data...")
    
    with get_db_session() as db:
        # Get all books with series
        books = db.query(Book).filter(Book.series.isnot(None)).all()
        
        updated_count = 0
        unchanged_count = 0
        
        for book in books:
            universe, series = extract_universe_and_series(book.series)
            
            if universe:
                # Update the book
                book.universe = universe
                book.series = series
                updated_count += 1
                print(f"  📖 {book.title}: '{book.universe} ({book.series})' -> Universe: '{universe}', Series: '{series}'")
            else:
                unchanged_count += 1
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"   Updated: {updated_count} books")
        print(f"   Unchanged: {unchanged_count} books")
        print(f"   Total: {len(books)} books with series")
    
    # Step 3: Show summary of universes
    print("\n🌌 Universe Summary:")
    with get_db_session() as db:
        universes = db.query(Book.universe).filter(Book.universe.isnot(None)).distinct().all()
        universes = sorted([u[0] for u in universes if u[0]])
        
        for universe in universes:
            # Count series in this universe
            series_in_universe = db.query(Book.series).filter(
                Book.universe == universe
            ).distinct().all()
            series_count = len([s[0] for s in series_in_universe if s[0]])
            
            # Count books in this universe
            book_count = db.query(Book).filter(Book.universe == universe).count()
            
            print(f"   {universe}: {series_count} series, {book_count} books")
    
    return True


def main():
    """Main migration function."""
    print("🚀 Universe Migration Script")
    print("=" * 50)
    
    if migrate_universe():
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

