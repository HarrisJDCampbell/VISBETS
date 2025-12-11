"""
Sample data population script for VisBets MVP testing.
This creates mock data to test the full flow without external APIs.
"""

import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal
from app.db.models import Player, Team, Game, PlayerGameStats, SportsbookLine


# Sample NBA teams
TEAMS = [
    {"name": "Los Angeles Lakers", "abbreviation": "LAL", "city": "Los Angeles"},
    {"name": "Golden State Warriors", "abbreviation": "GSW", "city": "San Francisco"},
    {"name": "Boston Celtics", "abbreviation": "BOS", "city": "Boston"},
    {"name": "Miami Heat", "abbreviation": "MIA", "city": "Miami"},
    {"name": "Phoenix Suns", "abbreviation": "PHX", "city": "Phoenix"},
]

# Sample players
PLAYERS = [
    {
        "first_name": "LeBron",
        "last_name": "James",
        "full_name": "LeBron James",
        "position": "F",
        "jersey_number": "23",
        "team_abbr": "LAL",
        "avg_points": 26.5,
        "avg_rebounds": 8.0,
        "avg_assists": 7.5,
    },
    {
        "first_name": "Stephen",
        "last_name": "Curry",
        "full_name": "Stephen Curry",
        "position": "G",
        "jersey_number": "30",
        "team_abbr": "GSW",
        "avg_points": 28.0,
        "avg_rebounds": 5.0,
        "avg_assists": 6.5,
    },
    {
        "first_name": "Jayson",
        "last_name": "Tatum",
        "full_name": "Jayson Tatum",
        "position": "F",
        "jersey_number": "0",
        "team_abbr": "BOS",
        "avg_points": 27.0,
        "avg_rebounds": 8.5,
        "avg_assists": 4.5,
    },
    {
        "first_name": "Jimmy",
        "last_name": "Butler",
        "full_name": "Jimmy Butler",
        "position": "F",
        "jersey_number": "22",
        "team_abbr": "MIA",
        "avg_points": 22.0,
        "avg_rebounds": 5.5,
        "avg_assists": 5.0,
    },
    {
        "first_name": "Kevin",
        "last_name": "Durant",
        "full_name": "Kevin Durant",
        "position": "F",
        "jersey_number": "35",
        "team_abbr": "PHX",
        "avg_points": 29.0,
        "avg_rebounds": 7.0,
        "avg_assists": 5.5,
    },
]


def generate_player_stats(avg_points, avg_rebounds, avg_assists, variance=0.3):
    """Generate realistic random stats with variance."""
    points = max(0, avg_points + random.uniform(-avg_points * variance, avg_points * variance))
    rebounds = max(0, avg_rebounds + random.uniform(-avg_rebounds * variance, avg_rebounds * variance))
    assists = max(0, avg_assists + random.uniform(-avg_assists * variance, avg_assists * variance))
    minutes = random.uniform(28, 38)

    return {
        "points": round(points, 1),
        "rebounds": round(rebounds, 1),
        "assists": round(assists, 1),
        "minutes": round(minutes, 1),
    }


async def populate_database():
    """Populate database with sample data."""
    async with AsyncSessionLocal() as db:
        print("🏀 Starting database population...")

        # 1. Create teams
        print("\n1️⃣ Creating teams...")
        team_objs = {}
        for team_data in TEAMS:
            team = Team(
                name=team_data["name"],
                abbreviation=team_data["abbreviation"],
                city=team_data["city"],
                full_name=team_data["name"],
            )
            db.add(team)
            await db.flush()
            team_objs[team_data["abbreviation"]] = team
            print(f"   ✓ {team.name}")

        await db.commit()

        # 2. Create players
        print("\n2️⃣ Creating players...")
        player_objs = []
        for player_data in PLAYERS:
            team = team_objs[player_data["team_abbr"]]
            player = Player(
                first_name=player_data["first_name"],
                last_name=player_data["last_name"],
                full_name=player_data["full_name"],
                position=player_data["position"],
                jersey_number=player_data["jersey_number"],
                team_id=team.id,
                image_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_data['full_name'].replace(' ', '_')}.png",
            )
            db.add(player)
            await db.flush()
            player_objs.append((player, player_data))
            print(f"   ✓ {player.full_name} ({player_data['team_abbr']})")

        await db.commit()

        # 3. Create games
        print("\n3️⃣ Creating games...")
        games = []

        # Today's games
        today = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        game1 = Game(
            date=today,
            home_team="LAL",
            away_team="BOS",
            status="scheduled",
        )
        game2 = Game(
            date=today,
            home_team="GSW",
            away_team="PHX",
            status="scheduled",
        )
        game3 = Game(
            date=today,
            home_team="MIA",
            away_team="LAL",
            status="scheduled",
        )
        db.add_all([game1, game2, game3])
        await db.flush()
        games.extend([game1, game2, game3])

        # Past 15 games
        for i in range(1, 16):
            game_date = datetime.now() - timedelta(days=i)
            game = Game(
                date=game_date,
                home_team=random.choice(list(team_objs.keys())),
                away_team=random.choice(list(team_objs.keys())),
                status="finished",
            )
            db.add(game)
            await db.flush()
            games.append(game)

        await db.commit()
        print(f"   ✓ Created {len(games)} games")

        # 4. Create player game stats
        print("\n4️⃣ Creating player game stats...")
        stats_count = 0
        for player, player_data in player_objs:
            # Create stats for past games only
            past_games = [g for g in games if g.status == "finished"]
            for game in past_games[:12]:  # Last 12 games per player
                stats = generate_player_stats(
                    player_data["avg_points"],
                    player_data["avg_rebounds"],
                    player_data["avg_assists"],
                )
                player_game_stat = PlayerGameStats(
                    player_id=player.id,
                    game_id=game.id,
                    date=game.date,
                    **stats,
                )
                db.add(player_game_stat)
                stats_count += 1

        await db.commit()
        print(f"   ✓ Created {stats_count} player game stats")

        # 5. Create sportsbook lines for today's games
        print("\n5️⃣ Creating sportsbook lines...")
        lines_count = 0
        for player, player_data in player_objs:
            # Create lines for today
            markets = ["points", "rebounds", "assists", "pra"]
            for market in markets:
                if market == "points":
                    base = player_data["avg_points"]
                elif market == "rebounds":
                    base = player_data["avg_rebounds"]
                elif market == "assists":
                    base = player_data["avg_assists"]
                else:  # pra
                    base = player_data["avg_points"] + player_data["avg_rebounds"] + player_data["avg_assists"]

                # Add some variance to the line
                line_value = base + random.uniform(-2, 2)

                sportsbook_line = SportsbookLine(
                    player_id=player.id,
                    date=today,
                    market=market,
                    line_value=round(line_value, 1),
                    book="PrizePicks",
                )
                db.add(sportsbook_line)
                lines_count += 1

        await db.commit()
        print(f"   ✓ Created {lines_count} sportsbook lines")

        print("\n✅ Database population complete!")
        print(f"\nSummary:")
        print(f"  - Teams: {len(team_objs)}")
        print(f"  - Players: {len(player_objs)}")
        print(f"  - Games: {len(games)}")
        print(f"  - Player Stats: {stats_count}")
        print(f"  - Sportsbook Lines: {lines_count}")


if __name__ == "__main__":
    print("=" * 60)
    print("VisBets MVP - Sample Data Population")
    print("=" * 60)
    asyncio.run(populate_database())
