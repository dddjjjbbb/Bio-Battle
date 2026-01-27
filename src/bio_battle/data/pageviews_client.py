"""Pageviews API client for fetching Wikipedia page statistics."""

from datetime import date, timedelta
from typing import Any

import requests
from returns.result import Failure, Result, Success

from bio_battle.domain.errors import (
    ApiError,
    FetchError,
    ParseError,
    PersonNotFoundError,
)

PAGEVIEWS_API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews"


class PageviewsClient:
    """Client for fetching page view statistics from Wikimedia API."""

    def __init__(
        self,
        base_url: str = PAGEVIEWS_API_BASE,
        timeout: int = 30,
    ) -> None:
        """Initialise the Pageviews client.

        Args:
            base_url: Base URL for Pageviews API.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "BioBattle/1.0 (https://github.com/bio-battle)",
            "Accept": "application/json",
        })

    def fetch_monthly_views(
        self, identifier: str, days: int = 30
    ) -> Result[int, FetchError]:
        """Fetch the total page views for the last N days.

        Args:
            identifier: Wikipedia page title (e.g., "Albert_Einstein").
            days: Number of days to fetch (default 30).

        Returns:
            Result containing total view count or FetchError.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Format dates as YYYYMMDD
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        url = (
            f"{self._base_url}/per-article/en.wikipedia/all-access/all-agents/"
            f"{identifier}/daily/{start_str}/{end_str}"
        )

        try:
            response = self._session.get(url, timeout=self._timeout)
        except requests.RequestException as e:
            return Failure(
                ApiError(
                    message=f"Request failed: {e}",
                    identifier=identifier,
                    status_code=None,
                )
            )

        if response.status_code == 404:
            return Failure(
                PersonNotFoundError(
                    message=f"Page not found: {identifier}",
                    identifier=identifier,
                )
            )

        if response.status_code != 200:
            return Failure(
                ApiError(
                    message=f"API error: {response.status_code}",
                    identifier=identifier,
                    status_code=response.status_code,
                )
            )

        try:
            data = response.json()
            return self._parse_pageviews_response(data, identifier)
        except (ValueError, KeyError) as e:
            return Failure(
                ParseError(
                    message=f"Failed to parse response: {e}",
                    identifier=identifier,
                )
            )

    def _parse_pageviews_response(
        self, data: dict[str, Any], identifier: str
    ) -> Result[int, FetchError]:
        """Parse the pageviews API response."""
        try:
            items = data.get("items", [])
            total_views = sum(item.get("views", 0) for item in items)
            return Success(total_views)
        except Exception as e:
            return Failure(
                ParseError(
                    message=f"Failed to parse response: {e}",
                    identifier=identifier,
                )
            )
