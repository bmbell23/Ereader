"""
Known Series Checker - Check for missing books in series with known book lists.
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..models import Book, Reading
from .series_data import KNOWN_SERIES, KNOWN_UNIVERSES

console = Console()


class KnownSeriesChecker:
    """Checks for missing books in series with known book lists."""
    
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
    
    def check_series(self, series_name: str) -> Dict:
        """
        Check a specific series against known book list.
        
        Returns:
            {
                'series': str,
                'info': dict,  # From KNOWN_SERIES
                'missing': List[Tuple[float, str]],  # (number, title)
                'have': Dict[float, str]  # {number: title}
            }
        """
        if series_name not in KNOWN_SERIES:
            return None
        
        series_info = KNOWN_SERIES[series_name]
        
        # Get all books in this series from database
        books = self.db.query(Book.title, Book.series_number)\
            .filter(Book.series == series_name)\
            .order_by(Book.series_number)\
            .all()
        
        db_books = {num: title for title, num in books if num is not None}
        
        # Check for missing books
        missing = []
        for num, title in series_info["known_books"]:
            if num not in db_books:
                missing.append((num, title))
        
        return {
            'series': series_name,
            'info': series_info,
            'missing': missing,
            'have': db_books
        }
    
    def check_all_known_series(self) -> List[Dict]:
        """Check all read series that have known book lists."""
        series_with_reads = self.get_series_with_reads()
        results = []
        
        for series_name in series_with_reads:
            if series_name in KNOWN_SERIES:
                check = self.check_series(series_name)
                if check and check['missing']:
                    results.append(check)
        
        return results
    
    def get_universes_with_reads(self) -> Dict[str, List[str]]:
        """
        Get all universes where user has read at least one series.
        
        Returns:
            {universe_name: [series_names_read]}
        """
        results = {}
        
        for universe_name, universe_info in KNOWN_UNIVERSES.items():
            # Check if user has read any series in this universe
            user_series = self.db.query(Book.series).distinct()\
                .join(Reading, Book.id == Reading.book_id)\
                .filter(
                    Book.universe == universe_name,
                    Book.series.isnot(None),
                    Reading.date_finished_actual.isnot(None)
                )\
                .all()
            
            user_series_list = [row[0] for row in user_series]
            
            if user_series_list:
                results[universe_name] = user_series_list
        
        return results
    
    def check_related_series(self) -> List[Dict]:
        """
        Check for related series in the same universe that user might be missing.
        
        Returns:
            List of universes with missing series
        """
        results = []
        universes_with_reads = self.get_universes_with_reads()
        
        for universe_name, user_series in universes_with_reads.items():
            universe_info = KNOWN_UNIVERSES[universe_name]
            
            # Check for missing series in this universe
            missing_series = [s for s in universe_info["series"] if s not in user_series]
            
            if missing_series:
                results.append({
                    'universe': universe_name,
                    'info': universe_info,
                    'read_series': user_series,
                    'missing_series': missing_series
                })
        
        return results
    
    def format_series_report(self, check: Dict) -> Table:
        """Format a single series check as a rich table."""
        # Combine all books (have + missing)
        all_books = {}
        for num, title in check['have'].items():
            all_books[num] = {'title': title, 'have': True}
        for num, title in check['missing']:
            all_books[num] = {'title': title, 'have': False}

        table = Table(
            title=f"📚 {check['series']}",
            caption=f"[dim]{check['info']['notes']}[/dim]",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta"
        )

        table.add_column("#", style="dim", width=6, justify="right")
        table.add_column("Title", style="white")
        table.add_column("Status", width=12, justify="center")

        for num in sorted(all_books.keys()):
            book = all_books[num]
            num_str = f"#{num}"

            if book['have']:
                status = Text("✓ HAVE", style="bold green")
            else:
                status = Text("⚠ MISSING", style="bold red")

            table.add_row(num_str, book['title'], status)

        return table
    
    def format_universe_report(self, check: Dict) -> Panel:
        """Format a universe check as a readable panel."""
        content_lines = []
        content_lines.append(f"[dim]{check['info']['notes']}[/dim]\n")
        content_lines.append("[bold green]✓ Series you've read:[/bold green]")
        for series in check['read_series']:
            content_lines.append(f"  • {series}")
        content_lines.append("")
        content_lines.append("[bold yellow]📚 Related series you might be missing:[/bold yellow]")
        for series in check['missing_series']:
            content_lines.append(f"  • {series}")

        return Panel(
            "\n".join(content_lines),
            title=f"[bold]🌍 {check['universe']}[/bold]",
            border_style="magenta"
        )
    
    def print_full_report(self):
        """Print a full report of missing books and related series."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]KNOWN SERIES CHECK[/bold cyan]\n[dim]Checking against documented book lists[/dim]",
            border_style="cyan"
        ))
        console.print()

        series_results = self.check_all_known_series()

        if series_results:
            for check in series_results:
                table = self.format_series_report(check)
                console.print(table)
                console.print()
        else:
            console.print(Panel(
                "[bold green]✓ No missing books found![/bold green]\n\nAll known series appear complete.",
                border_style="green"
            ))
            console.print()

        # Check for related series
        console.print(Panel.fit(
            "[bold magenta]RELATED SERIES CHECK[/bold magenta]\n[dim]Finding series in the same universe[/dim]",
            border_style="magenta"
        ))
        console.print()

        universe_results = self.check_related_series()

        if universe_results:
            for check in universe_results:
                panel = self.format_universe_report(check)
                console.print(panel)
                console.print()
        else:
            console.print(Panel(
                "[bold green]✓ No related series found![/bold green]\n\nNo additional series in universes you've read.",
                border_style="green"
            ))
            console.print()

