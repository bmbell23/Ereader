"""
Duplicate Detector - Find duplicate books in the database.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..models import Book, Reading

console = Console()


class DuplicateDetector:
    """Detects duplicate books in the database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_duplicates(self) -> List[Dict]:
        """
        Find duplicate books (same title, author, series, and series number).
        
        Returns:
            List of duplicate groups with details
        """
        # Group by title, author, series, and series number
        duplicates_query = self.db.query(
            Book.title,
            Book.author_name_first,
            Book.author_name_second,
            Book.series,
            Book.series_number,
            func.count(Book.id).label('count'),
            func.group_concat(Book.id).label('ids')
        ).group_by(
            Book.title,
            Book.author_name_first,
            Book.author_name_second,
            Book.series,
            Book.series_number
        ).having(
            func.count(Book.id) > 1
        ).order_by(
            Book.series,
            Book.series_number
        )
        
        results = []
        
        for row in duplicates_query.all():
            title, first, last, series, num, count, ids = row
            
            # Get full details for each duplicate
            book_ids = [int(id_str) for id_str in ids.split(',')]
            books = self.db.query(Book).filter(Book.id.in_(book_ids)).all()
            
            # Get reading information for each book
            book_details = []
            for book in books:
                readings = self.db.query(Reading).filter(Reading.book_id == book.id).all()
                
                for reading in readings:
                    book_details.append({
                        'book_id': book.id,
                        'status': 'READ' if reading.date_finished_actual else 'UNREAD',
                        'media': reading.media,
                        'date_finished': reading.date_finished_actual
                    })
                
                # If no readings, mark as unread
                if not readings:
                    book_details.append({
                        'book_id': book.id,
                        'status': 'UNREAD',
                        'media': None,
                        'date_finished': None
                    })
            
            author = f"{first or ''} {last or ''}".strip()
            series_info = f"{series} #{num}" if series and num is not None else series or "No series"
            
            results.append({
                'title': title,
                'author': author,
                'series': series_info,
                'count': count,
                'book_ids': book_ids,
                'details': book_details
            })
        
        return results
    
    def format_report(self, duplicate: Dict) -> Table:
        """Format a single duplicate group as a rich table."""
        table = Table(
            title=f"⚠️  {duplicate['title']}",
            show_header=True,
            header_style="bold yellow",
            border_style="yellow",
            title_style="bold red"
        )

        table.add_column("ID", style="dim", width=6)
        table.add_column("Status", width=10)
        table.add_column("Format", width=10)
        table.add_column("Date Finished", width=15)

        for detail in duplicate['details']:
            status_text = Text("✓ READ", style="green") if detail['status'] == 'READ' else Text("○ UNREAD", style="yellow")
            media = detail['media'] or "—"
            date_finished = str(detail['date_finished']) if detail['date_finished'] else "—"

            table.add_row(
                str(detail['book_id']),
                status_text,
                media,
                date_finished
            )

        return table

    def print_full_report(self):
        """Print a full report of all duplicates."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold yellow]DUPLICATE BOOKS CHECK[/bold yellow]\n[dim]Finding books with multiple copies[/dim]",
            border_style="yellow"
        ))
        console.print()

        duplicates = self.find_duplicates()

        if not duplicates:
            console.print(Panel(
                "[bold green]✓ No duplicate books found![/bold green]\n\nYour database is clean.",
                border_style="green"
            ))
            return

        console.print(f"[bold red]Found {len(duplicates)} sets of duplicate books:[/bold red]\n")

        for duplicate in duplicates:
            table = self.format_report(duplicate)
            console.print(f"[dim]Author:[/dim] {duplicate['author']} | [dim]Series:[/dim] {duplicate['series']}")
            console.print(table)
            console.print()

