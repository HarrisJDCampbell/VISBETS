# BallDontLie API Integration Guide

## Overview

This document explains how to use the VisBets backend with real NBA data from the BallDontLie API (All-Star tier).

## Architecture

```
BallDontLie API → Ingestion Scripts → PostgreSQL/SQLite → FastAPI → React Native App
```

### Components

1. **BallDontLie API Client** (`app/services/balldontlie_client.py`)
   - Rate-limited HTTP client for BallDontLie API
   - Handles pagination automatically
   - Implements retry logic and error handling

2. **Ingestion Service** (`app/services/ingestion.py`)
   - Upserts teams, players, games, and stats into our database
   - Idempotent operations (safe to run multiple times)
   - Maps external API IDs to internal database IDs

3. **Database Models** (`app/db/models.py`)
   - SQLAlchemy models for: Team, Player, Game, PlayerGameStats, SportsbookLine
   - Unique constraints to prevent duplicates
   - Compatible with BallDontLie's data structure

4. **FastAPI Endpoints**
   - `GET /api/slate?date=YYYY-MM-DD` - Daily player slate with stats
   - `GET /api/player/{id}` - Player detail with game logs and averages

5. **Management CLI** (`manage.py`)
   - Command-line tool for running ingestion pipelines

## Setup

### 1. Environment Configuration

The `.env` file in the backend directory contains:

```bash
# BallDontLie API Configuration (All-Star Tier)
BALLDONTLIE_API_KEY=efb21c73-3403-47d8-b557-ac47d3027d40
BALLDONTLIE_BASE_URL=https://api.balldontlie.io/v1

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./visbets.db

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_DELAY=1.0
```

### 2. Initialize Database

```bash
cd backend
python manage.py init_db
```

This creates all necessary tables in your database.

## Data Ingestion

### Running the Full Pipeline

To ingest all data for the 2024 season:

```bash
python manage.py ingest_all --season 2024
```

This runs all steps in sequence:
1. Ingest teams (30 NBA teams)
2. Ingest players (~500 active players)
3. Ingest games for the season
4. Ingest player stats for all games

### Individual Ingestion Commands

**Ingest Teams:**
```bash
python manage.py ingest_teams
```

**Ingest Players:**
```bash
python manage.py ingest_players
```

**Ingest Games:**
```bash
# All games for 2024 season
python manage.py ingest_games --season 2024

# Games for specific date range
python manage.py ingest_games --season 2024 --start-date 2024-10-01 --end-date 2024-12-31

# Playoff games only
python manage.py ingest_games --season 2024 --postseason
```

**Ingest Player Stats:**
```bash
# All stats for 2024 season
python manage.py ingest_stats --season 2024

# Stats for specific date range
python manage.py ingest_stats --season 2024 --start-date 2024-10-01 --end-date 2024-12-31

# Playoff stats only
python manage.py ingest_stats --season 2024 --postseason
```

## Database Schema

### Teams
- `id` - Internal primary key
- `api_id` - BallDontLie team ID (unique)
- `name`, `full_name`, `abbreviation`, `city`
- `conference`, `division`

### Players
- `id` - Internal primary key
- `api_id` - BallDontLie player ID (unique)
- `first_name`, `last_name`, `full_name`
- `team_id` - Foreign key to teams
- `position`, `height`, `weight`

### Games
- `id` - Internal primary key
- `api_id` - BallDontLie game ID (unique)
- `date`, `season`, `postseason`
- `home_team_id`, `visitor_team_id` - Foreign keys to teams
- `home_team_score`, `visitor_team_score`
- `status` - "scheduled", "in_progress", "Final"

### PlayerGameStats
- `id` - Internal primary key
- `player_id`, `game_id` - Foreign keys (unique together)
- `date` - Game date
- Box score stats: `points`, `rebounds`, `assists`, `steals`, `blocks`, `turnovers`
- Shooting stats: `fgm`, `fga`, `fg3m`, `fg3a`, `ftm`, `fta`
- `minutes` - Minutes played (format: "35:24")

## API Endpoints

### GET /api/slate

Get the daily slate of players playing on a specific date.

**Query Parameters:**
- `date` (optional) - Date in YYYY-MM-DD format (defaults to today)

