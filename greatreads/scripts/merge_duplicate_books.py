#!/usr/bin/env python3
"""
Merge duplicate books in GreatReads database.

This script safely merges duplicate book entries by:
1. Consolidating all readings, inventory, and external imports to the primary book
2. Merging inventory flags (owned_audio, owned_ebook, owned_physical)
3. Updating reading records to point to the primary book
4. Removing the duplicate book entries
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.greatreads.database import get_db_session
from src.greatreads.models import Book, Reading, Inventory, ExternalImport


def merge_books(db: Session, primary_id: int, duplicate_ids: List[int], dry_run: bool = True):
    """
    Merge duplicate books into a primary book.
    
    Args:
        db: Database session
        primary_id: ID of the book to keep
        duplicate_ids: IDs of duplicate books to merge
        dry_run: If True, only show what would happen
    """
    print(f"\n{'='*80}")
    print(f"Merging books: {duplicate_ids} -> {primary_id}")
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL MERGE'}")
    print(f"{'='*80}\n")
    
    # Get primary book
    primary_book = db.query(Book).filter_by(id=primary_id).first()
    if not primary_book:
        raise ValueError(f"Primary book {primary_id} not found")
    
    print(f"Primary Book: {primary_book.title} by {primary_book.author}")
    
    # Get all duplicate books
    duplicate_books = db.query(Book).filter(Book.id.in_(duplicate_ids)).all()
    if len(duplicate_books) != len(duplicate_ids):
        found_ids = {b.id for b in duplicate_books}
        missing = set(duplicate_ids) - found_ids
        raise ValueError(f"Some duplicate books not found: {missing}")
    
    for dup in duplicate_books:
        print(f"  Duplicate: {dup.title} by {dup.author} (ID: {dup.id})")
    
    # 1. Merge Inventory
    print("\n--- Inventory ---")
    primary_inv = db.query(Inventory).filter_by(book_id=primary_id).first()
    if not primary_inv:
        primary_inv = Inventory(book_id=primary_id)
        db.add(primary_inv)
        print(f"Created new inventory for primary book {primary_id}")
    
    print(f"Primary inventory: Audio={primary_inv.owned_audio}, Ebook={primary_inv.owned_ebook}, Physical={primary_inv.owned_physical}")
    
    for dup_id in duplicate_ids:
        dup_inv = db.query(Inventory).filter_by(book_id=dup_id).first()
        if dup_inv:
            print(f"  Duplicate {dup_id} inventory: Audio={dup_inv.owned_audio}, Ebook={dup_inv.owned_ebook}, Physical={dup_inv.owned_physical}")
            
            # Merge ownership flags (OR operation)
            primary_inv.owned_audio = primary_inv.owned_audio or dup_inv.owned_audio
            primary_inv.owned_ebook = primary_inv.owned_ebook or dup_inv.owned_ebook
            primary_inv.owned_physical = primary_inv.owned_physical or dup_inv.owned_physical
            
            # Preserve ISBNs if primary doesn't have them
            if not primary_inv.isbn_10 and dup_inv.isbn_10:
                primary_inv.isbn_10 = dup_inv.isbn_10
            if not primary_inv.isbn_13 and dup_inv.isbn_13:
                primary_inv.isbn_13 = dup_inv.isbn_13
            
            if not dry_run:
                db.delete(dup_inv)
                print(f"    Deleted duplicate inventory {dup_inv.id}")
    
    print(f"Merged inventory: Audio={primary_inv.owned_audio}, Ebook={primary_inv.owned_ebook}, Physical={primary_inv.owned_physical}")
    
    # 2. Move External Imports
    print("\n--- External Imports ---")
    for dup_id in duplicate_ids:
        ext_imports = db.query(ExternalImport).filter_by(book_id=dup_id).all()
        for ext_imp in ext_imports:
            print(f"  Moving {ext_imp.source} import (external_id={ext_imp.external_id}) from book {dup_id} to {primary_id}")
            if not dry_run:
                ext_imp.book_id = primary_id
    
    # 3. Move Readings
    print("\n--- Readings ---")
    for dup_id in duplicate_ids:
        readings = db.query(Reading).filter_by(book_id=dup_id).all()
        for reading in readings:
            media = reading.media or "Unknown"
            status = "Finished" if reading.date_finished_actual else "In Progress"
            print(f"  Moving reading (ID={reading.id}, media={media}, status={status}) from book {dup_id} to {primary_id}")
            if not dry_run:
                reading.book_id = primary_id
    
    # 4. Delete duplicate books
    print("\n--- Deleting Duplicates ---")
    for dup in duplicate_books:
        print(f"  Deleting book {dup.id}: {dup.title}")
        if not dry_run:
            db.delete(dup)
    
    if not dry_run:
        db.commit()
        print("\n✅ Merge completed successfully!")
    else:
        print("\n🔍 DRY RUN - No changes made")
    
    print(f"{'='*80}\n")


def main():
    """Main function to merge ASOIAF duplicates."""
    # Define the merges needed
    merges = [
        {
            "primary_id": 127,  # A Storm of Swords (has readings and ABS link)
            "duplicate_ids": [1593],  # A Storm of Swords: Book Three (has Calibre link)
            "title": "A Storm of Swords"
        },
        {
            "primary_id": 130,  # A Feast for Crows (has readings and ABS link)
            "duplicate_ids": [1595],  # A Feast for Crows: Book Four (has Calibre link)
            "title": "A Feast for Crows"
        },
        {
            "primary_id": 132,  # A Dance with Dragons (has readings and ABS link)
            "duplicate_ids": [1594],  # A Dance with Dragons: Book Five (has Calibre link)
            "title": "A Dance with Dragons"
        }
    ]
    
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - Use --execute to actually perform the merge")
        print("="*80 + "\n")
    
    with get_db_session() as db:
        for merge_config in merges:
            merge_books(
                db=db,
                primary_id=merge_config["primary_id"],
                duplicate_ids=merge_config["duplicate_ids"],
                dry_run=dry_run
            )
    
    if dry_run:
        print("\n" + "="*80)
        print("To execute the merge, run: python scripts/merge_duplicate_books.py --execute")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()
