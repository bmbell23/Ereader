"""
Book Discovery Module

Provides functionality for discovering books from external APIs.
"""

from .google_books_client import GoogleBooksClient
from .word_count_estimator import WordCountEstimator

__all__ = ['GoogleBooksClient', 'WordCountEstimator']