**Response:**
```json
{
  "date": "2025-12-07",
  "players": [
    {
      "player_id": 123,
      "name": "LeBron James",
      "team": "LAL",
      "position": "F",
      "opponent": "BOS",
      "image_url": "https://...",
      "markets": [
        {
          "market": "points",
          "line_value": 27.5,
          "book": "PrizePicks",
          "season_avg": 26.1,
          "last5_avg": 29.3,
          "last10_avg": 27.0,
          "delta_line_vs_season": 1.4,
          "delta_line_vs_last5": -1.8,
          "pct_diff_line_vs_season": 5.4,
          "pct_diff_line_vs_last5": -6.1
        }
      ]
    }
  ]
}
```

### GET /api/player/{player_id}

Get detailed information for a specific player.

**Response:**
```json
{
  "player": {
    "id": 123,
    "name": "LeBron James",
    "team": "LAL",
    "position": "F",
    "height": "6-9",
    "weight": "250"
  },
  "season_averages": {
    "points": 26.1,
    "rebounds": 7.8,
    "assists": 7.3,
    "pra": 41.2
  },
  "rolling_averages": {
    "last5_points": 29.3,
    "last5_rebounds": 8.1,
    "last5_assists": 6.9,
    "last5_pra": 44.3,
    "last10_points": 27.0,
    "last10_rebounds": 7.9,
    "last10_assists": 7.0,
    "last10_pra": 41.9
  },
  "game_logs": [
    {
      "date": "2025-12-01",
      "opponent": "BOS",
      "points": 30,
      "rebounds": 8,
      "assists": 7,
      "minutes": 35,
      "pra": 45
    }
  ],
  "current_lines": [...]
}
```

## Rate Limiting

The BallDontLie All-Star tier allows **60 requests per minute**. The client automatically:
- Throttles requests to stay within limits
- Sleeps between requests if needed
- Logs rate limiting activity

## Idempotent Ingestion

All ingestion functions are **idempotent** - they can be run multiple times safely:

- Uses SQLite `INSERT ... ON CONFLICT DO UPDATE` (upsert)
- For PostgreSQL, uses PostgreSQL's native upsert syntax
- Unique constraints prevent duplicates:
  - Teams: unique on `api_id`
  - Players: unique on `api_id`
  - Games: unique on `api_id`
  - PlayerGameStats: unique on `(player_id, game_id)`

This means you can:
- Re-run ingestion to update existing records
- Incrementally add new games as the season progresses
- Recover from partial failures by re-running

## Maintenance & Updates

### Daily Update Workflow

To keep data current during the season:

```bash
# Update today's games and stats
python manage.py ingest_games --season 2024 --start-date 2024-12-07 --end-date 2024-12-07
python manage.py ingest_stats --season 2024 --start-date 2024-12-07 --end-date 2024-12-07
```

### Cron Job Example

Add to your crontab to run daily at 6 AM:

```bash
0 6 * * * cd /path/to/backend && python manage.py ingest_games --season 2024 --start-date $(date +\%Y-\%m-\%d) && python manage.py ingest_stats --season 2024 --start-date $(date +\%Y-\%m-\%d)
```

## Troubleshooting

### Check API Key

```python
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('BALLDONTLIE_API_KEY'))"
```

### Test API Connection

```python
from app.services.balldontlie_client import get_client

with get_client() as client:
    teams = client.get_teams()
    print(f"Fetched {len(teams)} teams")
```

### View Logs

All ingestion scripts log their progress:
- Info level: Pagination progress, counts
- Debug level: Individual API requests
- Warning level: Missing references, skipped records

### Common Issues

1. **"Player/Team not found in database"**
   - Run `python manage.py ingest_teams` and `python manage.py ingest_players` first

2. **Rate limit errors**
   - The client auto-throttles, but if you hit limits, increase `API_RATE_LIMIT_DELAY` in `.env`

3. **Database locked (SQLite)**
   - SQLite has limited concurrency. For production, switch to PostgreSQL

## Migration to PostgreSQL

For production, update `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/visbets
```

Then run:

```bash
python manage.py init_db
```

## Next Steps

1. ✅ Set up BallDontLie integration (complete)
2. ✅ Create ingestion pipeline (complete)
3. ✅ API endpoints ready (complete)
4. 🔄 Run initial data ingestion
5. 🔄 Wire frontend to real API
6. 🔄 Add sportsbook line scraping/ingestion
7. 🔄 Set up automated daily updates

## Support

For issues or questions:
- Check BallDontLie API docs: https://docs.balldontlie.io
- Review error logs in ingestion output
- Verify database state with SQL queries
