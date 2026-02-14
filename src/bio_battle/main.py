"""CLI entry point for Bio Battle card generator."""

import sys
from pathlib import Path

import click
from returns.result import Failure, Success

from bio_battle.config.scoring_config import get_scoring_config
from bio_battle.config.settings import get_settings
from bio_battle.data.cache import FileCache, MemoryCache
from bio_battle.data.pageviews_client import PageviewsClient
from bio_battle.data.repositories import WikipediaSubjectRepository
from bio_battle.data.wikipedia_client import WikipediaClient
from bio_battle.domain.card_factory import CardFactory
from bio_battle.domain.entities import Card
from bio_battle.domain.errors import NotAPersonError
from bio_battle.domain.scoring import ScoringService
from bio_battle.presentation.image_processor import ImageProcessor
from bio_battle.presentation.layout import SheetLayout
from bio_battle.presentation.pdf_renderer import PdfRenderer


def create_card_factory(use_file_cache: bool = True) -> CardFactory:
    """Create a CardFactory with all dependencies wired up."""
    settings = get_settings()

    # Set up cache
    cache = (
        FileCache(cache_dir=settings.cache_dir)
        if use_file_cache
        else MemoryCache()
    )

    # Set up API clients
    wikipedia_client = WikipediaClient(timeout=settings.wikipedia_api_timeout)
    pageviews_client = PageviewsClient(timeout=settings.wikipedia_api_timeout)

    # Set up repository
    repository = WikipediaSubjectRepository(
        wikipedia_client=wikipedia_client,
        pageviews_client=pageviews_client,
        cache=cache,
        cache_ttl=settings.cache_ttl_seconds,
    )

    # Set up scoring
    scoring_config = get_scoring_config()
    scoring_service = ScoringService(scoring_config)

    return CardFactory(
        subject_repository=repository,
        scoring_service=scoring_service,
    )


def parse_input_file(file_path: Path) -> list[str]:
    """Parse input file and return list of Wikipedia identifiers.

    Supports:
    - One identifier per line
    - Lines starting with # are comments
    - Empty lines are ignored
    - Full Wikipedia URLs are converted to page titles
    """
    identifiers = []
    content = file_path.read_text()

    for line in content.splitlines():
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Handle Wikipedia URLs
        if "wikipedia.org" in line:
            # Extract page title from URL
            # e.g., https://en.wikipedia.org/wiki/Albert_Einstein -> Albert_Einstein
            if "/wiki/" in line:
                identifier = line.split("/wiki/")[-1]
                # Remove any query parameters or anchors
                identifier = identifier.split("?")[0].split("#")[0]
                identifiers.append(identifier)
        else:
            # Treat as direct identifier
            identifiers.append(line)

    return identifiers


