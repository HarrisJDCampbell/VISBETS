# VisBets Database Implementation

This document explains the database implementation for VisBets, which is designed to minimize API calls to RapidAPI's NBA API.

## Architecture

The database implementation consists of the following components:

1. **SQLite Database**: A local database that stores player data, team data, player statistics, and cached API responses.
2. **SQLAlchemy ORM**: Used for database operations and object-relational mapping.
3. **Repository Pattern**: Used to abstract database operations and provide clean interfaces.
4. **Cache Layer**: Used to cache API responses to minimize API calls.

## Directory Structure

```
backend/app/db/
├── __init__.py           # Initializes the database
├── database.py           # Database connection and setup
├── models.py             # SQLAlchemy models
├── repositories.py       # Data access repositories
├── service.py            # Service layer for business logic
└── init_script.py        # Script to initialize database with data
```

## Models

The database has the following models:

- **Team**: Stores NBA team information
- **Player**: Stores player information with references to their team
- **PlayerStats**: Stores player statistics for a specific season
- **ApiCache**: Stores cached API responses with expiry timestamps

## How It Works

1. **API Request Flow**:
   - When an API request is made, the system first checks if the data is available in the database.
   - If the data is in the database, it's returned immediately without making an API call.
   - If not, the system makes an API call, stores the result in the database, and returns it.

2. **Database Initialization**:
   - `/init-db` endpoint can be used to initialize the database with data from the NBA API.
   - This process fetches teams, players, and player statistics.
   - For testing purposes, the initialization fetches a subset of the data.

3. **Cache Management**:
   - API responses are cached in the database with an expiry time.
   - A background task runs periodically to clear expired cache entries.

## Endpoints

- **GET /teams**: Returns all NBA teams from the database. If not available, fetches from the API.
- **GET /players**: Returns NBA players with pagination. Uses the database first.
- **GET /players/{player_id}**: Returns detailed information for a specific player.
- **GET /top-scorers**: Returns the top NBA scorers with their stats and predictions.
- **GET /init-db**: Initializes the database with data from the NBA API.

## Usage

To initialize the database:

```bash
# Start the server
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Then make a request to initialize the database
curl http://localhost:8000/init-db
```

## Benefits

1. **Reduced API Calls**: Minimizes the number of API calls to stay within API rate limits.
2. **Faster Response Times**: Cached data is returned more quickly than making API calls.
3. **Offline Capability**: Basic functionality can work offline with cached data.
4. **Predictable Performance**: Consistent response times, not dependent on external API performance.

## Future Improvements

1. **Scheduled Updates**: Implement scheduled jobs to update data periodically.
2. **Selective Updates**: Update only data that has changed rather than all data.
3. **Data Versioning**: Add versioning to track changes in the data.
4. **Migration System**: Add a migration system for database schema changes.
5. **Replication**: Add support for database replication for high availability. 