"""Factory for creating Bio Battle cards."""


from returns.result import Result

from bio_battle.data.repositories import SubjectRepository
from bio_battle.domain.entities import Card, Subject
from bio_battle.domain.errors import FetchError
from bio_battle.domain.scoring import ScoringService


class CardFactory:
    """Orchestrates card creation from identifier to complete Card entity."""

    def __init__(
        self,
        subject_repository: SubjectRepository,
        scoring_service: ScoringService,
    ) -> None:
        """Initialise factory with dependencies.

        Args:
            subject_repository: Repository for fetching subject data.
            scoring_service: Service for calculating scores.
        """
        self._subject_repository = subject_repository
        self._scoring_service = scoring_service

    def create_card(self, identifier: str) -> Result[Card, FetchError]:
        """Create a card for a subject by identifier.

        Orchestrates the process of:
        1. Fetching subject data from repository
        2. Calculating scores using scoring service
        3. Creating the final Card entity

        Args:
            identifier: The unique identifier (e.g., Wikipedia page title).

        Returns:
            Result containing Card or FetchError.
        """
        subject_result = self._subject_repository.get_by_identifier(identifier)

        return subject_result.map(self._create_card_from_subject)

    def create_cards(
        self, identifiers: list[str]
    ) -> list[Result[Card, FetchError]]:
        """Create cards for multiple identifiers.

        Args:
            identifiers: List of unique identifiers.

        Returns:
            List of Results, each containing Card or FetchError.
        """
        return [self.create_card(identifier) for identifier in identifiers]

    def _create_card_from_subject(self, subject: Subject) -> Card:
        """Create a Card from a Subject entity."""
        scores = self._scoring_service.calculate_scores(subject)
        return Card(subject=subject, scores=scores)
