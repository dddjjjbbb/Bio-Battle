"""Unit tests for nationality extraction."""


from bio_battle.domain.nationality import (
    extract_nationalities,
    get_country_code,
    get_flags_for_text,
)


class TestExtractNationalities:
    """Tests for extract_nationalities function."""

    def test_should_extract_single_nationality(self) -> None:
        """Should extract a single nationality."""
        result = extract_nationalities("American businessman")

        assert result == ["American"]

    def test_should_extract_hyphenated_nationalities(self) -> None:
        """Should extract hyphenated nationalities."""
        result = extract_nationalities("Polish-French physicist")

        assert result == ["Polish", "French"]

    def test_should_extract_nationalities_with_and(self) -> None:
        """Should extract nationalities joined with 'and'."""
        result = extract_nationalities("British and American actor")

        assert result == ["British", "American"]

    def test_should_return_empty_for_no_nationality(self) -> None:
        """Should return empty list when no nationality found."""
        result = extract_nationalities("physicist and chemist")

        assert result == []

    def test_should_return_empty_for_empty_string(self) -> None:
        """Should return empty list for empty string."""
        result = extract_nationalities("")

        assert result == []

    def test_should_handle_german_nationality(self) -> None:
        """Should correctly extract German nationality."""
        result = extract_nationalities("German-born theoretical physicist")

        assert result == ["German"]

    def test_should_handle_unknown_nationality(self) -> None:
        """Should skip nationalities not in mapping."""
        result = extract_nationalities("Martian explorer")

        assert result == []


class TestGetCountryCode:
    """Tests for get_country_code function."""

    def test_should_return_us_code_for_american(self) -> None:
        """Should return US code for American."""
        result = get_country_code("American")

        assert result == "US"

    def test_should_return_french_code(self) -> None:
        """Should return FR code for French."""
        result = get_country_code("French")

        assert result == "FR"

    def test_should_return_polish_code(self) -> None:
        """Should return PL code for Polish."""
        result = get_country_code("Polish")

        assert result == "PL"

    def test_should_return_none_for_unknown(self) -> None:
        """Should return None for unknown nationality."""
        result = get_country_code("Martian")

        assert result is None


class TestGetFlagsForText:
    """Tests for get_flags_for_text function."""

    def test_should_return_codes_for_polish_french(self) -> None:
        """Should return Polish and French codes."""
        result = get_flags_for_text("Polish-French physicist and chemist")

        assert result == "[PL/FR]"

    def test_should_return_german_code(self) -> None:
        """Should return German code for German-born."""
        result = get_flags_for_text("German-born theoretical physicist")

        assert result == "[DE]"

    def test_should_return_empty_for_no_nationality(self) -> None:
        """Should return empty string when no nationality found."""
        result = get_flags_for_text("physicist and chemist")

        assert result == ""

    def test_should_return_british_code(self) -> None:
        """Should return British code."""
        result = get_flags_for_text("British politician")

        assert result == "[GB]"

    def test_should_return_multiple_codes(self) -> None:
        """Should return multiple codes for multiple nationalities."""
        result = get_flags_for_text("British and American actor")

        assert result == "[GB/US]"
