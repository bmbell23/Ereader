"""Reading reports API routes."""

from typing import Optional, Dict, Any, List
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract

from ..database import get_db
from ..models.reading import Reading
from ..models.book import Book

router = APIRouter()


@router.get("/")
async def get_reading_report(
    year: int = Query(..., description="Year for the report"),
    month: Optional[int] = Query(None, description="Optional month (1-12) for the report"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get reading report data for a specific time period."""

    # Base query for finished readings with eager loading of book relationship
    query = db.query(Reading).options(joinedload(Reading.book)).filter(
        Reading.date_finished_actual.isnot(None)
    )

    # Apply year filter
    query = query.filter(extract('year', Reading.date_finished_actual) == year)

    # Apply month filter if specified
    if month:
        query = query.filter(extract('month', Reading.date_finished_actual) == month)

    # Get all finished readings for this period, ordered by finish date
    readings = query.order_by(Reading.date_finished_actual).all()

    # Build book list with details
    books = []
    books_by_month = {}  # For annual reports, group by month
    total_words = 0
    total_pages = 0
    media_counts = {"Audio": 0, "Ebook": 0, "Physical": 0}
    media_words = {"Audio": 0, "Ebook": 0, "Physical": 0}

    # For chart data - now tracking media format breakdown
    author_counts = {}  # {author: {Audio: 0, Ebook: 0, Physical: 0}}
    decade_counts = {}  # {decade: {Audio: 0, Ebook: 0, Physical: 0}}
    month_counts = {  # {month_num: {Audio: 0, Ebook: 0, Physical: 0}}
        1: {"Audio": 0, "Ebook": 0, "Physical": 0},
        2: {"Audio": 0, "Ebook": 0, "Physical": 0},
        3: {"Audio": 0, "Ebook": 0, "Physical": 0},
        4: {"Audio": 0, "Ebook": 0, "Physical": 0},
        5: {"Audio": 0, "Ebook": 0, "Physical": 0},
        6: {"Audio": 0, "Ebook": 0, "Physical": 0},
        7: {"Audio": 0, "Ebook": 0, "Physical": 0},
        8: {"Audio": 0, "Ebook": 0, "Physical": 0},
        9: {"Audio": 0, "Ebook": 0, "Physical": 0},
        10: {"Audio": 0, "Ebook": 0, "Physical": 0},
        11: {"Audio": 0, "Ebook": 0, "Physical": 0},
        12: {"Audio": 0, "Ebook": 0, "Physical": 0}
    }
    word_count_ranges = {
        "300k+": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "200-300k": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "100-200k": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "50-100k": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "<50k": {"Audio": 0, "Ebook": 0, "Physical": 0}
    }
    days_after_pub_ranges = {
        "<1 year": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "1-5 years": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "5-20 years": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "20-40 years": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "40+ years": {"Audio": 0, "Ebook": 0, "Physical": 0}
    }
    days_to_finish_ranges = {
        "1-3": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "4-7": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "8-14": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "15-30": {"Audio": 0, "Ebook": 0, "Physical": 0},
        "31+": {"Audio": 0, "Ebook": 0, "Physical": 0}
    }

    for reading in readings:
        if reading.book:
            book_data = {
                "id": reading.book.id,
                "title": reading.book.title,
                "author": reading.book.author,
                "word_count": reading.book.word_count or 0,
                "page_count": reading.book.page_count or 0,
                "cover": reading.book.cover,
                "media": reading.media,
                "date_finished": reading.date_finished_actual.isoformat() if reading.date_finished_actual else None,
                "series": reading.book.series,
                "series_number": reading.book.series_number,
                "genre": reading.book.genre,
                "year_published": reading.book.year_published,
                "author_gender": reading.book.author_gender
            }
            books.append(book_data)

            # Group by month for annual reports
            if not month and reading.date_finished_actual:
                month_num = reading.date_finished_actual.month
                if month_num not in books_by_month:
                    books_by_month[month_num] = {
                        "books": [],
                        "total_entries": 0,
                        "total_words": 0
                    }
                books_by_month[month_num]["books"].append(book_data)
                books_by_month[month_num]["total_entries"] += 1
                if reading.book.word_count:
                    books_by_month[month_num]["total_words"] += reading.book.word_count

            # Update totals
            if reading.book.word_count:
                total_words += reading.book.word_count
            if reading.book.page_count:
                total_pages += reading.book.page_count

            # Normalize media format for tracking
            media_format = None
            if reading.media:
                media_normalized = reading.media.lower()
                if media_normalized in ['audio', 'audiobook']:
                    media_format = "Audio"
                    media_counts["Audio"] += 1
                    if reading.book.word_count:
                        media_words["Audio"] += reading.book.word_count
                elif media_normalized in ['kindle', 'ebook']:
                    media_format = "Ebook"
                    media_counts["Ebook"] += 1
                    if reading.book.word_count:
                        media_words["Ebook"] += reading.book.word_count
                elif media_normalized in ['physical', 'hardcover', 'paperback']:
                    media_format = "Physical"
                    media_counts["Physical"] += 1
                    if reading.book.word_count:
                        media_words["Physical"] += reading.book.word_count

            # Chart data: Author counts (with media breakdown)
            if reading.book.author and media_format:
                if reading.book.author not in author_counts:
                    author_counts[reading.book.author] = {"Audio": 0, "Ebook": 0, "Physical": 0}
                author_counts[reading.book.author][media_format] += 1

            # Chart data: Decade published (with media breakdown)
            if reading.book.year_published and media_format:
                decade = (reading.book.year_published // 10) * 10
                decade_label = f"{decade}s"
                if decade_label not in decade_counts:
                    decade_counts[decade_label] = {"Audio": 0, "Ebook": 0, "Physical": 0}
                decade_counts[decade_label][media_format] += 1

            # Chart data: Month finished (with media breakdown)
            if reading.date_finished_actual and media_format:
                month_num = reading.date_finished_actual.month
                month_counts[month_num][media_format] += 1

            # Chart data: Word count distribution (with media breakdown)
            if reading.book.word_count and media_format:
                wc = reading.book.word_count
                if wc >= 300000:
                    word_count_ranges["300k+"][media_format] += 1
                elif wc >= 200000:
                    word_count_ranges["200-300k"][media_format] += 1
                elif wc >= 100000:
                    word_count_ranges["100-200k"][media_format] += 1
                elif wc >= 50000:
                    word_count_ranges["50-100k"][media_format] += 1
                else:
                    word_count_ranges["<50k"][media_format] += 1

            # Chart data: Days after publication (with media breakdown)
            if reading.book.date_published and reading.date_finished_actual and media_format:
                days_diff = (reading.date_finished_actual - reading.book.date_published).days
                years_diff = days_diff / 365.25
                if years_diff < 1:
                    days_after_pub_ranges["<1 year"][media_format] += 1
                elif years_diff < 5:
                    days_after_pub_ranges["1-5 years"][media_format] += 1
                elif years_diff < 20:
                    days_after_pub_ranges["5-20 years"][media_format] += 1
                elif years_diff < 40:
                    days_after_pub_ranges["20-40 years"][media_format] += 1
                else:
                    days_after_pub_ranges["40+ years"][media_format] += 1

            # Chart data: Days to finish (with media breakdown)
            if reading.date_started and reading.date_finished_actual and media_format:
                days_to_finish = (reading.date_finished_actual - reading.date_started).days
                if days_to_finish <= 3:
                    days_to_finish_ranges["1-3"][media_format] += 1
                elif days_to_finish <= 7:
                    days_to_finish_ranges["4-7"][media_format] += 1
                elif days_to_finish <= 14:
                    days_to_finish_ranges["8-14"][media_format] += 1
                elif days_to_finish <= 30:
                    days_to_finish_ranges["15-30"][media_format] += 1
                else:
                    days_to_finish_ranges["31+"][media_format] += 1

    # Calculate period label
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    if month:
        period_label = f"{month_names[month - 1]} {year}"
    else:
        period_label = str(year)

    # Sort author counts and get top 5 (by total count)
    sorted_authors = sorted(
        author_counts.items(),
        key=lambda x: x[1]["Audio"] + x[1]["Ebook"] + x[1]["Physical"],
        reverse=True
    )[:5]
    top_authors = [{"author": author, "formats": formats} for author, formats in sorted_authors]

    # Sort decades chronologically
    sorted_decades = sorted(
        [(decade, formats) for decade, formats in decade_counts.items()
         if formats["Audio"] + formats["Ebook"] + formats["Physical"] > 0],
        key=lambda x: int(x[0].replace('s', ''))
    )
    decade_data = [{"decade": decade, "formats": formats} for decade, formats in sorted_decades]

    # Format month data with labels
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_data = [{"month": month_labels[i], "formats": month_counts[i+1]} for i in range(12)]

    return {
        "period": period_label,
        "year": year,
        "month": month,
        "total_books": len(books),
        "total_words": total_words,
        "total_pages": total_pages,
        "media_counts": media_counts,
        "media_words": media_words,
        "books": books,
        "books_by_month": books_by_month if not month else {},
        "charts": {
            "top_authors": top_authors,
            "decades": decade_data,
            "months": month_data,
            "word_count_ranges": word_count_ranges,
            "days_after_pub": days_after_pub_ranges,
            "days_to_finish": days_to_finish_ranges
        }
    }


@router.get("/available-periods")
async def get_available_periods(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get available years and months that have reading data."""

    # Get all finished readings
    all_readings = db.query(Reading).filter(
        Reading.date_finished_actual.isnot(None)
    ).all()

    # Extract unique years
    years = sorted(
        set(
            r.date_finished_actual.year
            for r in all_readings
            if r.date_finished_actual
        ),
        reverse=True
    )

    # Extract months per year
    months_by_year = {}
    for reading in all_readings:
        if reading.date_finished_actual:
            year = reading.date_finished_actual.year
            month = reading.date_finished_actual.month
            if year not in months_by_year:
                months_by_year[year] = set()
            months_by_year[year].add(month)

    # Convert sets to sorted lists
    for year in months_by_year:
        months_by_year[year] = sorted(list(months_by_year[year]))

    return {
        "years": years,
        "months_by_year": months_by_year
    }

