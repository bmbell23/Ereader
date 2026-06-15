"""Settings service for retrieving user settings."""

import json
import math
from datetime import date
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ..models.user_settings import UserSettings

# Default reading speeds (words per day) by media type
DEFAULT_READING_SPEEDS = {
    "ebook": 15000,
    "physical": 12000,
    "hardcover": 12000,
    "audio": 25000,
    "audiobook": 25000,
}
DEFAULT_WPD = 12000

# Exponential decay rate per month for recency weighting.
# At 0.5/month: weight after 1mo ≈ 61%, 3mo ≈ 22%, 6mo ≈ 5%, 12mo ≈ 0.2%.
# Books from the last 1-3 months dominate; 6+ months contribute very little.
_DECAY_RATE_PER_MONTH = 0.5


def get_wpd_mode(db: Session) -> str:
    """Return current WPD calculation mode: 'manual' or 'auto'."""
    setting = db.query(UserSettings).filter(
        UserSettings.setting_key == "wpd_mode"
    ).first()
    return setting.setting_value if setting else "manual"


def calculate_auto_wpd(db: Session) -> Dict[str, Optional[int]]:
    """Calculate auto WPD for each format based on historical readings.

    Uses exponential recency weighting: more recent finished books
    contribute more to the estimate than older ones.

    Returns a dict with keys 'ebook', 'physical', 'audio' mapping to
    the weighted-average WPD (or None if no data for that format).
    """
    # Avoid circular import – Reading imports settings_service at method level
    from ..models.reading import Reading

    today = date.today()

    finished = db.query(Reading).filter(
        Reading.date_finished_actual.isnot(None),
        Reading.date_started.isnot(None),
    ).all()

    # Accumulate (wpd, weight) pairs per canonical format
    buckets: Dict[str, list] = {"ebook": [], "physical": [], "audio": []}

    for r in finished:
        if not r.book or not r.book.word_count:
            continue

        days_elapsed = (r.date_finished_actual - r.date_started).days + 1
        if days_elapsed <= 0:
            continue

        actual_wpd = r.book.word_count / days_elapsed

        months_ago = (today - r.date_finished_actual).days / 30.0
        weight = math.exp(-_DECAY_RATE_PER_MONTH * months_ago)

        media = (r.media or "").lower()
        if media in ("ebook", "kindle"):
            buckets["ebook"].append((actual_wpd, weight))
        elif media in ("physical", "hardcover", "paperback"):
            buckets["physical"].append((actual_wpd, weight))
        elif media in ("audio", "audiobook"):
            buckets["audio"].append((actual_wpd, weight))

    result: Dict[str, Optional[int]] = {}
    for fmt, points in buckets.items():
        if not points:
            result[fmt] = None
        else:
            total_w = sum(w for _, w in points)
            weighted_wpd = sum(wpd * w for wpd, w in points) / total_w
            result[fmt] = round(weighted_wpd)

    return result


def _get_manual_speeds(db: Session) -> Dict[str, int]:
    """Return manually configured reading speeds (or defaults)."""
    setting = db.query(UserSettings).filter(
        UserSettings.setting_key == "reading_speeds"
    ).first()

    if setting:
        try:
            speeds = json.loads(setting.setting_value)
            return {
                "ebook": speeds.get("ebook_wpd", DEFAULT_READING_SPEEDS["ebook"]),
                "physical": speeds.get("physical_wpd", DEFAULT_READING_SPEEDS["physical"]),
                "hardcover": speeds.get("physical_wpd", DEFAULT_READING_SPEEDS["hardcover"]),
                "audio": speeds.get("audio_wpd", DEFAULT_READING_SPEEDS["audio"]),
                "audiobook": speeds.get("audio_wpd", DEFAULT_READING_SPEEDS["audiobook"]),
            }
        except (json.JSONDecodeError, KeyError):
            pass

    return dict(DEFAULT_READING_SPEEDS)


def get_reading_speeds(db: Session) -> Dict[str, int]:
    """Get reading speeds (WPD) respecting the current wpd_mode setting.

    In 'auto' mode the weighted historical average is used, falling back
    to manual/default values for formats that have no historical data.
    In 'manual' mode the user-configured (or default) values are used.
    """
    mode = get_wpd_mode(db)

    if mode == "auto":
        auto = calculate_auto_wpd(db)
        manual = _get_manual_speeds(db)
        ebook_wpd = auto.get("ebook") or manual["ebook"]
        physical_wpd = auto.get("physical") or manual["physical"]
        audio_wpd = auto.get("audio") or manual["audio"]
        return {
            "ebook": ebook_wpd,
            "physical": physical_wpd,
            "hardcover": physical_wpd,
            "audio": audio_wpd,
            "audiobook": audio_wpd,
        }

    return _get_manual_speeds(db)


def get_wpd_for_media(db: Session, media_type: str) -> int:
    """Get words per day for a specific media type."""
    speeds = get_reading_speeds(db)
    return speeds.get(media_type.lower(), DEFAULT_WPD)

