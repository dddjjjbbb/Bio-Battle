"""Nationality extraction and country code mapping."""

import re

# Mapping of nationalities/demonyms to ISO country codes
# Using text codes since PDF fonts don't support emoji
NATIONALITY_TO_CODE: dict[str, str] = {
    # Major nationalities
    "American": "US",
    "British": "GB",
    "English": "GB",
    "Scottish": "GB",
    "Welsh": "GB",
    "French": "FR",
    "German": "DE",
    "Italian": "IT",
    "Spanish": "ES",
    "Portuguese": "PT",
    "Dutch": "NL",
    "Belgian": "BE",
    "Swiss": "CH",
    "Austrian": "AT",
    "Polish": "PL",
    "Russian": "RU",
    "Ukrainian": "UA",
    "Czech": "CZ",
    "Hungarian": "HU",
    "Romanian": "RO",
    "Greek": "GR",
    "Turkish": "TR",
    "Swedish": "SE",
    "Norwegian": "NO",
    "Danish": "DK",
    "Finnish": "FI",
    "Irish": "IE",
    # Asian
    "Chinese": "CN",
    "Japanese": "JP",
    "Korean": "KR",
    "South Korean": "KR",
    "Indian": "IN",
    "Pakistani": "PK",
    "Vietnamese": "VN",
    "Thai": "TH",
    "Filipino": "PH",
    "Indonesian": "ID",
    "Malaysian": "MY",
    "Singaporean": "SG",
    # Americas
    "Canadian": "CA",
    "Mexican": "MX",
    "Brazilian": "BR",
    "Argentine": "AR",
    "Argentinian": "AR",
    "Colombian": "CO",
    "Chilean": "CL",
    "Peruvian": "PE",
    "Venezuelan": "VE",
    "Cuban": "CU",
    # Oceania
    "Australian": "AU",
    "New Zealand": "NZ",
    # Africa
    "South African": "ZA",
    "Egyptian": "EG",
    "Nigerian": "NG",
    "Kenyan": "KE",
    # Middle East
    "Israeli": "IL",
    "Iranian": "IR",
    "Saudi": "SA",
    "Emirati": "AE",
    # Historical
    "Soviet": "RU",
    "Prussian": "DE",
    "Austro-Hungarian": "AT",
    "Yugoslav": "RS",
    "Czechoslovak": "CZ",
}


def extract_nationalities(text: str) -> list[str]:
    """Extract nationalities from a description text.

    Looks for nationality adjectives at the start of descriptions,
    handling hyphenated nationalities like "Polish-French".

    Args:
        text: Description text (e.g., "Polish-French physicist").

    Returns:
        List of nationalities found.
    """
    if not text:
        return []

    nationalities: list[str] = []

    # Pattern to match nationality words at start of text
    # Handles formats like "American", "Polish-French", "Polish and French"
    nationality_pattern = r"^([A-Z][a-z]+(?:[-\s](?:and\s)?[A-Z][a-z]+)*)"
    match = re.match(nationality_pattern, text)

    if match:
        nationality_str = match.group(1)
        # Split on hyphen or "and"
        parts = re.split(r"[-]|\s+and\s+", nationality_str)

        for part in parts:
            part = part.strip()
            if part in NATIONALITY_TO_CODE:
                nationalities.append(part)

    return nationalities


def get_country_code(nationality: str) -> str | None:
    """Get the ISO country code for a nationality.

    Args:
        nationality: Nationality adjective (e.g., "French").

    Returns:
        Country code (e.g., "FR") or None if not found.
    """
    return NATIONALITY_TO_CODE.get(nationality)


def get_flags_for_text(text: str) -> str:
    """Extract nationalities and return country codes.

    Args:
        text: Description text containing nationality info.

    Returns:
        String of country codes in brackets (e.g., "[PL/FR]" for "Polish-French").
    """
    nationalities = extract_nationalities(text)
    codes = []

    for nat in nationalities:
        code = get_country_code(nat)
        if code:
            codes.append(code)

    if codes:
        return "[" + "/".join(codes) + "]"
    return ""
