#!/usr/bin/env python3
"""
VisBets Management CLI

This script provides commands for managing data ingestion from BallDontLie API.

Usage:
    python manage.py ingest_teams
    python manage.py ingest_players
    python manage.py ingest_games --season 2024
    python manage.py ingest_stats --season 2024
    python manage.py ingest_all --season 2024
"""

import sys
import argparse
import logging
from datetime import date, datetime
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.services.ingestion import IngestionService
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_session():
    """
    Create and return a database session.
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./visbets.db")
    # Convert async URL to sync URL for management scripts
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")

    engine = create_engine(database_url, echo=False)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def cmd_ingest_teams(args):
    """
    Ingest all NBA teams.
    """
    logger.info("=" * 60)
    logger.info("INGESTING TEAMS")
    logger.info("=" * 60)

    db = get_db_session()
    try:
        with IngestionService(db) as service:
            count = service.ingest_teams()
            logger.info(f"✅ Successfully ingested {count} teams")
    finally:
        db.close()


def cmd_ingest_players(args):
    """
    Ingest all NBA players.
    """
    logger.info("=" * 60)
    logger.info("INGESTING PLAYERS")
    logger.info("=" * 60)

    db = get_db_session()
    try:
        with IngestionService(db) as service:
            count = service.ingest_players()
            logger.info(f"✅ Successfully ingested {count} players")
    finally:
        db.close()


def cmd_ingest_games(args):
    """
    Ingest games for a specific season.
    """
    season = args.season
    logger.info("=" * 60)
    logger.info(f"INGESTING GAMES FOR SEASON {season}")
    logger.info("=" * 60)

    # Parse optional date filters
    start_date = None
    end_date = None

    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        logger.info(f"Start date filter: {start_date}")

    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        logger.info(f"End date filter: {end_date}")

    db = get_db_session()
    try:
        with IngestionService(db) as service:
            count = service.ingest_games(
                season=season,
                start_date=start_date,
                end_date=end_date,
                postseason=args.postseason
            )
            logger.info(f"✅ Successfully ingested {count} games")
    finally:
        db.close()


def cmd_ingest_stats(args):
    """
    Ingest player game stats for a specific season.
    """
    season = args.season
    logger.info("=" * 60)
    logger.info(f"INGESTING STATS FOR SEASON {season}")
    logger.info("=" * 60)

    # Parse optional date filters
    start_date = None
    end_date = None

    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        logger.info(f"Start date filter: {start_date}")

    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        logger.info(f"End date filter: {end_date}")

    db = get_db_session()
    try:
        with IngestionService(db) as service:
            count = service.ingest_stats(
                season=season,
                start_date=start_date,
                end_date=end_date,
                postseason=args.postseason
            )
            logger.info(f"✅ Successfully ingested {count} stat records")
    finally:
        db.close()


def cmd_ingest_all(args):
    """
    Run all ingestion steps in sequence.
    """
    season = args.season
    logger.info("=" * 60)
    logger.info(f"FULL INGESTION PIPELINE FOR SEASON {season}")
    logger.info("=" * 60)

    # Step 1: Teams
    logger.info("\n[1/4] Ingesting teams...")
    cmd_ingest_teams(args)

    # Step 2: Players
    logger.info("\n[2/4] Ingesting players...")
    cmd_ingest_players(args)

    # Step 3: Games
    logger.info("\n[3/4] Ingesting games...")
    cmd_ingest_games(args)

    # Step 4: Stats
    logger.info("\n[4/4] Ingesting stats...")
    cmd_ingest_stats(args)

    logger.info("\n" + "=" * 60)
    logger.info("✅ FULL INGESTION COMPLETE")
    logger.info("=" * 60)


def cmd_init_db(args):
    """
    Initialize the database (create tables).
    """
    logger.info("Initializing database...")

    database_url = os.getenv("DATABASE_URL", "sqlite:///./visbets.db")
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")

    engine = create_engine(database_url, echo=True)
    Base.metadata.create_all(bind=engine)

    logger.info("✅ Database initialized successfully")


def main():
    parser = argparse.ArgumentParser(
        description='VisBets Data Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python manage.py init_db

  # Ingest teams
  python manage.py ingest_teams

  # Ingest players
  python manage.py ingest_players

  # Ingest games for 2024 season
  python manage.py ingest_games --season 2024

  # Ingest games for date range
  python manage.py ingest_games --season 2024 --start-date 2024-10-01 --end-date 2024-12-31

  # Ingest playoff games
  python manage.py ingest_games --season 2024 --postseason

  # Ingest stats for 2024 season
  python manage.py ingest_stats --season 2024

  # Run full pipeline
  python manage.py ingest_all --season 2024
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # init_db command
    parser_init = subparsers.add_parser('init_db', help='Initialize database tables')
    parser_init.set_defaults(func=cmd_init_db)

    # ingest_teams command
    parser_teams = subparsers.add_parser('ingest_teams', help='Ingest all NBA teams')
    parser_teams.set_defaults(func=cmd_ingest_teams)

    # ingest_players command
    parser_players = subparsers.add_parser('ingest_players', help='Ingest all NBA players')
    parser_players.set_defaults(func=cmd_ingest_players)

    # ingest_games command
    parser_games = subparsers.add_parser('ingest_games', help='Ingest games for a season')
    parser_games.add_argument('--season', type=int, required=True, help='Season year (e.g., 2024)')
    parser_games.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser_games.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser_games.add_argument('--postseason', action='store_true', help='Include playoff games')
    parser_games.set_defaults(func=cmd_ingest_games)

    # ingest_stats command
    parser_stats = subparsers.add_parser('ingest_stats', help='Ingest player game stats for a season')
    parser_stats.add_argument('--season', type=int, required=True, help='Season year (e.g., 2024)')
    parser_stats.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser_stats.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser_stats.add_argument('--postseason', action='store_true', help='Include playoff stats')
    parser_stats.set_defaults(func=cmd_ingest_stats)

    # ingest_all command
    parser_all = subparsers.add_parser('ingest_all', help='Run full ingestion pipeline')
    parser_all.add_argument('--season', type=int, required=True, help='Season year (e.g., 2024)')
    parser_all.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser_all.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser_all.add_argument('--postseason', action='store_true', help='Include playoff data')
    parser_all.set_defaults(func=cmd_ingest_all)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run the command
    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
