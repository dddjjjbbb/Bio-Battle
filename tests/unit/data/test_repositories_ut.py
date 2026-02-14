"""Unit tests for repositories."""

import re
from typing import Any

import responses
from returns.result import Failure, Success

from bio_battle.data.cache import MemoryCache
from bio_battle.data.pageviews_client import PageviewsClient
from bio_battle.data.repositories import WikipediaPersonRepository
from bio_battle.data.wikipedia_client import WikipediaClient
from bio_battle.domain.errors import PersonNotFoundError


def create_mock_summary_response() -> dict[str, Any]:
    """Create a mock Wikipedia summary API response."""
    return {
        "title": "Albert Einstein",
        "description": "Theoretical physicist (1879-1955)",
        "extract": "Albert Einstein was a German-born theoretical physicist.",
        "thumbnail": {"source": "https://example.com/einstein.jpg"},
        "content_urls": {
            "desktop": {"page": "https://en.wikipedia.org/wiki/Albert_Einstein"}
        },
    }


def create_mock_langlinks_response(num_languages: int = 150) -> dict[str, Any]:
    """Create a mock Wikipedia langlinks API response."""
    langlinks = [{"lang": f"lang{i}", "*": f"Title{i}"} for i in range(num_languages - 1)]
    return {
        "query": {
            "pages": {
                "12345": {
                    "pageid": 12345,
                    "title": "Albert Einstein",
                    "langlinks": langlinks,
                }
            }
        }
    }


def create_mock_html_response() -> str:
    """Create mock Wikipedia HTML with birth/death dates."""
    return """
    <html>
    <body>
    <table class="infobox">
        <tr><th>Born</th><td>14 March 1879</td></tr>
        <tr><th>Died</th><td>18 April 1955</td></tr>
    </table>
    <div id="content">
        This is the article content with many words to simulate article length.
        Einstein developed the theory of relativity, one of the two pillars of modern physics.
    </div>
    </body>
    </html>
    """


class TestWikipediaPersonRepository:
    """Tests for WikipediaPersonRepository."""

    def test_should_create_repository_with_dependencies(self) -> None:
        """WikipediaPersonRepository should accept injected dependencies."""
        wikipedia_client = WikipediaClient()
        pageviews_client = PageviewsClient()
        cache = MemoryCache()

        repository = WikipediaPersonRepository(
            wikipedia_client=wikipedia_client,
            pageviews_client=pageviews_client,
            cache=cache,
        )

        assert repository is not None

    @responses.activate
    def test_should_fetch_person_by_identifier(self) -> None:
        """WikipediaPersonRepository should fetch a person by identifier."""
        # Mock summary API
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein",
            json=create_mock_summary_response(),
            status=200,
        )

        # Mock langlinks API
        responses.add(
            responses.GET,
            re.compile(r"https://en\.wikipedia\.org/w/api\.php.*"),
            json=create_mock_langlinks_response(150),
            status=200,
        )

        # Mock pageviews API
        responses.add(
            responses.GET,
            re.compile(r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/.*"),
            json={"items": [{"views": 5000} for _ in range(30)]},
            status=200,
        )

        # Mock HTML for article length
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/api/rest_v1/page/html/Albert_Einstein",
            body=create_mock_html_response(),
            status=200,
        )

        repository = WikipediaPersonRepository(
            wikipedia_client=WikipediaClient(),
            pageviews_client=PageviewsClient(),
            cache=MemoryCache(),
        )

        result = repository.get_by_identifier("Albert_Einstein")

        assert isinstance(result, Success)
        person = result.unwrap()
        assert person.name == "Albert Einstein"
        assert person.description == "Theoretical physicist (1879-1955)"
        assert person.extract == "Albert Einstein was a German-born theoretical physicist."
        assert person.page_views == 150000  # 5000 * 30
        assert person.languages_count == 150

    @responses.activate
    def test_should_return_error_when_person_not_found(self) -> None:
        """WikipediaPersonRepository should return error for non-existent person."""
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/api/rest_v1/page/summary/NonExistent",
            json={"type": "not_found"},
            status=404,
        )

        repository = WikipediaPersonRepository(
            wikipedia_client=WikipediaClient(),
            pageviews_client=PageviewsClient(),
            cache=MemoryCache(),
        )

        result = repository.get_by_identifier("NonExistent")

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PersonNotFoundError)

    @responses.activate
    def test_should_cache_person_data(self) -> None:
        """WikipediaPersonRepository should cache fetched data."""
        # Mock all APIs
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein",
            json=create_mock_summary_response(),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://en\.wikipedia\.org/w/api\.php.*"),
            json=create_mock_langlinks_response(100),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/.*"),
            json={"items": [{"views": 1000} for _ in range(30)]},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://en.wikipedia.org/api/rest_v1/page/html/Albert_Einstein",
            body=create_mock_html_response(),
            status=200,
        )

        cache = MemoryCache()
        repository = WikipediaPersonRepository(
            wikipedia_client=WikipediaClient(),
            pageviews_client=PageviewsClient(),
            cache=cache,
        )

        # First call should hit APIs
        result1 = repository.get_by_identifier("Albert_Einstein")
        assert isinstance(result1, Success)

        # Second call should use cache (no additional API calls needed)
        result2 = repository.get_by_identifier("Albert_Einstein")
        assert isinstance(result2, Success)

        # Both results should be equivalent
        person1 = result1.unwrap()
        person2 = result2.unwrap()
        assert person1.name == person2.name

