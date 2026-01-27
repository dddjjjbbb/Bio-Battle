"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="BIO_BATTLE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Card dimensions (standard trading card size in mm)
    card_width_mm: float = Field(default=63.5, description="Card width in millimetres")
    card_height_mm: float = Field(
        default=88.9, description="Card height in millimetres"
    )

    # Sheet layout (cards per sheet)
    cards_per_row: int = Field(default=3, description="Cards per row on a sheet")
    cards_per_column: int = Field(default=3, description="Cards per column on a sheet")

    # Output directories
    output_dir: Path = Field(
        default=Path("output"), description="Output directory for generated PDFs"
    )
    cache_dir: Path = Field(
        default=Path("output/cache"), description="Cache directory for API responses"
    )

    # Cache settings
    cache_ttl_seconds: int = Field(
        default=86400, description="Cache TTL in seconds (24 hours default)"
    )

    # API settings
    wikipedia_api_timeout: int = Field(
        default=30, description="Wikipedia API timeout in seconds"
    )
    max_retries: int = Field(default=3, description="Maximum API retry attempts")
    retry_delay_seconds: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    # Image settings
    image_width_px: int = Field(
        default=200, description="Target image width in pixels"
    )
    image_height_px: int = Field(
        default=200, description="Target image height in pixels"
    )

    @property
    def cards_per_sheet(self) -> tuple[int, int]:
        """Return cards per sheet as (rows, columns) tuple."""
        return (self.cards_per_row, self.cards_per_column)


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
