"""Development server startup script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uvicorn
from greatreads.config import settings


def main():
    """Start the GreatReads development server."""
    print(f"🚀 Starting {settings.app_name} server...")
    print(f"📍 Local URL: http://{settings.host}:{settings.port}")
    print(f"📍 Production URL: {settings.app_url}")
    print(f"🔧 Port: {settings.port}")
    print(f"🐛 Debug: {settings.debug}")
    
    uvicorn.run(
        "greatreads.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
