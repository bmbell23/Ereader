# Calibre Integration

## Overview

Your ereader app now integrates directly with your existing Calibre Content Server! This means:

✅ **No duplicate storage** - Books stay in your Calibre library  
✅ **Full metadata** - Authors, series, tags, descriptions, cover art  
✅ **Organized library** - All your Calibre organization preserved  
✅ **Multiple formats** - Access EPUB, PDF, MOBI, etc. from Calibre  
✅ **Easy management** - Add/edit books in Calibre, instantly available in app

## Current Setup

Your Calibre Content Server is already running in Docker:
- **Container**: `calibre` 
- **Calibre URL**: `http://localhost:8083`
- **Library**: `library`
- **Total Books**: 949
- **Location**: `/home/brandon/projects/docker/calibre`

## How It Works

```
Android App → Backend API → Calibre Content Server → Calibre Library
```

1. **Android app** requests books from backend
2. **Backend** queries Calibre Content Server API
3. **Calibre** returns metadata and book files
4. **Backend** proxies the response to the app
5. **App** displays books with full metadata and downloads them

## Backend API Endpoints

The backend provides these endpoints to the app:

### GET /api/books
List all books from Calibre library
- Query params: `limit`, `offset`, `query`
- Returns: Book list with metadata

### GET /api/books/{id}
Get detailed info about a specific book
- Returns: Full book metadata

### GET /api/books/{id}/download
Download a book file
- Query params: `format` (epub, pdf, mobi, etc.)
- Returns: Book file stream

### GET /api/books/{id}/cover
Get book cover image
- Returns: Cover image

### GET /api/search
Search books in library
- Query params: `q` (search query), `limit`, `offset`
- Returns: Matching books

### GET /api/health
Check backend and Calibre connection status

## Configuration

The backend is configured via environment variables:

```bash
export CALIBRE_URL="http://localhost:8083"
export CALIBRE_LIBRARY="library"
```

Defaults are already set in `backend/run.sh` to match your setup.

## Testing

Test the Calibre connection:
```bash
python3 test-calibre-connection.py
```

Test the backend server:
```bash
cd backend
./run.sh
# In another terminal:
./test-server.sh
```

## Advantages Over File Scanning

**Before** (file scanning):
- ❌ Limited metadata (just filename)
- ❌ No cover images
- ❌ No author/series info
- ❌ Manual organization
- ❌ Duplicate files

**Now** (Calibre integration):
- ✅ Rich metadata from Calibre
- ✅ Beautiful cover images
- ✅ Author, series, tags, descriptions
- ✅ Automatic organization
- ✅ Single source of truth

## What You Get From Calibre

For each book, the app receives:
- **Title** - Book title
- **Authors** - All authors
- **Series** - Series name and position
- **Publisher** - Publisher name
- **Published Date** - Publication date
- **ISBN** - ISBN number
- **Tags** - All tags/categories
- **Description** - Full book description
- **Cover** - High-quality cover image
- **Thumbnail** - Smaller preview image
- **Formats** - All available formats (EPUB, PDF, etc.)
- **Rating** - Your Calibre rating
- **Custom Fields** - Any custom columns you've added

## Future Enhancements

Possible future integrations:
- [ ] Sync reading progress back to Calibre
- [ ] Update Calibre metadata from app
- [ ] Access Calibre collections/shelves
- [ ] Use Calibre's reading history
- [ ] Leverage Calibre's book recommendations

## Calibre Docker Configuration

Your current setup (from `../docker/calibre/docker-compose.yml`):
- Desktop GUI: Port 8084 (HTTPS with Selkies)
- Content Server: Port 8083 (HTTP)
- Library location: `/config/library` (inside container)
- Books storage: `/mnt/boston/media/books_calibre_docker`

The ereader backend connects to port 8083 to access the Content Server API.
