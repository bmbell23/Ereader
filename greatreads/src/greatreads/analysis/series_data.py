"""
Known series data - Hardcoded information about real-world book series.

This data is used to check if you're missing books from series you've started reading.
As we move toward API integration, this will become a fallback/cache.
"""

# Known universes with multiple series
KNOWN_UNIVERSES = {
    "Osten Ard": {
        "series": ["Memory, Sorrow, and Thorn", "The Last King of Osten Ard"],
        "notes": "Two series in the same universe - Last King is a sequel series set 30+ years later"
    },
    "Banished Lands": {
        "series": ["The Faithful and the Fallen", "Of Blood and Bone"],
        "notes": "Two series in the same universe - Of Blood and Bone is set 130 years after The Faithful and the Fallen"
    },
    "Malazan": {
        "series": ["Malazan Book Of The Fallen", "Kharkanas Trilogy", "Novels of the Malazan Empire", "Path to Ascendancy"],
        "notes": "Multiple series in the same universe by Steven Erikson and Ian C. Esslemont"
    }
}

# Known series information
# Format: series_name: {main_books, notes, known_books}
KNOWN_SERIES = {
    "Dungeon Crawler Carl": {
        "main_books": 7,
        "notes": "Book 8 announced but no release date yet",
        "known_books": [
            (1, "Dungeon Crawler Carl"),
            (2, "Carl's Doomsday Scenario"),
            (3, "The Dungeon Anarchist's Cookbook"),
            (4, "The Gate of the Feral Gods"),
            (5, "The Butcher's Masquerade"),
            (6, "The Eye of the Bedlam Bride"),
            (7, "The Inevitable Run"),
        ]
    },
    "Empire of the Vampire": {
        "main_books": 3,
        "notes": "Trilogy - Book 3 'Empire of the Dawn' releases November 4, 2025",
        "known_books": [
            (1, "Empire of the Vampire"),
            (2, "Empire of the Damned"),
            (3, "Empire of the Dawn"),  # Upcoming
        ]
    },
    "Malazan Book Of The Fallen": {
        "main_books": 10,
        "notes": "Complete series by Steven Erikson",
        "known_books": [
            (1, "Gardens of the Moon"),
            (2, "Deadhouse Gates"),
            (3, "Memories of Ice"),
            (4, "House of Chains"),
            (5, "Midnight Tides"),
            (6, "The Bonehunters"),
            (7, "Reaper's Gale"),
            (8, "Toll the Hounds"),
            (9, "Dust of Dreams"),
            (10, "The Crippled God"),
        ]
    },
    "The Witcher": {
        "main_books": 8,
        "notes": "Complete series (2 short story collections + 5 novels + 1 standalone)",
        "known_books": [
            (0.5, "The Last Wish"),
            (0.7, "Sword of Destiny"),
            (1, "Blood of Elves"),
            (2, "The Time of Contempt"),
            (3, "Baptism of Fire"),
            (4, "The Tower of the Swallow"),
            (5, "The Lady of the Lake"),
            (0.2, "Season of Storms"),
        ]
    },
    "The Hunger Games": {
        "main_books": 5,
        "notes": "Original trilogy + 2 prequels",
        "known_books": [
            (0, "The Ballad of Songbirds and Snakes"),
            (0.5, "Sunrise on the Reaping"),  # Announced for March 2025
            (1, "The Hunger Games"),
            (2, "Catching Fire"),
            (3, "Mockingjay"),
        ]
    },
    "Outlander": {
        "main_books": 10,
        "notes": "Main series - Book 10 'A Blessing For A Warrior Going Out' in progress",
        "known_books": [
            (1, "Outlander"),
            (2, "Dragonfly in Amber"),
            (3, "Voyager"),
            (4, "Drums of Autumn"),
            (5, "The Fiery Cross"),
            (6, "A Breath of Snow and Ashes"),
            (7, "An Echo in the Bone"),
            (8, "Written in My Own Heart's Blood"),
            (9, "Go Tell the Bees That I Am Gone"),
            (10, "A Blessing For A Warrior Going Out"),  # Upcoming, no date
        ]
    },
    "The Faithful and the Fallen": {
        "main_books": 4,
        "notes": "Complete series by John Gwynne",
        "known_books": [
            (1, "Malice"),
            (2, "Valor"),
            (3, "Ruin"),
            (4, "Wrath"),
        ]
    },
    "Of Blood and Bone": {
        "main_books": 3,
        "notes": "Complete sequel series to The Faithful and the Fallen",
        "known_books": [
            (1, "A Time of Dread"),
            (2, "A Time of Blood"),
            (3, "A Time of Courage"),
        ]
    },
    "Knockemout": {
        "main_books": 3,
        "notes": "Complete trilogy by Lucy Score",
        "known_books": [
            (1, "Things We Never Got Over"),
            (2, "Things We Hide From the Light"),
            (3, "Things We Left Behind"),
        ]
    },
    "One Dark Window": {
        "main_books": 2,
        "notes": "Duology complete by Rachel Gillig",
        "known_books": [
            (1, "One Dark Window"),
            (2, "Two Twisted Crowns"),
        ]
    },
    "The Roots of Chaos": {
        "main_books": 2,
        "notes": "Standalone books in same universe by Samantha Shannon",
        "known_books": [
            (0, "A Day of Fallen Night"),
            (1, "The Priory of the Orange Tree"),
        ]
    },
    "Memory, Sorrow, and Thorn": {
        "main_books": 4,
        "notes": "Complete series by Tad Williams (3 main books + 1 bridge novella)",
        "known_books": [
            (1, "The Dragonbone Chair"),
            (2, "Stone of Farewell"),
            (3, "To Green Angel Tower"),
            (3.5, "The Heart of What Was Lost"),  # Bridge novella
        ]
    },
    "The Last King of Osten Ard": {
        "main_books": 4,
        "notes": "Sequel series to Memory, Sorrow, and Thorn - in progress",
        "known_books": [
            (1, "The Witchwood Crown"),
            (2, "Empire of Grass"),
            (3, "Into the Narrowdark"),
            (4, "The Navigator's Children"),  # Upcoming
        ]
    },
}


def get_series_info(series_name: str) -> dict:
    """Get information about a known series."""
    return KNOWN_SERIES.get(series_name)


def get_universe_info(universe_name: str) -> dict:
    """Get information about a known universe."""
    return KNOWN_UNIVERSES.get(universe_name)


def get_all_series_names() -> list:
    """Get list of all known series names."""
    return list(KNOWN_SERIES.keys())


def get_all_universe_names() -> list:
    """Get list of all known universe names."""
    return list(KNOWN_UNIVERSES.keys())


def find_series_by_universe(universe_name: str) -> list:
    """Get all series in a given universe."""
    universe_info = KNOWN_UNIVERSES.get(universe_name)
    if universe_info:
        return universe_info['series']
    return []

