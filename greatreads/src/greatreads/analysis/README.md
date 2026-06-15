# GreatReads Series Analysis Module

A comprehensive toolkit for analyzing your book collection to find missing books, gaps in series, duplicates, and related series you might want to read.

## Features

### 1. Gap Detection
Finds missing books in series based on numbering:
- Detects gaps in series numbering (e.g., you have #1, #2, #4 but missing #3)
- Identifies unread books in your library
- Only checks published books (filters by publication date)
- Handles decimal numbers for novellas (e.g., 3.5)

### 2. Duplicate Detection
Finds duplicate books in your database:
- Identifies books with same title, author, series, and series number
- Shows read status and media format for each duplicate
- Useful for finding books you own in multiple formats

### 3. Known Series Checking
Checks against hardcoded knowledge of real-world series:
- Currently knows about ~15 series (Dungeon Crawler Carl, Malazan, Witcher, etc.)
- Checks if you're missing books from these known series
- Can be extended with more series data

### 4. Universe Relationship Tracking
Identifies related series in the same universe:
- Finds sequel series or companion series you might be missing
- Currently tracks: Osten Ard, Banished Lands, Malazan universes
- Helps discover related books you didn't know existed

## Usage

### Command Line

Run the unified analysis script:

```bash
# Full analysis (all checks)
python analyze_series.py

# Individual checks
python analyze_series.py --gaps          # Only gap detection
python analyze_series.py --duplicates    # Only duplicate detection
python analyze_series.py --known         # Only known series check
python analyze_series.py --related       # Only related series check

# JSON output (for programmatic use)
python analyze_series.py --json
python analyze_series.py --known --json
```

### Python API

Use the module programmatically:

```python
from greatreads.database import get_db_session
from greatreads.analysis import SeriesAnalyzer

with get_db_session() as db:
    analyzer = SeriesAnalyzer(db)
    
    # Run full analysis
    results = analyzer.full_analysis()
    
    # Or run individual analyses
    gaps = analyzer.analyze_gaps()
    duplicates = analyzer.analyze_duplicates()
    known_series = analyzer.analyze_known_series()
    related_series = analyzer.analyze_related_series()
    
    # Print formatted report
    analyzer.print_full_report()
```

### Individual Components

You can also use the individual detectors directly:

```python
from greatreads.database import get_db_session
from greatreads.analysis import GapDetector, DuplicateDetector, KnownSeriesChecker

with get_db_session() as db:
    # Gap detection
    gap_detector = GapDetector(db)
    series_gaps = gap_detector.find_gaps("Malazan Book Of The Fallen")
    gap_detector.print_full_report()
    
    # Duplicate detection
    dup_detector = DuplicateDetector(db)
    duplicates = dup_detector.find_duplicates()
    dup_detector.print_full_report()
    
    # Known series checking
    known_checker = KnownSeriesChecker(db)
    missing = known_checker.check_series("The Witcher")
    known_checker.print_full_report()
```

## Module Structure

```
src/greatreads/analysis/
├── __init__.py              # Module exports
├── series_analyzer.py       # Main unified interface
├── gap_detector.py          # Gap detection logic
├── duplicate_detector.py    # Duplicate detection logic
├── known_series.py          # Known series checking
├── series_data.py           # Hardcoded series information
└── README.md                # This file
```

## Adding New Series

To add a new series to the known series database, edit `series_data.py`:

```python
KNOWN_SERIES = {
    # ... existing series ...
    
    "Your New Series": {
        "main_books": 5,
        "notes": "Complete series by Author Name",
        "known_books": [
            (1, "Book One Title"),
            (2, "Book Two Title"),
            (3, "Book Three Title"),
            (4, "Book Four Title"),
            (5, "Book Five Title"),
        ]
    },
}
```

To add a new universe with multiple series:

```python
KNOWN_UNIVERSES = {
    # ... existing universes ...
    
    "Your Universe Name": {
        "series": ["Series One", "Series Two", "Series Three"],
        "notes": "Description of how the series are related"
    },
}
```

## Data Structures

### Gap Analysis Result
```python
{
    'series': str,                      # Series name
    'gaps': List[str],                  # Human-readable gap descriptions
    'unread': List[Tuple[float, str]],  # (number, title) of unread books
    'books': List[Dict]                 # All books in series
}
```

### Duplicate Detection Result
```python
{
    'title': str,           # Book title
    'author': str,          # Author name
    'series': str,          # Series info
    'count': int,           # Number of duplicates
    'book_ids': List[int],  # IDs of duplicate books
    'details': List[Dict]   # Read status and media for each
}
```

### Known Series Check Result
```python
{
    'series': str,                      # Series name
    'info': dict,                       # Series metadata
    'missing': List[Tuple[float, str]], # (number, title) of missing books
    'have': Dict[float, str]            # {number: title} of books you have
}
```

### Related Series Result
```python
{
    'universe': str,            # Universe name
    'info': dict,               # Universe metadata
    'read_series': List[str],   # Series you've read
    'missing_series': List[str] # Related series you haven't read
}
```

## Future Enhancements

See `SERIES_ANALYSIS_SUMMARY.md` in the project root for:
- Roadmap for API integration
- Plans for follow/notification system
- Multi-user considerations
- Database schema proposals

## Notes

- Gap detection only checks for numbering gaps, not real-world missing books
- Known series data must be manually updated (for now)
- Duplicate detection considers same book in different formats as duplicates
- All analyses only consider published books (filters by publication date)

