"""Unit tests for scoring configuration."""

import pytest

from bio_battle.config.scoring_config import (
    CategoryConfig,
    ScoringBracket,
    ScoringConfig,
    get_scoring_config,
)


class TestScoringBracket:
    """Tests for ScoringBracket dataclass."""

    def test_should_create_immutable_bracket(self) -> None:
        """ScoringBracket should be immutable."""
        bracket = ScoringBracket(min_value=0, max_value=10, score=5)

        assert bracket.min_value == 0
        assert bracket.max_value == 10
        assert bracket.score == 5

    def test_should_raise_when_modifying_frozen_bracket(self) -> None:
        """ScoringBracket should raise error when modified."""
        bracket = ScoringBracket(min_value=0, max_value=10, score=5)

        with pytest.raises(AttributeError):
            bracket.score = 10  # type: ignore[misc]


class TestCategoryConfig:
    """Tests for CategoryConfig dataclass."""

    def test_should_create_category_with_brackets(self) -> None:
        """CategoryConfig should store name and brackets."""
        brackets = (
            ScoringBracket(0, 10, 1),
            ScoringBracket(11, 20, 2),
        )
        category = CategoryConfig(
            name="test_category",
            display_name="Test Category",
            brackets=brackets,
        )

        assert category.name == "test_category"
        assert category.display_name == "Test Category"
        assert len(category.brackets) == 2

    def test_should_return_score_for_value_in_bracket(self) -> None:
        """get_score should return correct score for value in bracket."""
        brackets = (
            ScoringBracket(0, 10, 1),
            ScoringBracket(11, 20, 2),
            ScoringBracket(21, 30, 3),
        )
        category = CategoryConfig(
            name="test",
            display_name="Test",
            brackets=brackets,
        )

        assert category.get_score(5) == 1
        assert category.get_score(15) == 2
        assert category.get_score(25) == 3

    def test_should_return_max_score_for_value_above_brackets(self) -> None:
        """get_score should return max score for values above all brackets."""
        brackets = (
            ScoringBracket(0, 10, 1),
            ScoringBracket(11, 20, 2),
        )
        category = CategoryConfig(
            name="test",
            display_name="Test",
            brackets=brackets,
        )

        assert category.get_score(100) == 2

    def test_should_return_min_score_for_value_below_brackets(self) -> None:
        """get_score should return min score for values below all brackets."""
        brackets = (
            ScoringBracket(10, 20, 2),
            ScoringBracket(21, 30, 3),
        )
        category = CategoryConfig(
            name="test",
            display_name="Test",
            brackets=brackets,
        )

        assert category.get_score(5) == 2


class TestScoringConfig:
    """Tests for ScoringConfig dataclass."""

    def test_should_create_config_with_default_categories(self) -> None:
        """ScoringConfig should have default categories."""
        config = ScoringConfig()

        assert len(config.categories) == 4
        assert "age" in config.category_names
        assert "page_views" in config.category_names
        assert "article_length" in config.category_names
        assert "languages" in config.category_names

    def test_should_get_category_by_name(self) -> None:
        """get_category should return category by name."""
        config = ScoringConfig()

        category = config.get_category("age")

        assert category.name == "age"
        assert category.display_name == "Age"

    def test_should_raise_for_unknown_category(self) -> None:
        """get_category should raise ValueError for unknown category."""
        config = ScoringConfig()

        with pytest.raises(ValueError, match="Unknown scoring category"):
            config.get_category("unknown")


class TestDefaultBrackets:
    """Tests for default scoring brackets."""

    def test_should_score_age_correctly(self) -> None:
        """Age brackets should score correctly."""
        config = get_scoring_config()
        category = config.get_category("age")

        # Young
        assert category.get_score(25) == 2
        # Middle aged
        assert category.get_score(55) == 5
        # Old
        assert category.get_score(85) == 8

    def test_should_score_page_views_correctly(self) -> None:
        """Page views brackets should score correctly."""
        config = get_scoring_config()
        category = config.get_category("page_views")

        # Low views
        assert category.get_score(500) == 1
        # Medium views
        assert category.get_score(75000) == 5
        # High views
        assert category.get_score(15000000) == 10

    def test_should_score_article_length_correctly(self) -> None:
        """Article length brackets should score correctly."""
        config = get_scoring_config()
        category = config.get_category("article_length")

        # Short article
        assert category.get_score(300) == 1
        # Medium article
        assert category.get_score(7500) == 5
        # Long article
        assert category.get_score(250000) == 10

    def test_should_score_languages_correctly(self) -> None:
        """Languages brackets should score correctly."""
        config = get_scoring_config()
        category = config.get_category("languages")

        # Few languages
        assert category.get_score(3) == 1
        # Medium languages
        assert category.get_score(60) == 6
        # Many languages
        assert category.get_score(250) == 10
