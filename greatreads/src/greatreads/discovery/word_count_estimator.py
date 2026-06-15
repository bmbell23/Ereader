"""
Word count estimation for books using multiple sources and strategies.
"""
import os
import re
import json
from typing import Dict, Optional, List
from pathlib import Path
import requests
from bs4 import BeautifulSoup


class WordCountEstimator:
    """Estimates word counts for books using multiple strategies."""

    def __init__(self, cache_file: str = 'word_count_cache.json', db_session=None):
        """Initialize the estimator with optional cache file and database session."""
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self.session = requests.Session()
        self.db = db_session

        # Training data from database
        self.author_wpp = {}  # Words per page by author
        self.genre_wpp = {}   # Words per page by genre
        self.global_wpp = 300  # Default global average

        # Train on database if available
        if self.db:
            self._train_on_database()

        # Initialize Gemini API key
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    def _load_cache(self) -> Dict:
        """Load cached word counts from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _get_cache_key(self, isbn: Optional[str], title: str, author: str) -> str:
        """Generate cache key for a book."""
        if isbn:
            return f"isbn_{isbn}"
        # Normalize title and author for cache key
        normalized = f"{title}_{author}".lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = '_'.join(normalized.split())
        return normalized

    def _train_on_database(self):
        """Train the estimator on existing books in the database."""
        try:
            from greatreads.models import Book

            # Get all books with both word_count and page_count
            books = self.db.query(Book).filter(
                Book.word_count.isnot(None),
                Book.page_count.isnot(None),
                Book.page_count > 0,
                Book.word_count > 0
            ).all()

            if not books:
                return

            # Calculate author-specific words per page
            author_data = {}
            genre_data = {}
            all_wpp = []

            # Filter outliers: typical books have 200-600 words per page
            # Anything outside this range is likely data entry errors or web serials
            MIN_WPP = 200
            MAX_WPP = 600

            filtered_count = 0

            for book in books:
                wpp = book.word_count / book.page_count

                # Skip outliers
                if wpp < MIN_WPP or wpp > MAX_WPP:
                    filtered_count += 1
                    continue

                all_wpp.append(wpp)

                # Track by author
                author = book.author
                if author:
                    if author not in author_data:
                        author_data[author] = []
                    author_data[author].append(wpp)

                # Track by genre
                if book.genre:
                    if book.genre not in genre_data:
                        genre_data[book.genre] = []
                    genre_data[book.genre].append(wpp)

            # Calculate averages
            for author, wpp_list in author_data.items():
                self.author_wpp[author] = sum(wpp_list) / len(wpp_list)

            for genre, wpp_list in genre_data.items():
                self.genre_wpp[genre] = sum(wpp_list) / len(wpp_list)

            # Calculate global average
            if all_wpp:
                self.global_wpp = sum(all_wpp) / len(all_wpp)

            print(f"[dim]Trained on {len(all_wpp)} books ({filtered_count} outliers filtered): {len(author_data)} authors, {len(genre_data)} genres[/dim]")
            print(f"[dim]Global average: {self.global_wpp:.1f} words/page[/dim]")

        except Exception as e:
            print(f"Warning: Could not train on database: {e}")
    
    def estimate(self, book_data: Dict) -> Dict:
        """
        Estimate word count for a book using multiple strategies.
        
        Args:
            book_data: Dictionary with keys: title, authors, isbn_13, isbn_10, page_count, etc.
        
        Returns:
            Dictionary with: word_count, confidence, source
        """
        title = book_data.get('title', '')
        author = book_data.get('primary_author', '')
        isbn_13 = book_data.get('isbn_13')
        isbn_10 = book_data.get('isbn_10')
        page_count = book_data.get('page_count')
        
        # Check cache first
        cache_key = self._get_cache_key(isbn_13 or isbn_10, title, author)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try strategies in order of reliability
        result = None
        
        # Strategy 1: Google Books API (sometimes has word count in description)
        if isbn_13 or isbn_10:
            result = self._try_google_books(isbn_13 or isbn_10)
        
        # Strategy 2: How Long to Read
        if not result:
            result = self._try_how_long_to_read(title, author)
        
        # Strategy 3: AR BookFinder
        if not result and isbn_13:
            result = self._try_ar_bookfinder(isbn_13)
        
        # Strategy 4: Page count estimation (if we have page count)
        if not result and page_count:
            result = self._estimate_from_pages(page_count, author, title)

        # Strategy 5: Gemini AI estimation (for books without page count)
        if not result and self.gemini_api_key:
            result = self._try_gemini_estimation(title, author, page_count)

        # Strategy 6: Use trained global average (for books without page count)
        if not result and self.global_wpp:
            # Estimate based on global average and typical book length
            estimated_pages = 400  # Typical novel length
            word_count = int(estimated_pages * self.global_wpp)
            result = {
                'word_count': word_count,
                'confidence': 'low',
                'source': f'global_avg_estimate_{self.global_wpp:.0f}wpp'
            }

        # Fallback: Use average book length
        if not result:
            result = {
                'word_count': 80000,
                'confidence': 'low',
                'source': 'default_average'
            }
        
        # Cache the result
        self.cache[cache_key] = result
        self._save_cache()
        
        return result
    
    def _try_google_books(self, isbn: str) -> Optional[Dict]:
        """Try to extract word count from Google Books API."""
        # Google Books API rarely has word count, but worth checking
        # This is a placeholder for now
        return None
    
    def _try_how_long_to_read(self, title: str, author: str) -> Optional[Dict]:
        """Scrape How Long to Read for word count."""
        try:
            # Search for the book
            search_url = "https://howlongtoread.com/search"
            params = {'q': f"{title} {author}"}
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for word count in the results
            # This is a simplified version - actual implementation would need
            # to parse the specific HTML structure of the site
            word_count_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*words', response.text, re.IGNORECASE)
            if word_count_match:
                word_count = int(word_count_match.group(1).replace(',', ''))
                return {
                    'word_count': word_count,
                    'confidence': 'high',
                    'source': 'how_long_to_read'
                }
        except Exception as e:
            print(f"Error scraping How Long to Read: {e}")
        
        return None
    
    def _try_ar_bookfinder(self, isbn: str) -> Optional[Dict]:
        """Scrape AR BookFinder for word count."""
        # AR BookFinder requires more complex scraping
        # Placeholder for now
        return None
    
    def _estimate_from_pages(self, page_count: int, author: str, title: str) -> Dict:
        """Estimate word count from page count using trained data."""
        words_per_page = None
        source = None
        confidence = 'medium'

        # Priority 1: Use author-specific data if available
        if author in self.author_wpp:
            words_per_page = self.author_wpp[author]
            source = f'author_trained_{words_per_page:.0f}wpp'
            confidence = 'high'  # Author-specific is more reliable

        # Priority 2: Try to infer genre from title and use genre data
        if not words_per_page:
            title_lower = title.lower()
            genre = None

            # Try to match genre from title keywords
            if any(word in title_lower for word in ['fantasy', 'epic', 'saga', 'dragon', 'magic']):
                genre = 'Fantasy'
            elif any(word in title_lower for word in ['science fiction', 'sci-fi', 'space', 'alien']):
                genre = 'Science Fiction'
            elif any(word in title_lower for word in ['mystery', 'detective', 'murder']):
                genre = 'Mystery'
            elif any(word in title_lower for word in ['romance', 'love']):
                genre = 'Romance'

            if genre and genre in self.genre_wpp:
                words_per_page = self.genre_wpp[genre]
                source = f'genre_trained_{words_per_page:.0f}wpp'
                confidence = 'medium'

        # Priority 3: Use global average from database
        if not words_per_page:
            words_per_page = self.global_wpp
            source = f'global_trained_{words_per_page:.0f}wpp'
            confidence = 'medium'

        word_count = int(page_count * words_per_page)

        return {
            'word_count': word_count,
            'confidence': confidence,
            'source': source
        }
    
    def _try_gemini_estimation(self, title: str, author: str, page_count: Optional[int]) -> Optional[Dict]:
        """Use Gemini AI to estimate word count via REST API."""
        if not self.gemini_api_key:
            return None

        try:
            # Build prompt
            prompt = f"""You are a book expert. Estimate the word count for this book:

