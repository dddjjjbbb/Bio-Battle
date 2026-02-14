# Bio Battle

Ever wondered how Michael Jordan might fare in a completely ludicrous and impossible Top Trumps game against, say, Ada Lovelace, Carl Sagan, or Boudica? For some reason, I did, and thus, Bio Battle was born.

![Bio Battle Cards](cards.png)

## What Actually Is It?

A trading card generator that creates cards with fairly nonsensical rankings extrapolated from Wikipedia biographies.

Best not to take it too seriously, although Toni Morrison besting Chairman Mao with 28 points to 19 seems absolutely correct.

## What Does It Do?

Point it at a list of Wikipedia page titles and it will:

- Fetch data from Wikipedia for people
- Download images and apply Floyd-Steinberg dithering (or keep them in **full colour**)
- Calculate scores across four categories of dubious merit: Lifespan, Fame, Legacy, Reach (max 40 points)
- Render print-ready PDF cards (9 per A4 sheet)
- Generate **card backs** with QR codes linking to Wikipedia
- Serve a **REST API** for mobile apps
- Sort cards from highest to lowest score, because someone has to be on top
- Cache everything always!

### Scoring Categories

| Category | Description | Score |
|----------|-------------|-------|
| Lifespan | How long they lived (or have lived so far) | 1-10 |
| Fame | Monthly Wikipedia page views | 1-10 |
| Legacy | Article word count | 1-10 |
| Reach | Number of Wikipedia language editions | 1-10 |

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
# Generate cards
python -m bio_battle.main generate examples/people.txt -o output/cards.pdf

# Full colour images instead of dithered B&W
python -m bio_battle.main generate examples/people.txt --color

# Generate card backs with QR codes linking to Wikipedia
python -m bio_battle.main generate examples/people.txt --backs
```

Options:
- `--output, -o`: Output PDF path (default: `output/cards.pdf`)
- `--no-images`: Skip downloading images (faster, but less fun)
- `--no-cache`: Disable caching
- `--color`: Full colour images instead of dithered black and white
- `--backs`: Generate a separate PDF of card backs with QR codes

### Inspect a Single Subject

Curious about stats before committing to a card?

```bash
python -m bio_battle.main info "Zell Kravinsky"
```

### REST API

Serve the card generation engine as an API for mobile or web apps:

```bash
python -m bio_battle.main serve --port 8000
```

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/cards/{identifier}` | Get card data for a single subject |
| GET | `/api/search?q=keyword&limit=10` | Search Wikipedia for subjects |
| POST | `/api/deck` | Generate a deck from a list of identifiers |

Interactive API docs are available at `http://localhost:8000/docs` once the server is running.

Example:

```bash
# Get a single card as JSON
curl http://localhost:8000/api/cards/Albert_Einstein

# Search Wikipedia
curl "http://localhost:8000/api/search?q=scientists&limit=5"

# Generate a deck
curl -X POST http://localhost:8000/api/deck \
  -H "Content-Type: application/json" \
  -d '{"identifiers": ["Albert_Einstein", "Marie_Curie", "Isaac_Newton"]}'
```

## What's On a Card?

- **Header**: Name and nationality code(s) like [DE] or [PL/FR]
- **Portrait**: Heavily dithered black and white image (or full colour with `--color`)
- **Score Bars**: Four categories with visual bars. Scores out of 10
- **Vital Statistics**: Born, Died, Age, page views, word count, language editions
- **Bio**: The opening Wikipedia paragraph, truncated at sentence boundary
- **Total Score**: The number that settles all arguments!

Cards come with dashed cut lines, so, if you're so inclined, you can print them out and battle your friends. It's a very objective game, so it's bound to go well.

With `--backs`, you also get a separate PDF of card backs featuring a QR code that links to each subject's Wikipedia page, along with the project name and GitHub repo. The backs are mirrored so they align with the fronts for double-sided printing -- just print both PDFs and cut once.

## Project Structure

```
src/bio_battle/
    api/             # FastAPI REST API
    config/          # Settings and scoring brackets
    data/            # Wikipedia API clients and caching
    domain/          # Entities, scoring logic, card factory
    presentation/    # PDF rendering, image processing, layout, QR codes
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
- **qrcode**: QR code generation for card backs
- **fastapi**: REST API framework
- **uvicorn**: ASGI server for the API

## Licence

GNU General Public License (GPL)
