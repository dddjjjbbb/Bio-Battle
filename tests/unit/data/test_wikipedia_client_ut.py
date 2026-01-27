"""Unit tests for Wikipedia client."""

from typing import Any

import pytest
import responses
from returns.result import Failure, Success

from bio_battle.data.wikipedia_client import WikipediaClient, WikipediaPersonData
from bio_battle.domain.errors import ApiError, PersonNotFoundError

WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"


def create_mock_response(
    title: str = "Albert Einstein",
    description: str = "Theoretical physicist",
    extract: str = "Albert Einstein was a German-born theoretical physicist.",
    thumbnail_url: str | None = "https://example.com/image.jpg",
) -> dict[str, Any]:
    """Create a mock Wikipedia API response."""
    response: dict[str, Any] = {
        "title": title,
        "description": description,
        "extract": extract,
        "content_urls": {
            "desktop": {"page": f"https://en.wikipedia.org/wiki/{title}"}
        },
    }
    if thumbnail_url:
        response["thumbnail"] = {"source": thumbnail_url}
    return response


class TestWikipediaClient:
    """Tests for WikipediaClient."""

    @responses.activate
    def test_should_fetch_person_summary(self) -> None:
        """WikipediaClient should fetch person summary from API."""
        responses.add(
            responses.GET,
            f"{WIKIPEDIA_API_URL}/Albert_Einstein",
            json=create_mock_response(),
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_summary("Albert_Einstein")

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.title == "Albert Einstein"
        assert data.description == "Theoretical physicist"

    @responses.activate
    def test_should_return_error_for_not_found(self) -> None:
        """WikipediaClient should return error for non-existent page."""
        responses.add(
            responses.GET,
            f"{WIKIPEDIA_API_URL}/NonExistent_Person",
            json={"type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"},
            status=404,
        )
        client = WikipediaClient()

        result = client.fetch_summary("NonExistent_Person")

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PersonNotFoundError)

    @responses.activate
    def test_should_return_error_for_api_failure(self) -> None:
        """WikipediaClient should return error for API failures."""
        responses.add(
            responses.GET,
            f"{WIKIPEDIA_API_URL}/Test_Person",
            json={"error": "Internal error"},
            status=500,
        )
        client = WikipediaClient()

        result = client.fetch_summary("Test_Person")

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, ApiError)
        assert error.status_code == 500

    @responses.activate
    def test_should_handle_missing_thumbnail(self) -> None:
        """WikipediaClient should handle missing thumbnail."""
        responses.add(
            responses.GET,
            f"{WIKIPEDIA_API_URL}/Test_Person",
            json=create_mock_response(thumbnail_url=None),
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_summary("Test_Person")

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.thumbnail_url is None

    @responses.activate
    def test_should_extract_thumbnail_url(self) -> None:
        """WikipediaClient should extract thumbnail URL."""
        responses.add(
            responses.GET,
            f"{WIKIPEDIA_API_URL}/Test_Person",
            json=create_mock_response(thumbnail_url="https://upload.wikimedia.org/image.jpg"),
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_summary("Test_Person")

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.thumbnail_url == "https://upload.wikimedia.org/image.jpg"


class TestWikipediaPersonData:
    """Tests for WikipediaPersonData dataclass."""

    def test_should_create_person_data(self) -> None:
        """WikipediaPersonData should be created with all fields."""
        data = WikipediaPersonData(
            title="Albert Einstein",
            description="Theoretical physicist",
            extract="Einstein was a physicist.",
            thumbnail_url="https://example.com/image.jpg",
            page_url="https://en.wikipedia.org/wiki/Albert_Einstein",
        )

        assert data.title == "Albert Einstein"
        assert data.description == "Theoretical physicist"
        assert data.extract == "Einstein was a physicist."
        assert data.thumbnail_url == "https://example.com/image.jpg"

    def test_should_be_immutable(self) -> None:
        """WikipediaPersonData should be immutable."""
        data = WikipediaPersonData(
            title="Test",
            description="Desc",
            extract="Extract",
            thumbnail_url=None,
            page_url="https://example.com",
        )

        with pytest.raises(AttributeError):
            data.title = "New Title"  # type: ignore[misc]
