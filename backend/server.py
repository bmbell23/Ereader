#!/usr/bin/env python3
"""
Ereader Backend Server
Serves ebook files from Calibre Content Server via REST API
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app access

# Calibre Content Server configuration
CALIBRE_URL = os.environ.get('CALIBRE_URL', 'http://localhost:8083')
CALIBRE_LIBRARY = os.environ.get('CALIBRE_LIBRARY', 'library')

def get_calibre_books(limit=None, offset=0, query=None):
    """Fetch books from Calibre Content Server"""
    try:
        params = {
            'library_id': CALIBRE_LIBRARY,
            'num': limit if limit else 1000,
            'offset': offset,
            'sort': 'author'  # Sort by author in Calibre
        }
        if query:
            params['query'] = query

        print(f"Fetching books with params: {params}")
        response = requests.get(f'{CALIBRE_URL}/ajax/search', params=params, timeout=30)
        response.raise_for_status()
        search_data = response.json()

        print(f"Calibre returned {len(search_data.get('book_ids', []))} book IDs, total: {search_data.get('total_num', 0)}")

        books = []
        for book_id in search_data.get('book_ids', []):
            book_data = get_book_metadata(book_id)
            if book_data:
                books.append(book_data)

        print(f"Successfully loaded {len(books)} books")

        # Additional sorting: by author last name, then series, then published date
        def sort_key(book):
            # Extract last name from first author
            author = book.get('author', 'Unknown')
            last_name = author.split(',')[0] if ',' in author else author.split()[-1] if author.split() else 'Unknown'

            # Series with index, or empty (handle None)
            series = book.get('series') or ''
            series_index = book.get('series_index') or 0

            # Publication date (handle None)
            published = book.get('published') or ''

            return (last_name.lower(), series.lower(), series_index, published)

        books.sort(key=sort_key)

        print(f"Returning {len(books)} sorted books")

        return books, search_data.get('total_num', 0)
    except Exception as e:
        print(f"Error fetching books from Calibre: {e}")
        import traceback
        traceback.print_exc()
        return [], 0

def get_book_metadata(book_id):
    """Get metadata for a specific book from Calibre"""
    try:
        response = requests.get(
            f'{CALIBRE_URL}/ajax/book/{book_id}/{CALIBRE_LIBRARY}',
            timeout=10
        )
        response.raise_for_status()
        book = response.json()

        # Extract relevant information
        authors = book.get('authors', ['Unknown'])
        formats = book.get('formats', [])

        # Get external-facing URL (replace localhost with actual host)
        host = os.environ.get('PUBLIC_HOST', '100.69.184.113:8091')

        return {
            'id': str(book_id),
            'title': book.get('title', 'Unknown'),
            'authors': authors,
            'author': ', '.join(authors),
            'publisher': book.get('publisher', ''),
            'formats': formats,
            'format': formats[0].upper() if formats else 'UNKNOWN',
            'tags': book.get('tags', []),
            'series': book.get('series', ''),
            'series_index': book.get('series_index', 0),
            'thumbnail': f'http://{host}/api/books/{book_id}/cover?type=thumb',
            'cover': f'http://{host}/api/books/{book_id}/cover',
            'description': book.get('comments', ''),
            'isbn': book.get('isbn', ''),
            'published': book.get('pubdate', ''),
            'rating': book.get('rating', 0),
        }
    except Exception as e:
        print(f"Error fetching book {book_id}: {e}")
        return None

@app.route('/api/books', methods=['GET'])
def list_books():
    """List all available books from Calibre"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    query = request.args.get('query')

    books, total = get_calibre_books(limit=limit, offset=offset, query=query)
    return jsonify({
        'books': books,
        'total': total,
        'offset': offset,
        'limit': limit
    })

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book_info(book_id):
    """Get information about a specific book"""
    book = get_book_metadata(book_id)

    if book:
        return jsonify(book)
    else:
        return jsonify({'error': 'Book not found'}), 404

