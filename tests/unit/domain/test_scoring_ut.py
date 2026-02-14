"""Unit tests for ScoringService."""

from datetime import date

from bio_battle.config.scoring_config import get_scoring_config
from bio_battle.domain.entities import Person, Score
from bio_battle.domain.scoring import ScoringService


def create_test_person(
    name: str = "Test Person",
    birth_date: date | None = date(1950, 1, 1),
    death_date: date | None = None,
    page_views: int = 100000,
    article_length: int = 25000,
    languages_count: int = 50,
) -> Person:
    """Create a test person with configurable fields."""
    return Person(
        identifier="test",
        name=name,
        description="Test description",
        extract="Test extract text for the biography.",
        birth_date=birth_date,
        death_date=death_date,
        image_url=None,
        page_views=page_views,
        article_length=article_length,
        languages_count=languages_count,
    )


class TestScoringService:
    """Tests for ScoringService."""

    def test_should_create_service_with_config(self) -> None:
        """ScoringService should be created with scoring config."""
        config = get_scoring_config()
        service = ScoringService(config)

        assert service is not None

    def test_should_calculate_all_category_scores(self) -> None:
        """calculate_scores should return scores for all categories."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person()

        scores = service.calculate_scores(person)

        assert "age" in scores
        assert "page_views" in scores
        assert "article_length" in scores
        assert "languages" in scores
        assert len(scores) == 4

    def test_should_calculate_age_score_for_deceased_person(self) -> None:
        """calculate_scores should correctly score age for deceased person."""
        config = get_scoring_config()
        service = ScoringService(config)
        # Born 1879, died 1955 = 76 years -> bracket 71-80 -> score 7
        person = create_test_person(
            birth_date=date(1879, 3, 14),
            death_date=date(1955, 4, 18),
        )

        scores = service.calculate_scores(person)

        assert scores["age"].raw_value == 76.0
        assert scores["age"].bracket_score == 7

    def test_should_return_default_age_score_when_no_birth_date(self) -> None:
        """calculate_scores should return default score for unknown age."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person(birth_date=None)

        scores = service.calculate_scores(person)

        assert scores["age"].raw_value == -1.0  # Sentinel for unknown
        assert scores["age"].bracket_score == 5  # Default middle score

    def test_should_calculate_page_views_score(self) -> None:
        """calculate_scores should correctly score page views."""
        config = get_scoring_config()
        service = ScoringService(config)
        # 100000 views -> bracket 50001-100000 -> score 5
        person = create_test_person(page_views=100000)

        scores = service.calculate_scores(person)

        assert scores["page_views"].raw_value == 100000.0
        assert scores["page_views"].bracket_score == 5

    def test_should_calculate_article_length_score(self) -> None:
        """calculate_scores should correctly score article length."""
        config = get_scoring_config()
        service = ScoringService(config)
        # 25000 words -> bracket 20001-50000 -> score 7
        person = create_test_person(article_length=25000)

        scores = service.calculate_scores(person)

        assert scores["article_length"].raw_value == 25000.0
        assert scores["article_length"].bracket_score == 7

    def test_should_calculate_languages_score(self) -> None:
        """calculate_scores should correctly score languages count."""
        config = get_scoring_config()
        service = ScoringService(config)
        # 50 languages -> bracket 31-50 -> score 5
        person = create_test_person(languages_count=50)

        scores = service.calculate_scores(person)

        assert scores["languages"].raw_value == 50.0
        assert scores["languages"].bracket_score == 5

    def test_should_return_score_objects(self) -> None:
        """calculate_scores should return Score objects."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person()

        scores = service.calculate_scores(person)

        for score in scores.values():
            assert isinstance(score, Score)

    def test_should_handle_extreme_values(self) -> None:
        """calculate_scores should handle very high values."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person(
            page_views=50000000,  # 50 million views
            article_length=500000,  # 500k words
            languages_count=300,  # 300 languages
        )

        scores = service.calculate_scores(person)

        # All should get maximum scores (10)
        assert scores["page_views"].bracket_score == 10
        assert scores["article_length"].bracket_score == 10
        assert scores["languages"].bracket_score == 10

    def test_should_handle_minimum_values(self) -> None:
        """calculate_scores should handle minimum values."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person(
            page_views=10,  # Very few views
            article_length=100,  # Very short article
            languages_count=1,  # Single language
        )

        scores = service.calculate_scores(person)

        # All should get minimum scores (1)
        assert scores["page_views"].bracket_score == 1
        assert scores["article_length"].bracket_score == 1
        assert scores["languages"].bracket_score == 1

    def test_should_always_include_age_category(self) -> None:
        """calculate_scores should always include age for all subjects."""
        config = get_scoring_config()
        service = ScoringService(config)
        person = create_test_person()

        scores = service.calculate_scores(person)

        assert "age" in scores
        assert len(scores) == 4
