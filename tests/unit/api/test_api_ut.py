"""Unit tests for Bio Battle REST API."""

from datetime import date
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from returns.result import Failure, Success

from bio_battle.api.app import create_app
from bio_battle.domain.entities import Card, Score, Subject
from bio_battle.domain.errors import PersonNotFoundError


def create_test_subject(identifier: str = "Albert_Einstein") -> Subject:
    """Create a test subject."""
    return Subject(
        identifier=identifier,
        name="Albert Einstein",
        description="German-born theoretical physicist",
        extract="Albert Einstein was a German-born theoretical physicist.",
        birth_date=date(1879, 3, 14),
        death_date=date(1955, 4, 18),
        image_url="https://example.com/einstein.jpg",
        page_views=1000000,
        article_length=50000,
        languages_count=150,
    )


def create_test_card(identifier: str = "Albert_Einstein") -> Card:
    """Create a test card."""
    subject = create_test_subject(identifier)
    scores: dict[str, Score] = {
        "age": Score(raw_value=76.0, bracket_score=7),
        "page_views": Score(raw_value=1000000.0, bracket_score=7),
        "article_length": Score(raw_value=50000.0, bracket_score=7),
        "languages": Score(raw_value=150.0, bracket_score=8),
    }
    return Card(subject=subject, scores=scores)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_should_return_ok(self) -> None:
        """GET /api/health should return status ok."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestCardEndpoint:
    """Tests for card endpoint."""

    @patch("bio_battle.api.app.create_card_factory")
    def test_should_return_card_data(self, mock_factory_fn: Mock) -> None:
        """GET /api/cards/{identifier} should return card JSON."""
        card = create_test_card()
        mock_factory = Mock()
        mock_factory.create_card.return_value = Success(card)
        mock_factory_fn.return_value = mock_factory

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/cards/Albert_Einstein")

        assert response.status_code == 200
        data = response.json()
        assert data["subject"]["name"] == "Albert Einstein"
        assert data["total_score"] == 29

    @patch("bio_battle.api.app.create_card_factory")
    def test_should_return_404_when_not_found(self, mock_factory_fn: Mock) -> None:
        """GET /api/cards/{identifier} should return 404 for missing subject."""
        error = PersonNotFoundError(
            message="Not found",
            identifier="Unknown",
        )
        mock_factory = Mock()
        mock_factory.create_card.return_value = Failure(error)
        mock_factory_fn.return_value = mock_factory

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/cards/Unknown")

        assert response.status_code == 404


class TestSearchEndpoint:
    """Tests for search endpoint."""

    @patch("bio_battle.api.app.WikipediaClient")
    def test_should_return_search_results(self, mock_client_cls: Mock) -> None:
        """GET /api/search should return list of page titles."""
        mock_client = Mock()
        mock_client.search_pages.return_value = Success(["Oak", "Pine", "Elm"])
        mock_client_cls.return_value = mock_client

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/search?q=trees")

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == ["Oak", "Pine", "Elm"]

    def test_should_return_400_without_query(self) -> None:
        """GET /api/search without q param should return 422."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/search")

        assert response.status_code == 422


class TestDeckEndpoint:
    """Tests for deck generation endpoint."""

    @patch("bio_battle.api.app.create_card_factory")
    def test_should_return_deck_of_cards(self, mock_factory_fn: Mock) -> None:
        """POST /api/deck should return list of cards."""
        card = create_test_card()
        mock_factory = Mock()
        mock_factory.create_card.return_value = Success(card)
        mock_factory_fn.return_value = mock_factory

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/deck",
            json={"identifiers": ["Albert_Einstein"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["cards"]) == 1
        assert data["cards"][0]["subject"]["name"] == "Albert Einstein"
