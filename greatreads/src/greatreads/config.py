"""Configuration settings for GreatReads."""

import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App settings
    app_name: str = "GreatReads"
    app_version: str = "2.0.10"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8006

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent

    # Detect if running in Docker
    is_docker: bool = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", "false").lower() == "true"

    # Database settings - support both Docker and local deployment
    @property
    def database_url(self) -> str:
        """Get database URL based on environment."""
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            return env_db_url

        # Default paths
        if self.is_docker:
            # In Docker, use /app/data directory
            return "sqlite:////app/data/greatreads.db"
        else:
            # Local development, use src directory
            return f"sqlite:///{self.project_root / 'src' / 'greatreads.db'}"

    # Static files directory - support both Docker and local
    @property
    def static_dir(self) -> Path:
        """Get static directory based on environment."""
        return self.project_root / "src" / "greatreads" / "static"

    @property
    def templates_dir(self) -> Path:
        """Get templates directory based on environment."""
        return self.project_root / "src" / "greatreads" / "templates"

    # Covers directory - in Docker, use /app/data/covers
    @property
    def covers_dir(self) -> Path:
        """Get covers directory based on environment."""
        if self.is_docker:
            return Path("/app/data/covers")
        else:
            return self.static_dir / "covers"

    # URL settings (for production deployment)
    base_url: str = "https://forge-freedom.com"
    app_path: str = "/"
    app_url: str = f"{base_url}/greatreads"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days

    # Reading tracker integration
    original_db_path: str = "../reading_tracker/data/db/reading_list.db"

    # External library paths (host paths; in Docker these must match mounted paths)
    # Calibre library – mounted read-only at /calibre in the container
    calibre_db_path: str = os.environ.get("CALIBRE_DB_PATH", "/calibre/metadata.db")
    # Calibre book root (same mount) – covers live at <root>/<book.path>/cover.jpg
    calibre_library_path: str = os.environ.get("CALIBRE_LIBRARY_PATH", "/calibre")

    # Audiobookshelf – mounted read-only at /audiobookshelf in the container
    abs_db_path: str = os.environ.get(
        "ABS_DB_PATH", "/audiobookshelf/absdatabase.sqlite"
    )
    # ABS metadata dir – covers live at <metadata_dir>/items/<item_id>/cover.jpg
    abs_metadata_path: str = os.environ.get(
        "ABS_METADATA_PATH", "/audiobookshelf/metadata"
    )

    # API Keys
    gemini_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()
