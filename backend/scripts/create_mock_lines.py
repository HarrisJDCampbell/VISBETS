#!/usr/bin/env python3
"""
Create mock sportsbook lines for testing.

This script creates sample sportsbook lines for players in games happening today.
Run this after ingesting players, games, and stats to test the full slate endpoint.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import random

from app.db.models import Base, Player, Game, PlayerGameStats, SportsbookLine

def main():
    # Get database connection
    database_url = os.getenv("DATABASE_URL", "sqlite:///./visbets.db")
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")

    engine = create_engine(database_url, echo=False)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("Creating mock sportsbook lines...")

    # Use 2024-12-07 since that's when we have game data
    today = datetime(2024, 12, 7)
    tomorrow = today + timedelta(days=1)

    # Get games for today
    games_stmt = select(Game).where(
        Game.date >= today,
        Game.date < tomorrow
    )
    games = db.execute(games_stmt).scalars().all()

    if not games:
        print(f"No games found for today ({today.date()})")
        print("Try a different date or ingest more games")
        return

    print(f"Found {len(games)} games for today")

    # Get all players (since we don't have stats for all games, just use any players)
    # In production, we'd match players to games, but for MVP testing we'll create lines for any players
    players_stmt = select(Player).limit(50)  # Get 50 players for testing
    players = db.execute(players_stmt).scalars().all()

    if not players:
        print("No players found in database")
        print("Run: python manage.py ingest_players")
        return

    print(f"Using {len(players)} players for mock lines")

    # Create lines for each player
    markets = ['points', 'rebounds', 'assists', 'pra']
    line_count = 0

    for player in players:
        # Use realistic baseline values for MVP testing
        # Points: 15-25, Rebounds: 4-10, Assists: 3-8
        base_points = random.uniform(15, 25)
        base_rebounds = random.uniform(4, 10)
        base_assists = random.uniform(3, 8)

        line_data = {
            'points': round(base_points, 1),
            'rebounds': round(base_rebounds, 1),
            'assists': round(base_assists, 1),
            'pra': round(base_points + base_rebounds + base_assists, 1),
        }

        for market in markets:
            line = SportsbookLine(
                player_id=player.id,
                date=today,
                market=market,
                line_value=line_data[market],
                book='PrizePicks'
            )
            db.add(line)
            line_count += 1

    db.commit()
    print(f"✅ Created {line_count} mock sportsbook lines for {len(players)} players")
    print(f"\nYou can now test the slate endpoint:")
    print(f"  curl 'http://localhost:8000/api/slate?date_str={today.date()}'")

if __name__ == '__main__':
    main()
