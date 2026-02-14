"""Repository implementations for fetching person data."""

import re
from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from bs4 import BeautifulSoup
from returns.result import Failure, Result, Success

from bio_battle.data.cache import Cache
from bio_battle.data.pageviews_client import PageviewsClient
from bio_battle.data.wikipedia_client import WikipediaClient
from bio_battle.domain.entities import Subject
from bio_battle.domain.errors import FetchError, NotAPersonError


class SubjectRepository(ABC):
    """Abstract base class for subject repositories."""

    @abstractmethod
    def get_by_identifier(self, identifier: str) -> Result[Subject, FetchError]:
        """Fetch a subject by their identifier.

        Args:
            identifier: The unique identifier for the subject (e.g., Wikipedia page title).

        Returns:
            Result containing Subject or FetchError.
        """
        pass


# Backward compatibility alias
PersonRepository = SubjectRepository


class WikipediaSubjectRepository(SubjectRepository):
    """Repository for fetching subject data from Wikipedia."""

    def __init__(
        self,
        wikipedia_client: WikipediaClient,
        pageviews_client: PageviewsClient,
        cache: Cache,
        cache_ttl: int = 86400,
    ) -> None:
        """Initialise the repository with dependencies.

        Args:
            wikipedia_client: Client for Wikipedia API calls.
            pageviews_client: Client for pageviews API calls.
            cache: Cache for storing fetched data.
            cache_ttl: Cache TTL in seconds (default 24 hours).
        """
        self._wikipedia_client = wikipedia_client
        self._pageviews_client = pageviews_client
        self._cache = cache
        self._cache_ttl = cache_ttl

    def get_by_identifier(self, identifier: str) -> Result[Subject, FetchError]:
        """Fetch a subject from Wikipedia by their page title.

        Args:
            identifier: Wikipedia page title (e.g., "Albert_Einstein").

        Returns:
            Result containing Subject or FetchError.
        """
        # Check cache first
        cache_key = identifier
        cached_data = self._cache.get(cache_key)
        if cached_data is not None:
            return Success(self._dict_to_subject(cached_data))

        # Fetch from Wikipedia API
        summary_result = self._wikipedia_client.fetch_summary(identifier)
        if isinstance(summary_result, Failure):
            return summary_result

        summary = summary_result.unwrap()

        # Fetch additional data in parallel (conceptually)
        languages_result = self._wikipedia_client.fetch_languages(identifier)
        pageviews_result = self._pageviews_client.fetch_monthly_views(identifier)
        html_result = self._wikipedia_client.fetch_page_html(identifier)

        # Extract languages count
        languages_count = 1  # Default to English only
        if isinstance(languages_result, Success):
            languages_count = languages_result.unwrap()

        # Extract page views
        page_views = 0
        if isinstance(pageviews_result, Success):
            page_views = pageviews_result.unwrap()

        # Extract article length and dates from HTML
        article_length = 0
        birth_date: date | None = None
        death_date: date | None = None

        if isinstance(html_result, Success):
            html_content = html_result.unwrap()
            article_length = self._calculate_article_length(html_content)
            birth_date, death_date = self._extract_dates(html_content)

        # Check if this is actually a person
        is_person, article_type = self._is_person(
            description=summary.description,
            extract=summary.extract,
            birth_date=birth_date,
        )
        if not is_person:
            return Failure(
                NotAPersonError(
                    message=f"'{summary.title}' is not a person ({article_type})",
                    identifier=identifier,
                    article_type=article_type,
                )
            )

        # Create Subject entity
        subject = Subject(
            identifier=identifier,
            name=summary.title,
            description=summary.description,
            extract=summary.extract,
            birth_date=birth_date,
            death_date=death_date,
            image_url=summary.thumbnail_url,
            page_views=page_views,
            article_length=article_length,
            languages_count=languages_count,
        )

        # Cache the result
        self._cache.set(cache_key, self._subject_to_dict(subject), ttl=self._cache_ttl)

        return Success(subject)

    def _calculate_article_length(self, html_content: str) -> int:
        """Calculate the word count of the article."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator=" ", strip=True)

        # Count words
        words = text.split()
        return len(words)

    def _extract_dates(
        self, html_content: str
    ) -> tuple[date | None, date | None]:
        """Extract birth and death dates from Wikipedia infobox."""
        soup = BeautifulSoup(html_content, "html.parser")

        birth_date: date | None = None
        death_date: date | None = None

        # Try to find dates in the HTML using infobox classes (most reliable)
        # Look for bday class (birthday)
        bday_elem = soup.find(class_="bday")
        if bday_elem:
            birth_date = self._parse_date_string(bday_elem.get_text())

        # Look for dday class (death day)
        dday_elem = soup.find(class_="dday")
        if dday_elem:
            death_date = self._parse_date_string(dday_elem.get_text())

        # Only use year range fallback if BOTH dates are missing
        # This prevents false death dates for living people
        # (year ranges like "(1963-1984)" often refer to career spans, not lifespans)
        if birth_date is None and death_date is None:
            dates = self._extract_dates_from_text(html_content)
            birth_date = dates[0]
            death_date = dates[1]

        return birth_date, death_date

    def _parse_date_string(self, date_str: str) -> date | None:
        """Parse a date string into a date object."""
        # Try ISO format first (YYYY-MM-DD)
        iso_pattern = r"(\d{4})-(\d{2})-(\d{2})"
        match = re.search(iso_pattern, date_str)
        if match:
            try:
                return date(
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                )
            except ValueError:
                pass

        return None

    def _extract_dates_from_text(
        self, html_content: str
    ) -> tuple[date | None, date | None]:
        """Extract birth/death years from text patterns like '(1879-1955)'."""
        # Pattern for year ranges in parentheses
        year_range_pattern = r"\((\d{4})\s*[-–]\s*(\d{4})\)"
        match = re.search(year_range_pattern, html_content)

        if match:
            try:
                birth_year = int(match.group(1))
                death_year = int(match.group(2))
                # Default to January 1st for year-only dates
                return date(birth_year, 1, 1), date(death_year, 1, 1)
            except ValueError:
                pass

        return None, None

    def _subject_to_dict(self, subject: Subject) -> dict[str, Any]:
        """Convert Subject entity to dictionary for caching."""
        return {
            "identifier": subject.identifier,
            "name": subject.name,
            "description": subject.description,
            "extract": subject.extract,
            "birth_date": subject.birth_date.isoformat() if subject.birth_date else None,
            "death_date": subject.death_date.isoformat() if subject.death_date else None,
            "image_url": subject.image_url,
            "page_views": subject.page_views,
            "article_length": subject.article_length,
            "languages_count": subject.languages_count,
        }

    def _is_person(
        self,
        description: str,
        extract: str,
        birth_date: date | None,
    ) -> tuple[bool, str]:
        """Check if the Wikipedia article is about a person.

        Args:
            description: Wikipedia short description.
            extract: Wikipedia extract text.
            birth_date: Parsed birth date if found.

        Returns:
            Tuple of (is_person, detected_type).
        """
        description_lower = description.lower()

        # Check for CLEAR non-person patterns first (these override birth date)
        # because films/albums can have dates in their infoboxes too
        clear_non_person_patterns = [
            (r"^\d{4} film\b", "film"),
            (r"^\d{4} .*\bfilm\b", "film"),
            (r"\bfilm by\b", "film"),
            (r"\bfilm directed by\b", "film"),
            (r"\bfilm starring\b", "film"),
            (r"^\d{4} .*\balbum\b", "album"),
            (r"\balbum by\b", "album"),
            (r"\bstudio album\b", "album"),
            (r"^\d{4} .*\bsong\b", "song"),
            (r"\bsong by\b", "song"),
            (r"\bsingle by\b", "song"),
            (r"\bprogramming language\b", "software"),
            (r"\bvideo game\b", "game"),
            (r"\btelevision series\b", "tv series"),
            (r"^\d{4} .*\bnovel\b", "book"),
            (r"\bnovel by\b", "book"),
        ]

        for pattern, article_type in clear_non_person_patterns:
            if re.search(pattern, description_lower):
                return False, article_type

        # Strong positive indicator: has birth date - almost certainly a person
        if birth_date is not None:
            return True, "person"

        # Check for person-like description patterns
        # e.g., "American actor", "British politician", "German physicist"
        person_patterns = [
            r"\b(actor|actress|singer|musician|artist|writer|author|politician|"
            r"scientist|physicist|chemist|biologist|mathematician|philosopher|"
            r"athlete|footballer|basketball player|tennis player|boxer|"
            r"director|producer|composer|poet|journalist|historian|"
            r"businessman|businesswoman|entrepreneur|inventor|engineer|"
            r"king|queen|emperor|empress|president|prime minister|monarch|"
            r"general|admiral|soldier|military officer|"
            r"activist|revolutionary|leader|founder|pioneer|explorer|"
            r"painter|sculptor|architect|photographer|designer|"
            r"chef|model|comedian|entertainer|presenter|"
            r"bishop|priest|pope|rabbi|imam|monk|saint|"
            r"lawyer|judge|doctor|physician|surgeon|psychologist|"
            r"academic|professor|scholar|educator|teacher|"
            r"novelist|playwright|screenwriter|songwriter|rapper|"
            r"dancer|choreographer|magician|illusionist|"
            r"astronaut|cosmonaut|pilot|racing driver|"
            r"criminal|gangster|serial killer|spy|"
            r"pharaoh|sultan|tsar|czar|duke|duchess|prince|princess)\b",
        ]

        for pattern in person_patterns:
            if re.search(pattern, description_lower):
                return True, "person"

        # Check extract for biographical language
        extract_lower = extract.lower()
        bio_indicators = [
            "was born",
            "is a former",
            "is an american",
            "is a british",
            "is an english",
            "was an american",
            "was a british",
            "was an english",
            "was a german",
            "was a french",
            "is a canadian",
            "was a canadian",
            "is an australian",
            "was an australian",
        ]

        for indicator in bio_indicators:
            if indicator in extract_lower:
                return True, "person"

        # Additional non-person patterns (less certain, only checked if no person indicators)
        additional_non_person_patterns = [
            (r"\brock band\b", "band"),
            (r"\bmusical group\b", "band"),
            (r"\bband formed\b", "band"),
            (r"\bmultinational.*\bcompany\b", "company"),
            (r"\bcorporation\b", "company"),
            (r"\bcity in\b", "place"),
            (r"\btown in\b", "place"),
            (r"\bvillage in\b", "place"),
            (r"\bcountry in\b", "place"),
            (r"\briver in\b", "place"),
            (r"\bmountain in\b", "place"),
            (r"\bspecies of\b", "species"),
            (r"\bgenus of\b", "species"),
        ]

        for pattern, article_type in additional_non_person_patterns:
            if re.search(pattern, description_lower):
                return False, article_type

        # Default: if no clear indicators either way, assume it might be a person
        # (better to include than exclude)
        return True, "person"

    def _dict_to_subject(self, data: dict[str, Any]) -> Subject:
        """Convert dictionary to Subject entity."""
        birth_date = None
        if data.get("birth_date"):
            birth_date = date.fromisoformat(data["birth_date"])

        death_date = None
        if data.get("death_date"):
            death_date = date.fromisoformat(data["death_date"])

        return Subject(
            identifier=data["identifier"],
            name=data["name"],
            description=data["description"],
            extract=data.get("extract", ""),
            birth_date=birth_date,
            death_date=death_date,
            image_url=data.get("image_url"),
            page_views=data.get("page_views", 0),
            article_length=data.get("article_length", 0),
            languages_count=data.get("languages_count", 1),
        )


# Backward compatibility alias
WikipediaPersonRepository = WikipediaSubjectRepository
