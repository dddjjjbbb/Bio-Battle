"""Unit tests for application settings."""

from pathlib import Path

from bio_battle.config.settings import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_should_create_settings_with_defaults(self) -> None:
        """Settings should be created with default values."""
        settings = Settings()

        assert settings.card_width_mm == 63.5
        assert settings.card_height_mm == 88.9
        assert settings.cards_per_row == 3
        assert settings.cards_per_column == 3

    def test_should_return_cards_per_sheet_tuple(self) -> None:
        """Settings should return cards_per_sheet as tuple."""
        settings = Settings()

        result = settings.cards_per_sheet

        assert result == (3, 3)

    def test_should_have_default_output_directories(self) -> None:
        """Settings should have default output directories."""
        settings = Settings()

        assert settings.output_dir == Path("output")
        assert settings.cache_dir == Path("output/cache")

    def test_should_have_default_cache_ttl(self) -> None:
        """Settings should have 24 hour cache TTL by default."""
        settings = Settings()

        assert settings.cache_ttl_seconds == 86400

    def test_should_have_default_api_settings(self) -> None:
        """Settings should have default API configuration."""
        settings = Settings()

        assert settings.wikipedia_api_timeout == 30
        assert settings.max_retries == 3
        assert settings.retry_delay_seconds == 1.0

    def test_should_have_default_image_settings(self) -> None:
        """Settings should have default image dimensions."""
        settings = Settings()

        assert settings.image_width_px == 200
        assert settings.image_height_px == 200


class TestGetSettings:
    """Tests for get_settings factory function."""

    def test_should_return_settings_instance(self) -> None:
        """get_settings should return a Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)
