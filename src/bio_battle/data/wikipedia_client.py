"""Wikipedia API client for fetching person data."""

from dataclasses import dataclass
from typing import Any

import requests
from returns.result import Failure, Result, Success

from bio_battle.domain.errors import (
    ApiError,
    FetchError,
    ParseError,
    PersonNotFoundError,
)

WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1"


@dataclass(frozen=True)
class WikipediaPersonData:
    """Data fetched from Wikipedia API."""

    title: str
    description: str
    extract: str
    thumbnail_url: str | None
    page_url: str


class WikipediaClient:
    """Client for fetching data from Wikipedia REST API."""

    def __init__(
        self,
        base_url: str = WIKIPEDIA_API_BASE,
        timeout: int = 30,
    ) -> None:
        """Initialise the Wikipedia client.

        Args:
            base_url: Base URL for Wikipedia API.
            timeout: Request timeout in seconds.
        """
        self._base_url = base_url
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "BioBattle/1.0 (https://github.com/bio-battle)",
            "Accept": "application/json",
        })

    def fetch_summary(
        self, identifier: str
    ) -> Result[WikipediaPersonData, FetchError]:
        """Fetch a page summary from Wikipedia.

        Args:
            identifier: Wikipedia page title (e.g., "Albert_Einstein").

        Returns:
            Result containing WikipediaPersonData or FetchError.
        """
        url = f"{self._base_url}/page/summary/{identifier}"

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
            return self._parse_summary_response(data, identifier)
        except (ValueError, KeyError) as e:
            return Failure(
                ParseError(
                    message=f"Failed to parse response: {e}",
                    identifier=identifier,
                )
            )

    def _parse_summary_response(
        self, data: dict[str, Any], identifier: str
    ) -> Result[WikipediaPersonData, FetchError]:
        """Parse the summary API response."""
        try:
            title = data.get("title", identifier)
            description = data.get("description", "")
            extract = data.get("extract", "")

            # Extract thumbnail URL if present
            thumbnail_url: str | None = None
            thumbnail = data.get("thumbnail")
            if thumbnail and isinstance(thumbnail, dict):
                thumbnail_url = thumbnail.get("source")

            # Extract page URL
            content_urls = data.get("content_urls", {})
            desktop = content_urls.get("desktop", {})
            page_url = desktop.get("page", f"https://en.wikipedia.org/wiki/{identifier}")

            return Success(
                WikipediaPersonData(
                    title=title,
                    description=description,
                    extract=extract,
                    thumbnail_url=thumbnail_url,
                    page_url=page_url,
                )
            )
        except Exception as e:
            return Failure(
                ParseError(
                    message=f"Failed to parse response: {e}",
                    identifier=identifier,
                )
            )

    def fetch_page_html(self, identifier: str) -> Result[str, FetchError]:
        """Fetch the full HTML content of a Wikipedia page.

        Args:
            identifier: Wikipedia page title.

        Returns:
            Result containing HTML string or FetchError.
        """
        url = f"{self._base_url}/page/html/{identifier}"

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

        return Success(response.text)

    def fetch_languages(self, identifier: str) -> Result[int, FetchError]:
        """Fetch the number of language editions for a page.

        Args:
            identifier: Wikipedia page title.

        Returns:
            Result containing language count or FetchError.
        """
        # Use the mobile-sections endpoint which includes language count
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": identifier.replace("_", " "),
            "prop": "langlinks",
            "lllimit": "500",
            "format": "json",
        }

        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
        except requests.RequestException as e:
            return Failure(
                ApiError(
                    message=f"Request failed: {e}",
                    identifier=identifier,
                    status_code=None,
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
            pages = data.get("query", {}).get("pages", {})

            # Get the first page (there should only be one)
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    return Failure(
                        PersonNotFoundError(
                            message=f"Page not found: {identifier}",
                            identifier=identifier,
                        )
                    )
                langlinks = page_data.get("langlinks", [])
                # Add 1 for English
                return Success(len(langlinks) + 1)

            return Success(1)  # Default to 1 (English only)

        except (ValueError, KeyError) as e:
            return Failure(
                ParseError(
                    message=f"Failed to parse response: {e}",
                    identifier=identifier,
                )
            )
