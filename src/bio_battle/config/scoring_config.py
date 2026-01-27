"""Scoring configuration with bracket definitions."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringBracket:
    """A single scoring bracket with min, max, and score values."""

    min_value: float
    max_value: float
    score: int


@dataclass(frozen=True)
class CategoryConfig:
    """Configuration for a single scoring category."""

    name: str
    display_name: str
    brackets: tuple[ScoringBracket, ...]

    def get_score(self, value: float) -> int:
        """Get the score for a given value based on brackets."""
        for bracket in self.brackets:
            if bracket.min_value <= value <= bracket.max_value:
                return bracket.score
        # Return max score if above all brackets
        if value > self.brackets[-1].max_value:
            return self.brackets[-1].score
        # Return min score if below all brackets
        return self.brackets[0].score


@dataclass(frozen=True)
class ScoringConfig:
    """Complete scoring configuration for all categories."""

    categories: tuple[CategoryConfig, ...] = field(
        default_factory=lambda: DEFAULT_CATEGORIES
    )

    def get_category(self, name: str) -> CategoryConfig:
        """Get a category configuration by name."""
        for category in self.categories:
            if category.name == name:
                return category
        raise ValueError(f"Unknown scoring category: {name}")

    @property
    def category_names(self) -> list[str]:
        """Return list of all category names."""
        return [cat.name for cat in self.categories]


# Default scoring brackets for each category
AGE_BRACKETS = (
    ScoringBracket(0, 20, 1),
    ScoringBracket(21, 30, 2),
    ScoringBracket(31, 40, 3),
    ScoringBracket(41, 50, 4),
    ScoringBracket(51, 60, 5),
    ScoringBracket(61, 70, 6),
    ScoringBracket(71, 80, 7),
    ScoringBracket(81, 90, 8),
    ScoringBracket(91, 100, 9),
    ScoringBracket(101, float("inf"), 10),
)

PAGE_VIEWS_BRACKETS = (
    ScoringBracket(0, 1000, 1),
    ScoringBracket(1001, 5000, 2),
    ScoringBracket(5001, 10000, 3),
    ScoringBracket(10001, 50000, 4),
    ScoringBracket(50001, 100000, 5),
    ScoringBracket(100001, 500000, 6),
    ScoringBracket(500001, 1000000, 7),
    ScoringBracket(1000001, 5000000, 8),
    ScoringBracket(5000001, 10000000, 9),
    ScoringBracket(10000001, float("inf"), 10),
)

ARTICLE_LENGTH_BRACKETS = (
    ScoringBracket(0, 500, 1),
    ScoringBracket(501, 1000, 2),
    ScoringBracket(1001, 2000, 3),
    ScoringBracket(2001, 5000, 4),
    ScoringBracket(5001, 10000, 5),
    ScoringBracket(10001, 20000, 6),
    ScoringBracket(20001, 50000, 7),
    ScoringBracket(50001, 100000, 8),
    ScoringBracket(100001, 200000, 9),
    ScoringBracket(200001, float("inf"), 10),
)

LANGUAGES_BRACKETS = (
    ScoringBracket(0, 5, 1),
    ScoringBracket(6, 10, 2),
    ScoringBracket(11, 20, 3),
    ScoringBracket(21, 30, 4),
    ScoringBracket(31, 50, 5),
    ScoringBracket(51, 75, 6),
    ScoringBracket(76, 100, 7),
    ScoringBracket(101, 150, 8),
    ScoringBracket(151, 200, 9),
    ScoringBracket(201, float("inf"), 10),
)


# Default category configurations
DEFAULT_CATEGORIES: tuple[CategoryConfig, ...] = (
    CategoryConfig(
        name="age",
        display_name="Age",
        brackets=AGE_BRACKETS,
    ),
    CategoryConfig(
        name="page_views",
        display_name="Page Views",
        brackets=PAGE_VIEWS_BRACKETS,
    ),
    CategoryConfig(
        name="article_length",
        display_name="Article Length",
        brackets=ARTICLE_LENGTH_BRACKETS,
    ),
    CategoryConfig(
        name="languages",
        display_name="Languages",
        brackets=LANGUAGES_BRACKETS,
    ),
)


def get_scoring_config() -> ScoringConfig:
    """Create and return the default scoring configuration."""
    return ScoringConfig()
