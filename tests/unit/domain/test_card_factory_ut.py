"""Unit tests for CardFactory."""

from datetime import date
from unittest.mock import Mock

from returns.result import Failure, Success

from bio_battle.config.scoring_config import get_scoring_config
from bio_battle.data.repositories import PersonRepository
from bio_battle.domain.card_factory import CardFactory
from bio_battle.domain.entities import Card, Person
from bio_battle.domain.errors import PersonNotFoundError
from bio_battle.domain.scoring import ScoringService


def create_test_person(
    identifier: str = "Albert_Einstein",
    name: str = "Albert Einstein",
) -> Person:
    """Create a test person."""
    return Person(
        identifier=identifier,
        name=name,
        description="German-born theoretical physicist",
        extract="Albert Einstein was a German-born theoretical physicist who is widely held to be one of the greatest and most influential scientists of all time.",
        birth_date=date(1879, 3, 14),
        death_date=date(1955, 4, 18),
        image_url="https://example.com/einstein.jpg",
        page_views=1000000,
        article_length=50000,
        languages_count=150,
    )


class TestCardFactory:
    """Tests for CardFactory."""

    def test_should_create_factory_with_dependencies(self) -> None:
        """CardFactory should be created with repository and scoring service."""
        repository = Mock(spec=PersonRepository)
        scoring_service = ScoringService(get_scoring_config())

        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        assert factory is not None

    def test_should_create_card_from_identifier(self) -> None:
        """create_card should return Card when person is found."""
        repository = Mock(spec=PersonRepository)
        person = create_test_person()
        repository.get_by_identifier.return_value = Success(person)
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        result = factory.create_card("Albert_Einstein")

        assert isinstance(result, Success)
        card = result.unwrap()
        assert isinstance(card, Card)
        assert card.person == person

    def test_should_calculate_scores_for_card(self) -> None:
        """create_card should include calculated scores."""
        repository = Mock(spec=PersonRepository)
        person = create_test_person()
        repository.get_by_identifier.return_value = Success(person)
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        result = factory.create_card("Albert_Einstein")

        card = result.unwrap()
        assert "age" in card.scores
        assert "page_views" in card.scores
        assert "article_length" in card.scores
        assert "languages" in card.scores

    def test_should_return_failure_when_person_not_found(self) -> None:
        """create_card should return Failure when person is not found."""
        repository = Mock(spec=PersonRepository)
        error = PersonNotFoundError(
            message="Person not found",
            identifier="Unknown_Person",
        )
        repository.get_by_identifier.return_value = Failure(error)
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        result = factory.create_card("Unknown_Person")

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), PersonNotFoundError)

    def test_should_create_multiple_cards(self) -> None:
        """create_cards should return list of Cards for valid identifiers."""
        repository = Mock(spec=PersonRepository)
        person1 = create_test_person(identifier="Person_1", name="Person One")
        person2 = create_test_person(identifier="Person_2", name="Person Two")
        repository.get_by_identifier.side_effect = [
            Success(person1),
            Success(person2),
        ]
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        results = factory.create_cards(["Person_1", "Person_2"])

        assert len(results) == 2
        assert isinstance(results[0], Success)
        assert isinstance(results[1], Success)

    def test_should_handle_partial_failures_in_batch(self) -> None:
        """create_cards should handle mix of successes and failures."""
        repository = Mock(spec=PersonRepository)
        person = create_test_person(identifier="Valid_Person", name="Valid Person")
        error = PersonNotFoundError(
            message="Person not found",
            identifier="Invalid_Person",
        )
        repository.get_by_identifier.side_effect = [
            Success(person),
            Failure(error),
        ]
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        results = factory.create_cards(["Valid_Person", "Invalid_Person"])

        assert len(results) == 2
        assert isinstance(results[0], Success)
        assert isinstance(results[1], Failure)

    def test_should_call_repository_with_correct_identifier(self) -> None:
        """create_card should pass identifier to repository."""
        repository = Mock(spec=PersonRepository)
        person = create_test_person()
        repository.get_by_identifier.return_value = Success(person)
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        factory.create_card("Albert_Einstein")

        repository.get_by_identifier.assert_called_once_with("Albert_Einstein")

    def test_should_return_empty_list_for_empty_input(self) -> None:
        """create_cards should return empty list for empty input."""
        repository = Mock(spec=PersonRepository)
        scoring_service = ScoringService(get_scoring_config())
        factory = CardFactory(
            person_repository=repository,
            scoring_service=scoring_service,
        )

        results = factory.create_cards([])

        assert results == []