@click.group()
@click.version_option(version="0.1.0", prog_name="bio-battle")
def cli() -> None:
    """Bio Battle - Generate trading cards from Wikipedia biographies."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output PDF file path (default: output/cards.pdf)",
)
@click.option(
    "--no-images",
    is_flag=True,
    default=False,
    help="Skip downloading images (faster)",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable file caching",
)
@click.option(
    "--backs",
    is_flag=True,
    default=False,
    help="Generate card backs with QR codes linking to Wikipedia",
)
@click.option(
    "--color",
    is_flag=True,
    default=False,
    help="Generate cards with color images instead of dithered B&W",
)
def generate(
    input_file: Path,
    output: Path | None,
    no_images: bool,
    no_cache: bool,
    backs: bool,
    color: bool,
) -> None:
    """Generate Bio Battle cards from input file.

    INPUT_FILE should contain Wikipedia page titles or URLs, one per line.
    Lines starting with # are treated as comments.

    Example input file:
        # Famous scientists
        Albert_Einstein
        https://en.wikipedia.org/wiki/Marie_Curie
        Isaac_Newton
    """
    settings = get_settings()

    # Set up output path
    if output is None:
        output = settings.output_dir / "cards.pdf"

    click.echo(f"Reading identifiers from {input_file}...")
    identifiers = parse_input_file(input_file)

    if not identifiers:
        click.echo("No identifiers found in input file.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(identifiers)} identifiers")

    # Create card factory
    factory = create_card_factory(use_file_cache=not no_cache)

    # Generate cards
    click.echo("Fetching data from Wikipedia...")
    cards: list[Card] = []
    failed: list[str] = []
    skipped: list[tuple[str, str]] = []  # (identifier, reason)

    with click.progressbar(identifiers, label="Processing") as progress:
        for identifier in progress:
            result = factory.create_card(identifier)
            if isinstance(result, Success):
                cards.append(result.unwrap())
            else:
                error = result.failure()
                if isinstance(error, NotAPersonError):
                    skipped.append((identifier, error.article_type))
                else:
                    failed.append(identifier)

    click.echo(f"Successfully created {len(cards)} cards")
    if skipped:
        click.echo("Skipped (not a person):", err=True)
        for identifier, article_type in skipped:
            click.echo(f"  - {identifier} ({article_type})", err=True)
    if failed:
        click.echo(f"Failed to create cards for: {', '.join(failed)}", err=True)

    if not cards:
        click.echo("No cards to render.", err=True)
        sys.exit(1)

    # Download images if requested
    images = {}
    if not no_images:
        click.echo("Downloading images...")
        image_processor = ImageProcessor(settings)

        with click.progressbar(cards, label="Images") as progress:
            for card in progress:
                if card.person.image_url:
                    result = image_processor.process_image(
                        card.person.image_url, apply_dither=not color
                    )
                    if isinstance(result, Success) and result.unwrap() is not None:
                        images[card.person.identifier] = result.unwrap()

        click.echo(f"Downloaded {len(images)} images")

    # Sort cards by total score (highest first)
    cards.sort(key=lambda c: c.total_score, reverse=True)

    # Render PDF
    click.echo("Rendering PDF...")
    layout = SheetLayout.from_settings(settings)
    renderer = PdfRenderer(settings=settings, sheet_layout=layout)

    renderer.save_to_file(cards, output, images=images)

    click.echo(f"Saved PDF to {output}")

    if backs:
        backs_path = output.with_stem(output.stem + "_backs")
        click.echo("Rendering card backs with QR codes...")
        backs_bytes = renderer.render_card_backs(cards)
        backs_path.parent.mkdir(parents=True, exist_ok=True)
        backs_path.write_bytes(backs_bytes)
        click.echo(f"Saved card backs to {backs_path}")


@cli.command()
@click.argument("identifier")
def info(identifier: str) -> None:
    """Show information about a Wikipedia subject.

    IDENTIFIER can be a Wikipedia page title (e.g., Albert_Einstein)
    or a full Wikipedia URL.
    """
    # Handle URLs
    if "wikipedia.org" in identifier and "/wiki/" in identifier:
        identifier = identifier.split("/wiki/")[-1].split("?")[0].split("#")[0]

    factory = create_card_factory(use_file_cache=True)
    result = factory.create_card(identifier)

    if isinstance(result, Failure):
        click.echo(f"Failed to fetch data for: {identifier}", err=True)
        sys.exit(1)

    card = result.unwrap()
    subject = card.subject

    click.echo(f"\nName: {subject.name}")
    click.echo(f"Description: {subject.description}")

    if subject.birth_date:
        birth = subject.birth_date.strftime("%Y-%m-%d")
        if subject.death_date:
            death = subject.death_date.strftime("%Y-%m-%d")
            click.echo(f"Dates: {birth} - {death}")
        else:
            click.echo(f"Born: {birth}")

    click.echo("\nScores:")
    for category, score in card.scores.items():
        if score.raw_value < 0:
            # Unknown value (e.g., age for ancient figures)
            click.echo(f"  {category}: Unknown (score: {score.bracket_score})")
        else:
            click.echo(f"  {category}: {score.raw_value:.0f} (score: {score.bracket_score})")

    click.echo(f"\nTotal Score: {card.total_score}")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8000, help="Port to listen on")
def serve(host: str, port: int) -> None:
    """Start the Bio Battle REST API server.

    Runs a FastAPI server with endpoints for card generation,
    Wikipedia search, and deck building.

    Endpoints:
        GET  /api/health              - Health check
        GET  /api/cards/{identifier}  - Get card for a subject
        GET  /api/search?q=keyword    - Search Wikipedia
        POST /api/deck                - Generate deck from identifiers
    """
    import uvicorn

    from bio_battle.api.app import create_app

    app = create_app()
    click.echo(f"Starting Bio Battle API on {host}:{port}")
    click.echo("API docs: http://localhost:{port}/docs")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
