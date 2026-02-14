"""Domain entities for Bio Battle."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class EntityMode(Enum):
    """Mode for entity type."""

    PERSON = "person"


@dataclass(frozen=True)
class Subject:
    """Represents a Wikipedia biography subject."""

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
    mode: EntityMode = EntityMode.PERSON

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


# Backward compatibility alias
Person = Subject


@dataclass(frozen=True)
class Score:
    """Represents a score for a single category."""

    raw_value: float
    bracket_score: int


@dataclass(frozen=True)
class Card:
    """Represents a completed card with subject and scores."""

    subject: Subject
    scores: dict[str, Score]

    @property
    def person(self) -> Subject:
        """Backward compatibility alias for subject."""
        return self.subject

    @property
    def total_score(self) -> int:
        """Calculate the total score across all categories."""
        return sum(score.bracket_score for score in self.scores.values())
