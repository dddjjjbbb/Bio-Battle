"""Domain error types for Bio Battle."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FetchError:
    """Base error for fetch operations."""

    message: str
    identifier: str


@dataclass(frozen=True)
class PersonNotFoundError(FetchError):
    """Error when a person cannot be found."""

    pass


@dataclass(frozen=True)
class ApiError(FetchError):
    """Error when an API call fails."""

    status_code: int | None = None


@dataclass(frozen=True)
class CacheError:
    """Error when cache operations fail."""

    message: str


@dataclass(frozen=True)
class ParseError(FetchError):
    """Error when parsing API response fails."""

    pass


@dataclass(frozen=True)
class NotAPersonError(FetchError):
    """Error when the Wikipedia article is not about a person."""

    article_type: str = "unknown"
