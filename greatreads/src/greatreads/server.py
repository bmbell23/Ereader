"""Production server entry point."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from greatreads.config import settings


def main():
    """Start the GreatReads production server."""
    print(f"🚀 Starting {settings.app_name} production server...")
    print(f"📍 Production URL: {settings.app_url}")
    print(f"🔧 Port: {settings.port}")
    
    uvicorn.run(
        "greatreads.main:app",
        host=settings.host,
        port=settings.port,
        workers=1,
        log_level="info"
    )


if __name__ == "__main__":
    main()
