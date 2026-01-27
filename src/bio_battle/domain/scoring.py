"""Scoring service for calculating person scores."""


from bio_battle.config.scoring_config import ScoringConfig
from bio_battle.domain.entities import Person, Score


class ScoringService:
    """Stateless service for calculating scores based on configurable brackets."""

    def __init__(self, config: ScoringConfig) -> None:
        """Initialise scoring service with configuration."""
        self._config = config

    def calculate_scores(self, person: Person) -> dict[str, Score]:
        """Calculate scores for all categories.

        Returns a dictionary mapping category name to Score object containing
        both the raw value and the bracket score.
        """
        return {
            "age": self._calculate_age_score(person),
            "page_views": self._calculate_page_views_score(person),
            "article_length": self._calculate_article_length_score(person),
            "languages": self._calculate_languages_score(person),
        }

    def _calculate_age_score(self, person: Person) -> Score:
        """Calculate score based on age.

        For unknown ages, returns a default middle score of 5.
        """
        age = person.age
        if age is None:
            # Unknown age gets a default middle score
            return Score(raw_value=-1.0, bracket_score=5)

        raw_value = float(age)
        category = self._config.get_category("age")
        bracket_score = category.get_score(raw_value)
        return Score(raw_value=raw_value, bracket_score=bracket_score)

    def _calculate_page_views_score(self, person: Person) -> Score:
        """Calculate score based on page views."""
        raw_value = float(person.page_views)
        category = self._config.get_category("page_views")
        bracket_score = category.get_score(raw_value)
        return Score(raw_value=raw_value, bracket_score=bracket_score)

    def _calculate_article_length_score(self, person: Person) -> Score:
        """Calculate score based on article length."""
        raw_value = float(person.article_length)
        category = self._config.get_category("article_length")
        bracket_score = category.get_score(raw_value)
        return Score(raw_value=raw_value, bracket_score=bracket_score)

    def _calculate_languages_score(self, person: Person) -> Score:
        """Calculate score based on number of Wikipedia language editions."""
        raw_value = float(person.languages_count)
        category = self._config.get_category("languages")
        bracket_score = category.get_score(raw_value)
        return Score(raw_value=raw_value, bracket_score=bracket_score)
