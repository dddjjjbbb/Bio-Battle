"""Unit tests for Pageviews client."""

import re
from typing import Any

import responses
from returns.result import Failure, Success

from bio_battle.data.pageviews_client import PageviewsClient
from bio_battle.domain.errors import ApiError, PersonNotFoundError


def create_mock_pageviews_response(
    daily_views: int = 1000,
    days: int = 30,
) -> dict[str, Any]:
    """Create a mock Pageviews API response."""
    items = [
        {"views": daily_views, "timestamp": f"202501{str(i+1).zfill(2)}00"}
        for i in range(days)
    ]
    return {"items": items}


class TestPageviewsClient:
    """Tests for PageviewsClient."""

    @responses.activate
    def test_should_fetch_monthly_pageviews(self) -> None:
        """PageviewsClient should fetch monthly pageviews."""
        # Use regex to match any date pattern
        url_pattern = re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/per-article/"
            r"en\.wikipedia/all-access/all-agents/Albert_Einstein/daily/\d{8}/\d{8}"
        )
        responses.add(
            responses.GET,
            url_pattern,
            json=create_mock_pageviews_response(daily_views=5000, days=30),
            status=200,
        )
        client = PageviewsClient()

        result = client.fetch_monthly_views("Albert_Einstein")

        assert isinstance(result, Success)
        views = result.unwrap()
        # 5000 views/day * 30 days = 150000 total
        assert views == 150000

    @responses.activate
    def test_should_return_error_for_not_found(self) -> None:
        """PageviewsClient should return error for non-existent page."""
        url_pattern = re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/per-article/"
            r"en\.wikipedia/all-access/all-agents/NonExistent/daily/\d{8}/\d{8}"
        )
        responses.add(
            responses.GET,
            url_pattern,
            json={"type": "not_found"},
            status=404,
        )
        client = PageviewsClient()

        result = client.fetch_monthly_views("NonExistent")

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PersonNotFoundError)

    @responses.activate
    def test_should_handle_empty_response(self) -> None:
        """PageviewsClient should handle empty response."""
        url_pattern = re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/per-article/"
            r"en\.wikipedia/all-access/all-agents/Test_Person/daily/\d{8}/\d{8}"
        )
        responses.add(
            responses.GET,
            url_pattern,
            json={"items": []},
            status=200,
        )
        client = PageviewsClient()

        result = client.fetch_monthly_views("Test_Person")

        assert isinstance(result, Success)
        views = result.unwrap()
        assert views == 0

    @responses.activate
    def test_should_return_error_for_api_failure(self) -> None:
        """PageviewsClient should return error for API failures."""
        url_pattern = re.compile(
            r"https://wikimedia\.org/api/rest_v1/metrics/pageviews/per-article/"
            r"en\.wikipedia/all-access/all-agents/Test_Person/daily/\d{8}/\d{8}"
        )
        responses.add(
            responses.GET,
            url_pattern,
            json={"error": "Internal error"},
            status=500,
        )
        client = PageviewsClient()

        result = client.fetch_monthly_views("Test_Person")

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, ApiError)
