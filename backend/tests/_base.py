"""Shared config + helpers for the GreatReads/Ereader test suite.

All HTTP tests target the *running* services (backend :8091, static :8090,
Calibre :8083, ABS :13378) so the suite verifies the live system end to end,
not a mock. Override any host with the matching *_URL env var.
"""
import os
import requests

BACKEND = os.environ.get('BACKEND_URL', 'http://localhost:8091').rstrip('/')
STATIC = os.environ.get('STATIC_URL', 'http://localhost:8090').rstrip('/')
CALIBRE = os.environ.get('CALIBRE_URL', 'http://localhost:8083').rstrip('/')
ABS = os.environ.get('ABS_URL', 'http://localhost:13378').rstrip('/')

API = BACKEND + '/api'
TIMEOUT = 20


def get(path, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return requests.get(API + path, **kw)


def post(path, json=None, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return requests.post(API + path, json=json if json is not None else {}, **kw)


def put(path, json=None, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return requests.put(API + path, json=json if json is not None else {}, **kw)


def delete(path, **kw):
    kw.setdefault('timeout', TIMEOUT)
    return requests.delete(API + path, **kw)


def backend_up():
    """True if the backend answers /api/health with 200."""
    try:
        return get('/health', timeout=5).status_code == 200
    except Exception:
        return False


def abs_enabled():
    """True if the running backend has Audiobookshelf configured + reachable."""
    try:
        return bool(get('/audiobooks', timeout=10).json().get('absEnabled'))
    except Exception:
        return False


def first_dual_book():
    """Return a merged-library item that is matched to an audiobook (has absId
    and both media types), or None."""
    try:
        data = get('/library?limit=2000&offset=0', timeout=60).json()
    except Exception:
        return None
    for b in data.get('books', []):
        if b.get('absId') and b.get('mediaTypes') == ['ebook', 'audiobook']:
            return b
    return None
