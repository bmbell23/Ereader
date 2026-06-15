"""
Series Analyzer - Main interface for all series analysis functionality.
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from rich.console import Console
from rich.panel import Panel

from .gap_detector import GapDetector
from .duplicate_detector import DuplicateDetector
from .known_series import KnownSeriesChecker

console = Console()


class SeriesAnalyzer:
    """
    Main interface for analyzing book series.
    
    Provides a unified API for:
    - Finding gaps in series numbering
    - Detecting duplicate books
    - Checking for missing books in known series
    - Identifying related series in the same universe
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.gap_detector = GapDetector(db)
        self.duplicate_detector = DuplicateDetector(db)
        self.known_series_checker = KnownSeriesChecker(db)
    
    def analyze_gaps(self) -> List[Dict]:
        """
        Find gaps in series numbering.
        
        Returns:
            List of series with gaps or unread books
        """
        return self.gap_detector.analyze_all_series()
    
    def analyze_duplicates(self) -> List[Dict]:
        """
        Find duplicate books in the database.
        
        Returns:
            List of duplicate book groups
        """
        return self.duplicate_detector.find_duplicates()
    
    def analyze_known_series(self) -> List[Dict]:
        """
        Check for missing books in series with known book lists.
        
        Returns:
            List of series with missing books
        """
        return self.known_series_checker.check_all_known_series()
    
    def analyze_related_series(self) -> List[Dict]:
        """
        Check for related series in the same universe.
        
        Returns:
            List of universes with missing series
        """
        return self.known_series_checker.check_related_series()
    
    def full_analysis(self) -> Dict:
        """
        Run all analysis types and return comprehensive results.
        
        Returns:
            {
                'gaps': List[Dict],
                'duplicates': List[Dict],
                'known_series': List[Dict],
                'related_series': List[Dict],
                'summary': Dict
            }
        """
        gaps = self.analyze_gaps()
        duplicates = self.analyze_duplicates()
        known_series = self.analyze_known_series()
        related_series = self.analyze_related_series()
        
        summary = {
            'total_series_with_gaps': len(gaps),
            'total_gaps_found': sum(len(g['gaps']) for g in gaps),
            'total_unread_books': sum(len(g['unread']) for g in gaps),
            'total_duplicate_groups': len(duplicates),
            'total_known_series_missing': len(known_series),
            'total_missing_books': sum(len(k['missing']) for k in known_series),
            'total_related_series_missing': sum(len(r['missing_series']) for r in related_series),
        }
        
        return {
            'gaps': gaps,
            'duplicates': duplicates,
            'known_series': known_series,
            'related_series': related_series,
            'summary': summary
        }
    
    def print_full_report(self):
        """Print a comprehensive report of all analysis types."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]GREATREADS SERIES ANALYSIS[/bold cyan]\n[dim]Complete analysis of your book collection[/dim]",
            border_style="cyan"
        ))

        # Just call each individual report method
        self.gap_detector.print_full_report()
        self.duplicate_detector.print_full_report()
        self.known_series_checker.print_full_report()

        # Print overall summary
        analysis = self.full_analysis()
        summary = analysis['summary']

        summary_text = f"""[bold]Series with gaps or unread books:[/bold] {summary['total_series_with_gaps']}
[bold]Total gaps found:[/bold] {summary['total_gaps_found']}
[bold]Total unread books:[/bold] {summary['total_unread_books']}
[bold]Duplicate book groups:[/bold] {summary['total_duplicate_groups']}
[bold]Known series with missing books:[/bold] {summary['total_known_series_missing']}
[bold]Total missing books from known series:[/bold] {summary['total_missing_books']}
[bold]Related series you might be missing:[/bold] {summary['total_related_series_missing']}"""

        console.print(Panel(summary_text, title="[bold]Overall Summary[/bold]", border_style="green"))
        console.print()

