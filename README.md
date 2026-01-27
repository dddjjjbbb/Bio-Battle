# Bio Battle

Ever wondered how Michael Jordan might fare in a completely ludicrous and impossible Top Trumps game against, say, Ada Lovelace, Carl Sagan, or Boudica? For some reason, I did, and thus, Bio Battle was born.

![Bio Battle Cards](docs/cards.png)

## What Actually Is It?

A trading card generator that creates cards with fairly nonsensical rankings extrapolated from Wikipedia biographies.

Best not to take it too seriously, although Toni Morrison besting Chairman Mao with 28 points to 19 seems absolutely correct.

## What Does It Do?

Point it at a list of Wikipedia page titles and it will:

- Fetch biographical data from Wikipedia (politely ignores anything that isn't a person, sorry things.)
- Download portrait images and apply Floyd-Steinberg dithering
- Calculate scores across four categories of dubious merit:
  - **Lifespan**: How long they lived (or have lived so far)
  - **Fame**: Monthly Wikipedia page views (the modern metric, so I'm told)
  - **Legacy**: Article word count (more words is a clear indicator of more significance)
  - **Reach**: Number of Wikipedia language editions (global appeal)
- Render print-ready PDF cards (9 per A4 sheet)
- Sort cards from highest to lowest score, because someone has to be on top
- Cache everything always!

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bio-battle.git
cd bio-battle

# Install dependencies using Poetry
poetry install

# Or using pip
pip install -e .
```

## Usage

### Generate Cards

Create a text file with Wikipedia page titles (one per line). Comments are allowed:

```text
# People
Toni Morrison
Patti Smith
David Lynch
Chairman Mao
Pharoah Sanders
Emma Goldman
```

Generate the PDF:

```bash
python -m bio_battle.main generate examples/people.txt -o output/cards.pdf
```

Options:
- `--output, -o`: Output PDF path (default: `output/cards.pdf`)
- `--no-images`: Skip downloading images (faster, but less fun)
- `--no-cache`: Disable caching

### Inspect a Single Person

Curious about someone's stats before committing to a card?

```bash
python -m bio_battle.main info "Zell Kravinsky"
```

## What's On a Card?

- **Header**: Name and nationality code(s) like [DE] or [PL/FR]
- **Portrait**: Heavily dithered black and white image (everyone looks distinguished)
- **Score Bars**: Four categories with visual bars. Scores out of 10
- **Vital Statistics**: Born, Died, Created date, page views, word count, language editions
- **Bio**: The opening Wikipedia paragraph, truncated at sentence boundary
- **Total Score**: The number that settles all arguments!

Cards come with dashed cut lines, so, if you're so inclined, you can print them out and battle your friends. It's a very objective game, so it's bound to go well.

## Project Structure

```
src/bio_battle/
    config/          # Settings and scoring brackets
    data/            # Wikipedia API clients and caching
    domain/          # Entities, scoring logic, card factory
    presentation/    # PDF rendering, image processing, layout
    main.py          # CLI entry point
```

## Development

### Running Tests

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=bio_battle --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Configuration

Settings live in `src/bio_battle/config/settings.py`:

- Page size (default: A4)
- Cards per sheet (default: 3x3)
- Image dimensions
- Cache TTL (default: 24 hours)
- API timeouts

Scoring brackets are defined in `src/bio_battle/config/scoring_config.py`.

## Dependencies

- **reportlab**: PDF generation
- **Pillow**: Image processing and dithering
- **requests**: HTTP client for Wikipedia API
- **beautifulsoup4**: HTML parsing for date extraction
- **pydantic**: Settings management
- **returns**: Result type for civilised error handling

## Licence

GNU General Public License (GPL)
