#!/bin/bash
# GreatReads/Ereader test suite — stdlib unittest, no extra dependencies.
#
# Covers: service reachability (backend :8091, static :8090, Calibre, ABS),
# every /api route, the Calibre<->ABS matching logic, and the audiobook
# play/sync/close + HLS proxy chain. HTTP tests hit the *running* services, so
# start them first (./run.sh for the backend, the :8090 static server for web).
#
# Usage:  ./run-tests.sh                 # all tests, verbose
#         ./run-tests.sh test_matching   # one module (matching is offline-safe)
set -e
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "venv missing — run ./run.sh once first to create it." >&2
    exit 1
fi
source venv/bin/activate

# Load optional ABS creds so server.py import + any ABS-aware logic see them.
if [ -f abs.env ]; then set -a; source abs.env; set +a; fi

if [ -n "$1" ]; then
    exec python -m unittest -v "tests.$1"
fi
exec python -m unittest discover -s tests -p 'test_*.py' -v
