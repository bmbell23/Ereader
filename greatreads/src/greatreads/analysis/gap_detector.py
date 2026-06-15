"""
Gap Detector - Find missing books in series based on numbering.
"""

from datetime import date
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..models import Book, Reading

console = Console()


class GapDetector:
    """Detects gaps in series numbering and unread books."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_series_with_reads(self) -> List[str]:
        """Get all series that have at least one book read."""
        results = self.db.query(Book.series).distinct()\
            .join(Reading, Book.id == Reading.book_id)\
            .filter(
                Book.series.isnot(None),
                Reading.date_finished_actual.isnot(None)
            )\
            .order_by(Book.series)\
            .all()
        
        return [row[0] for row in results]
    
    def get_series_books(self, series_name: str, include_unpublished: bool = False) -> List[Dict]:
        """Get all books in a series."""
        # First get all books in the series
        query = self.db.query(Book).filter(Book.series == series_name)

        if not include_unpublished:
            today = date.today()
            query = query.filter(
                Book.date_published.isnot(None),
                Book.date_published <= today
            )

        query = query.order_by(Book.series_number)

        books = []
        for book in query.all():
            # Check if this book has been read (any reading with finish date)
            is_read = self.db.query(Reading).filter(
                Reading.book_id == book.id,
                Reading.date_finished_actual.isnot(None)
            ).first() is not None

            books.append({
                'id': book.id,
                'title': book.title,
                'series_number': book.series_number,
                'date_published': book.date_published,
                'is_read': is_read
            })

        return books
    
    def find_gaps(self, series_name: str) -> Dict:
        """
        Find gaps in series numbering.
        
        Returns:
            {
                'series': str,
                'gaps': List[str],  # Human-readable gap descriptions
                'unread': List[Tuple[float, str]],  # (number, title)
                'books': List[Dict]  # All books in series
            }
        """
        books = self.get_series_books(series_name)
        
        if not books:
            return {
                'series': series_name,
                'gaps': [],
                'unread': [],
                'books': []
            }
        
        # Extract series numbers and create lookup
        series_numbers = []
        book_map = {}
        
        for book in books:
            if book['series_number'] is not None:
                num = book['series_number']
                series_numbers.append(num)
                book_map[num] = book
        
        if not series_numbers:
            return {
                'series': series_name,
                'gaps': [],
                'unread': [],
                'books': books
            }
        
        series_numbers.sort()
        
        # Find gaps
        gaps = []
        
        # Check if series starts at 1 (or 0)
        first_num = series_numbers[0]
        if first_num > 1:
            missing_count = int(first_num) - 1
            if missing_count == 1:
                gaps.append(f"Missing book #1 (before first book)")
            else:
                gaps.append(f"Missing books #1-{int(first_num)-1} (before first book)")
        
        # Check for gaps between books
        for i in range(len(series_numbers) - 1):
            current = series_numbers[i]
            next_num = series_numbers[i + 1]
            
            # Allow for decimal numbers (novellas), but check for integer gaps
            expected_next = int(current) + 1
            actual_next = int(next_num)
            
            if actual_next > expected_next:
                # There's a gap
                if expected_next == actual_next - 1:
                    gaps.append(f"Missing book #{expected_next}")
                else:
                    gaps.append(f"Missing books #{expected_next}-{actual_next-1}")
        
        # Find unread books
        unread = []
        for num in series_numbers:
            if num in book_map and not book_map[num]['is_read']:
                unread.append((num, book_map[num]['title']))
        
        return {
            'series': series_name,
            'gaps': gaps,
            'unread': unread,
            'books': books
        }
    
    def analyze_all_series(self) -> List[Dict]:
        """Analyze all series with reads for gaps."""
        series_list = self.get_series_with_reads()
        results = []
        
        for series_name in series_list:
            analysis = self.find_gaps(series_name)
            # Only include series with gaps or unread books
            if analysis['gaps'] or analysis['unread']:
                results.append(analysis)
        
        return results
    
    def format_report(self, analysis: Dict) -> Table:
        """Format a single series analysis as a rich table."""
        # Create table with series name as title
        table = Table(
            title=f"📚 {analysis['series']}",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta"
        )

        table.add_column("#", style="dim", width=6, justify="right")
        table.add_column("Title", style="white")
        table.add_column("In Database", width=13, justify="center")
        table.add_column("Read", width=10, justify="center")

        # Add all books
        for book in analysis['books']:
            if book['series_number'] is not None:
                num_str = f"#{book['series_number']}"

                # In Database status (all books in this list are in database)
                in_database = Text("✓ YES", style="bold cyan")

                # Read status
                if book['is_read']:
                    read_status = Text("✓ READ", style="bold green")
                else:
                    read_status = Text("○ UNREAD", style="dim yellow")

                # Check if this is a gap (shouldn't happen in current logic, but keep for safety)
                is_gap = False
                for gap in analysis['gaps']:
                    if f"#{book['series_number']}" in gap:
                        is_gap = True
                        break

                # Style the row
                if is_gap:
                    table.add_row(
                        Text(num_str, style="bold red"),
                        Text(book['title'], style="red"),
                        Text("⚠ GAP", style="bold red"),
                        Text("—", style="dim")
                    )
                else:
                    table.add_row(num_str, book['title'], in_database, read_status)

        return table
    
    def print_full_report(self):
        """Print a full report of all series with gaps."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]SERIES GAP ANALYSIS[/bold cyan]\n[dim]Finding missing books and unread titles[/dim]",
            border_style="cyan"
        ))
        console.print()

        results = self.analyze_all_series()

        if not results:
            console.print(Panel(
                "[bold green]✓ No gaps found![/bold green]\n\nAll your series appear complete with no unread books.",
                border_style="green"
            ))
            return

        # Print each series table
        for analysis in results:
            table = self.format_report(analysis)
            console.print(table)
            console.print()

        # Summary
        total_series = len(self.get_series_with_reads())
        total_gaps = sum(len(r['gaps']) for r in results)
        total_unread = sum(len(r['unread']) for r in results)

        summary_text = f"""[bold]Total series analyzed:[/bold] {total_series}
[bold]Series with gaps or unread books:[/bold] {len(results)}
[bold]Total potential gaps:[/bold] {total_gaps}
[bold]Total unread books:[/bold] {total_unread}"""

        console.print(Panel(summary_text, title="[bold]Summary[/bold]", border_style="blue"))
        console.print()