@app.route('/api/books/<book_id>/cover', methods=['GET'])
def get_book_cover(book_id):
    """Proxy book cover from Calibre"""
    cover_type = request.args.get('type', 'cover')  # 'cover' or 'thumb'

    try:
        url = f'{CALIBRE_URL}/get/{cover_type}/{book_id}/{CALIBRE_LIBRARY}'
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            # Return a placeholder SVG if no cover
            placeholder = '''<svg width="200" height="300" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="200" height="300" fill="url(#grad)"/>
                <text x="100" y="150" text-anchor="middle" fill="white" font-size="60">📚</text>
            </svg>'''
            return Response(placeholder, mimetype='image/svg+xml')

        response.raise_for_status()
        return Response(response.content, mimetype=response.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        print(f"Error fetching cover: {e}")
        # Return placeholder on error
        placeholder = '<svg width="200" height="300" xmlns="http://www.w3.org/2000/svg"><rect fill="#333"/></svg>'
        return Response(placeholder, mimetype='image/svg+xml')

@app.route('/api/books/<book_id>/download', methods=['GET'])
def download_book(book_id):
    """Download a book file from Calibre"""
    # Get book metadata to find available formats
    book = get_book_metadata(book_id)

    if not book:
        print(f"❌ Book {book_id} not found")
        return jsonify({'error': 'Book not found'}), 404

    # Get the requested format or use the first available
    fmt = request.args.get('format', book['formats'][0] if book['formats'] else 'epub').lower()

    print(f"📚 Download request for book {book_id}: '{book.get('title', 'Unknown')}'")
    print(f"📖 Available formats: {book['formats']}")
    print(f"📥 Requested format: {fmt}")

    if fmt not in [f.lower() for f in book['formats']]:
        print(f"❌ Format {fmt} not available")
        return jsonify({'error': f'Format {fmt} not available for this book'}), 404

    # Proxy the download from Calibre
    try:
        calibre_download_url = f'{CALIBRE_URL}/get/{fmt}/{book_id}/{CALIBRE_LIBRARY}'
        print(f"🌐 Calibre URL: {calibre_download_url}")
        response = requests.get(calibre_download_url, stream=True, timeout=30)
        response.raise_for_status()

        # Create a filename
        safe_title = "".join(c for c in book['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.{fmt}"

        # Stream the response
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')
            }
        )
    except Exception as e:
        print(f"Error downloading book: {e}")
        return jsonify({'error': 'Failed to download book'}), 500

@app.route('/api/search', methods=['GET'])
def search_books():
    """Search books in Calibre library"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)

    books, total = get_calibre_books(limit=limit, offset=offset, query=query)
    return jsonify({
        'books': books,
        'total': total,
        'query': query,
        'offset': offset,
        'limit': limit
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Test Calibre connection
    calibre_ok = False
    try:
        response = requests.get(f'{CALIBRE_URL}/ajax/library-info', timeout=5)
        calibre_ok = response.status_code == 200
    except:
        pass

    return jsonify({
        'status': 'ok' if calibre_ok else 'degraded',
        'calibre_url': CALIBRE_URL,
        'calibre_library': CALIBRE_LIBRARY,
        'calibre_connected': calibre_ok
    })

if __name__ == '__main__':
    print(f"Ereader Backend Server")
    print(f"======================")
    print(f"Calibre URL: {CALIBRE_URL}")
    print(f"Calibre Library: {CALIBRE_LIBRARY}")

    # Test Calibre connection
    try:
        response = requests.get(f'{CALIBRE_URL}/ajax/library-info', timeout=5)
        if response.status_code == 200:
            print(f"✓ Connected to Calibre Content Server")
            libraries = response.json().get('library_map', {})
            print(f"  Available libraries: {', '.join(libraries.keys())}")
        else:
            print(f"✗ Could not connect to Calibre Content Server")
    except Exception as e:
        print(f"✗ Error connecting to Calibre: {e}")
        print(f"  Make sure Calibre Content Server is running at {CALIBRE_URL}")

    print(f"\nStarting server on http://0.0.0.0:8091")
    # Run server - accessible from local network
    app.run(host='0.0.0.0', port=8091, debug=True)