Title: {title}
Author: {author}
Page Count: {page_count if page_count else 'Unknown'}

Based on the author's typical writing style, the genre, and the page count (if available),
provide your best estimate of the word count.

Respond with ONLY a JSON object in this exact format:
{{"word_count": <number>, "reasoning": "<brief explanation>"}}

Do not include any other text before or after the JSON."""

            # Use Gemini REST API (v1 endpoint with gemini-2.0-flash-lite model - fast and free)
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-lite:generateContent?key={self.gemini_api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }

            response = self.session.post(url, json=payload, timeout=30)

            if response.status_code != 200:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return None

            result = response.json()

            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    response_text = candidate['content']['parts'][0].get('text', '').strip()

                    # Extract JSON from response
                    json_match = re.search(r'\{[^}]+\}', response_text)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        word_count = data.get('word_count')

                        if word_count and isinstance(word_count, (int, float)):
                            return {
                                'word_count': int(word_count),
                                'confidence': 'medium',
                                'source': 'gemini_ai',
                                'reasoning': data.get('reasoning', '')
                            }
        except Exception as e:
            print(f"Error using Gemini estimation: {e}")

        return None
    
    def estimate_batch(self, books: List[Dict]) -> List[Dict]:
        """Estimate word counts for multiple books."""
        results = []
        for book in books:
            estimate = self.estimate(book)
            book_with_estimate = book.copy()
            book_with_estimate['word_count_estimate'] = estimate
            results.append(book_with_estimate)
        return results

