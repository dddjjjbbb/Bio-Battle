"""Domain entities for Bio Battle."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Person:
    """Represents a person from Wikipedia."""

    identifier: str
    name: str
    description: str
    extract: str
    birth_date: date | None
    death_date: date | None
    image_url: str | None
    page_views: int
    article_length: int
    languages_count: int

    @property
    def age(self) -> int | None:
        """Calculate age (at death if deceased, current age if alive)."""
        if self.birth_date is None:
            return None

        end_date = self.death_date if self.death_date else date.today()
        age = end_date.year - self.birth_date.year

        # Adjust if birthday hasn't occurred yet this year
        if (end_date.month, end_date.day) < (
            self.birth_date.month,
            self.birth_date.day,
        ):
            age -= 1

        return age

    @property
    def name_length(self) -> int:
        """Return the length of the name in characters."""
        return len(self.name)

    @property
    def bio(self) -> str:
        """Return the best available bio text (extract or description)."""
        if self.extract and len(self.extract) > len(self.description):
            return self.extract
        return self.description


@dataclass(frozen=True)
class Score:
    """Represents a score for a single category."""

    raw_value: float
    bracket_score: int


@dataclass(frozen=True)
class Card:
    """Represents a completed card with person and scores."""

    person: Person
    scores: dict[str, Score]

    @property
    def total_score(self) -> int:
        """Calculate the total score across all categories."""
        return sum(score.bracket_score for score in self.scores.values())
