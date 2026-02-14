"""Unit tests for domain entities."""

from datetime import date

import pytest

from bio_battle.domain.entities import Card, EntityMode, Person, Score


class TestPerson:
    """Tests for Person entity."""

    def test_should_create_person_with_required_fields(self) -> None:
        """Person should be created with required fields."""
        person = Person(
            identifier="Albert_Einstein",
            name="Albert Einstein",
            description="Theoretical physicist",
            extract="Albert Einstein was a German-born theoretical physicist.",
            birth_date=date(1879, 3, 14),
            death_date=date(1955, 4, 18),
            image_url="https://example.com/einstein.jpg",
            page_views=1000000,
            article_length=50000,
            languages_count=150,
        )

        assert person.identifier == "Albert_Einstein"
        assert person.name == "Albert Einstein"
        assert person.description == "Theoretical physicist"
        assert person.birth_date == date(1879, 3, 14)
        assert person.death_date == date(1955, 4, 18)

    def test_should_be_immutable(self) -> None:
        """Person should be immutable (frozen dataclass)."""
        person = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=date(1990, 1, 1),
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        with pytest.raises(AttributeError):
            person.name = "New Name"  # type: ignore[misc]

    def test_should_calculate_age_for_living_person(self) -> None:
        """Person should calculate current age for living person."""
        # Using a fixed birth date for testing
        person = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=date(1990, 1, 15),
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        age = person.age
        # Age should be approximately 36 (in 2026)
        assert age is not None
        assert 35 <= age <= 37

    def test_should_calculate_age_for_deceased_person(self) -> None:
        """Person should calculate age at death for deceased person."""
        person = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=date(1879, 3, 14),
            death_date=date(1955, 4, 18),
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        age = person.age

        assert age == 76

    def test_should_return_none_age_when_no_birth_date(self) -> None:
        """Person should return None age when birth date is unknown."""
        person = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person.age is None

    def test_should_calculate_name_length(self) -> None:
        """Person should calculate name length in characters."""
        person = Person(
            identifier="test",
            name="Albert Einstein",
            description="Description",
            extract="Test extract text.",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person.name_length == 15

    def test_should_support_equality_comparison(self) -> None:
        """Two Person instances with same data should be equal."""
        person1 = Person(
            identifier="test",
            name="Test",
            description="Desc",
            extract="Extract text.",
            birth_date=date(1990, 1, 1),
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )
        person2 = Person(
            identifier="test",
            name="Test",
            description="Desc",
            extract="Extract text.",
            birth_date=date(1990, 1, 1),
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person1 == person2

    def test_should_return_extract_as_bio_when_longer(self) -> None:
        """Person.bio should return extract when it is longer than description."""
        person = Person(
            identifier="test",
            name="Test",
            description="Short desc",
            extract="Much longer extract text that provides more biographical detail.",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person.bio == person.extract

    def test_should_return_description_as_bio_when_extract_shorter(self) -> None:
        """Person.bio should return description when extract is shorter."""
        person = Person(
            identifier="test",
            name="Test",
            description="Longer description text",
            extract="Short",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person.bio == person.description

    def test_should_return_description_as_bio_when_extract_empty(self) -> None:
        """Person.bio should return description when extract is empty."""
        person = Person(
            identifier="test",
            name="Test",
            description="Description text",
            extract="",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )

        assert person.bio == person.description


class TestEntityMode:
    """Tests for EntityMode enum."""

    def test_should_have_person_mode(self) -> None:
        """EntityMode should include a PERSON value."""
        mode = EntityMode.PERSON

        assert mode.value == "person"

    def test_should_create_person_mode_from_string(self) -> None:
        """EntityMode should be created from 'person' string."""
        mode = EntityMode("person")

        assert mode == EntityMode.PERSON


class TestScore:
    """Tests for Score value object."""

    def test_should_create_score_with_raw_and_bracket_values(self) -> None:
        """Score should store raw value and bracket score."""
        score = Score(raw_value=72.0, bracket_score=8)

        assert score.raw_value == 72.0
        assert score.bracket_score == 8

    def test_should_be_immutable(self) -> None:
        """Score should be immutable."""
        score = Score(raw_value=72.0, bracket_score=8)

        with pytest.raises(AttributeError):
            score.bracket_score = 10  # type: ignore[misc]


class TestCard:
    """Tests for Card entity."""

    def test_should_create_card_with_person_and_scores(self) -> None:
        """Card should be created with subject and scores."""
        subject = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=date(1950, 1, 1),
            death_date=None,
            image_url="https://example.com/image.jpg",
            page_views=100000,
            article_length=25000,
            languages_count=50,
        )
        scores: dict[str, Score] = {
            "age": Score(raw_value=76.0, bracket_score=7),
            "page_views": Score(raw_value=100000.0, bracket_score=5),
            "article_length": Score(raw_value=25000.0, bracket_score=7),
            "languages": Score(raw_value=50.0, bracket_score=5),
        }

        card = Card(subject=subject, scores=scores)

        assert card.subject == subject
        assert card.person == subject  # backward compatibility
        assert len(card.scores) == 4

    def test_should_calculate_total_score(self) -> None:
        """Card should calculate total score from all categories."""
        subject = Person(
            identifier="test",
            name="Test Person",
            description="Description",
            extract="Test extract text.",
            birth_date=date(1950, 1, 1),
            death_date=None,
            image_url=None,
            page_views=100000,
            article_length=25000,
            languages_count=50,
        )
        scores: dict[str, Score] = {
            "age": Score(raw_value=76.0, bracket_score=7),
            "page_views": Score(raw_value=100000.0, bracket_score=5),
            "article_length": Score(raw_value=25000.0, bracket_score=7),
            "languages": Score(raw_value=50.0, bracket_score=5),
        }
        card = Card(subject=subject, scores=scores)

        assert card.total_score == 24  # 7 + 5 + 7 + 5

    def test_should_be_immutable(self) -> None:
        """Card should be immutable."""
        subject = Person(
            identifier="test",
            name="Test",
            description="Desc",
            extract="Extract text.",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )
        card = Card(subject=subject, scores={})

        with pytest.raises(AttributeError):
            card.subject = subject  # type: ignore[misc]

    def test_should_support_equality_comparison(self) -> None:
        """Two Card instances with same data should be equal."""
        subject = Person(
            identifier="test",
            name="Test",
            description="Desc",
            extract="Extract text.",
            birth_date=None,
            death_date=None,
            image_url=None,
            page_views=1000,
            article_length=5000,
            languages_count=10,
        )
        scores: dict[str, Score] = {"test": Score(raw_value=10.0, bracket_score=5)}

        card1 = Card(subject=subject, scores=scores)
        card2 = Card(subject=subject, scores=scores)

        assert card1 == card2
