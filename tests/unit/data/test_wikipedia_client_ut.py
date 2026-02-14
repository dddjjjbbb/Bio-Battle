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


class TestWikipediaClientSearch:
    """Tests for WikipediaClient search functionality."""

    @responses.activate
    def test_should_return_page_titles_for_keyword(self) -> None:
        """search_pages should return a list of page titles matching a keyword."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "search": [
                        {"title": "Oak"},
                        {"title": "Oak tree"},
                        {"title": "White oak"},
                    ]
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.search_pages("oak trees")

        assert isinstance(result, Success)
        titles = result.unwrap()
        assert len(titles) == 3
        assert "Oak" in titles

    @responses.activate
    def test_should_respect_limit_parameter(self) -> None:
        """search_pages should pass limit to the API."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "search": [
                        {"title": "Oak"},
                        {"title": "Pine"},
                    ]
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.search_pages("trees", limit=2)

        assert isinstance(result, Success)
        titles = result.unwrap()
        assert len(titles) == 2

    @responses.activate
    def test_should_return_failure_for_api_error(self) -> None:
        """search_pages should return Failure on API error."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={"error": "Server error"},
            status=500,
        )
        client = WikipediaClient()

        result = client.search_pages("trees")

        assert isinstance(result, Failure)

    @responses.activate
    def test_should_return_empty_list_for_no_results(self) -> None:
        """search_pages should return empty list when no results found."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={"query": {"search": []}},
            status=200,
        )
        client = WikipediaClient()

        result = client.search_pages("xyznonexistent")

        assert isinstance(result, Success)
        assert result.unwrap() == []


class TestWikipediaClientDescriptions:
    """Tests for fetching article descriptions to determine article type."""

    @responses.activate
    def test_should_return_descriptions_for_titles(self) -> None:
        """fetch_descriptions should return a dict of title -> description."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": {
                        "1": {"title": "Rose", "description": "Genus of plants"},
                        "2": {"title": "Flowers for Algernon", "description": "1966 novel by Daniel Keyes"},
                        "3": {"title": "Brandon Flowers", "description": "American rock musician"},
                    }
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_descriptions(["Rose", "Flowers for Algernon", "Brandon Flowers"])

        assert isinstance(result, Success)
        descriptions = result.unwrap()
        assert descriptions["Rose"] == "Genus of plants"
        assert descriptions["Flowers for Algernon"] == "1966 novel by Daniel Keyes"
        assert descriptions["Brandon Flowers"] == "American rock musician"

    @responses.activate
    def test_should_handle_missing_descriptions(self) -> None:
        """fetch_descriptions should return empty string for pages without descriptions."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": {
                        "1": {"title": "SomeObscureThing"},
                    }
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_descriptions(["SomeObscureThing"])

        assert isinstance(result, Success)
        descriptions = result.unwrap()
        assert descriptions["SomeObscureThing"] == ""

    @responses.activate
    def test_should_return_failure_on_api_error(self) -> None:
        """fetch_descriptions should return Failure on API error."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={"error": "Server error"},
            status=500,
        )
        client = WikipediaClient()

        result = client.fetch_descriptions(["Rose"])

        assert isinstance(result, Failure)


class TestWikipediaClientPageImages:
    """Tests for checking which pages have images."""

    @responses.activate
    def test_should_return_titles_with_images(self) -> None:
        """fetch_titles_with_images should return set of titles that have thumbnails."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": {
                        "1": {"title": "Rose", "thumbnail": {"source": "https://example.com/rose.jpg"}},
                        "2": {"title": "Obscure Plant"},
                        "3": {"title": "Oak", "thumbnail": {"source": "https://example.com/oak.jpg"}},
                    }
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_titles_with_images(["Rose", "Obscure Plant", "Oak"])

        assert isinstance(result, Success)
        titles_with_images = result.unwrap()
        assert "Rose" in titles_with_images
        assert "Oak" in titles_with_images
        assert "Obscure Plant" not in titles_with_images

    @responses.activate
    def test_should_return_empty_set_when_none_have_images(self) -> None:
        """fetch_titles_with_images should return empty set when no pages have images."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/w/api.php",
            json={
                "query": {
                    "pages": {
                        "1": {"title": "No Image Page"},
                    }
                }
            },
            status=200,
        )
        client = WikipediaClient()

        result = client.fetch_titles_with_images(["No Image Page"])

        assert isinstance(result, Success)
        assert result.unwrap() == set()
