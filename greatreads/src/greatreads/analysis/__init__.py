"""
GreatReads Series Analysis Module

This module provides tools for analyzing your book collection:
- Finding gaps in series numbering
- Detecting duplicate books
- Checking for missing books in known series
- Identifying related series in the same universe
"""

from .series_analyzer import SeriesAnalyzer
from .gap_detector import GapDetector
from .duplicate_detector import DuplicateDetector
from .known_series import KnownSeriesChecker

__all__ = [
    'SeriesAnalyzer',
    'GapDetector',
    'DuplicateDetector',
    'KnownSeriesChecker',
]

