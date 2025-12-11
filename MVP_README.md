# VisBets MVP - No ML Data Explorer

A React Native (Expo) mobile app for NBA player statistics and sportsbook line analysis using **simple data manipulation only** (no machine learning).

## Overview

This MVP focuses on delivering a clean, data-driven experience for sports bettors and NBA fans by:
- Fetching NBA player stats and game data
- Displaying sportsbook lines from platforms like PrizePicks
- Computing simple derived metrics (rolling averages, deltas vs lines)
- Presenting insights in tappable, mobile-friendly views

**No ML models are used.** All insights come from deterministic arithmetic and aggregation.

---

## Architecture

### Frontend (React Native + Expo)
- **Framework:** React Native with Expo
- **Language:** TypeScript
- **State Management:** Zustand
- **Navigation:** React Navigation (Stack + Bottom Tabs)
- **Networking:** Axios
- **Styling:** React Native StyleSheet

**Key Screens:**
1. [DashboardScreen.tsx](frontend/src/screens/DashboardScreen.tsx) - Today's slate with player cards
2. [PlayerDetailScreenNew.tsx](frontend/src/screens/PlayerDetailScreenNew.tsx) - Player profile with tabs (Overview, Game Log)
3. [SettingsScreenNew.tsx](frontend/src/screens/SettingsScreenNew.tsx) - Basic settings

### Backend (FastAPI + PostgreSQL)
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Purpose:**
  - Ingest NBA data and sportsbook lines
  - Store in normalized tables
  - Compute derived metrics via SQL/Python
  - Serve REST endpoints

**No ML pipeline.** All calculations are transparent aggregations.

---

## Database Schema

### Core Tables

#### `players`
```sql
id, name, team, position, image_url, ...
```

#### `games`
```sql
id, date, home_team, away_team, status
```

#### `player_game_stats`
```sql
id, player_id, game_id, date, points, rebounds, assists, minutes
```

#### `sportsbook_lines`
```sql
id, player_id, date, market, line_value, book
```

See [backend/app/db/models.py](backend/app/db/models.py) for full schema.

---

## Derived Metrics

All "insights" are computed in [backend/app/services/metrics_service.py](backend/app/services/metrics_service.py):

For each player + market (e.g., points):
- `season_avg` - Average over all season games
- `last5_avg` - Average over last 5 games
- `last10_avg` - Average over last 10 games
- `delta_line_vs_season` - Line value minus season average
- `delta_line_vs_last5` - Line value minus last 5 average
- `pct_diff_line_vs_season` - Percentage difference from season avg
- `pct_diff_line_vs_last5` - Percentage difference from last 5 avg

**Markets supported:** points, rebounds, assists, PRA (points + rebounds + assists)

---

## Backend API Endpoints

### `GET /api/slate?date_str=YYYY-MM-DD`
Returns players with games on a specific date (defaults to today).

**Response:**
```json
{
  "date": "2025-12-07",
  "players": [
    {
      "player_id": 237,
      "name": "LeBron James",
      "team": "LAL",
      "opponent": "BOS",
      "markets": [
        {
          "market": "points",
          "line_value": 27.5,
          "season_avg": 26.1,
          "last5_avg": 29.3,
          "delta_line_vs_last5": -1.8,
          "delta_line_vs_season": 1.4
        }
      ]
    }
  ]
}
```

See [backend/app/routers/slate.py](backend/app/routers/slate.py)

### `GET /api/player/{player_id}`
Returns detailed player profile, averages, game logs, and current lines.

**Response includes:**
- Player profile (name, team, position, image)
- Season averages
- Rolling averages (last 5, last 10)
- Recent game logs
- Current sportsbook lines with deltas

See [backend/app/routers/player_detail.py](backend/app/routers/player_detail.py)

---

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- Expo CLI

### Backend Setup

1. Navigate to backend:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/visbets
   NBA_API_KEY=your_api_key
   ```

5. Initialize database:
   ```bash
   alembic upgrade head
   ```

6. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to frontend:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update API URL in [src/config.js](frontend/src/config.js):
   ```javascript
   API_URL: 'http://localhost:8000'  // or your backend URL
   ```

4. Start Expo:
   ```bash
   npm start
   ```

5. Run on device:
   - iOS: Press `i` or run `npm run ios`
   - Android: Press `a` or run `npm run android`

---

## Project Structure

```
Visbets_2.0.0/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   ├── models.py          # Database models
│   │   │   └── database.py        # DB connection
│   │   ├── routers/
│   │   │   ├── slate.py           # Daily slate endpoint
│   │   │   └── player_detail.py   # Player detail endpoint
│   │   ├── services/
│   │   │   └── metrics_service.py # Derived metrics logic
│   │   └── main.py                # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── DashboardScreen.tsx       # Today's slate
│   │   │   ├── PlayerDetailScreenNew.tsx # Player details
│   │   │   └── SettingsScreenNew.tsx     # Settings
│   │   ├── store/
│   │   │   └── usePlayerStore.ts         # Zustand state
│   │   ├── services/
│   │   │   └── api.ts                    # API client
│   │   └── navigation/
│   │       └── AppNavigatorMVP.tsx       # Navigation setup
│   └── package.json
└── MVP_README.md
```

---

## Key Features

### Dashboard Screen
- Date selector (default: today)
- Search bar for player names
- Filter chips: points, rebounds, assists, PRA
- Player cards showing:
  - Name, team, opponent
  - Markets with lines, averages, and deltas
  - Color-coded edge indicators (green = good, red = bad)

### Player Detail Screen
- **Header:** Name, team, position, image, favorite button
- **Overview Tab:**
  - Season averages (PPG, RPG, APG, PRA)
  - Last 5 and last 10 game averages
  - Current lines with deltas vs season and recent form
- **Game Log Tab:**
  - Recent 10 games with stats
  - Date, opponent, points, rebounds, assists, minutes

### Settings Screen
- Dark mode toggle
- Push notifications toggle
- Account/subscription stubs
- Favorite players count
- About section

---

## Data Flow

1. **Backend fetches** NBA game/player data from external APIs
2. **Backend computes** rolling averages and deltas using [MetricsService](backend/app/services/metrics_service.py)
3. **Frontend calls** `/api/slate` or `/api/player/{id}` via [api.ts](frontend/src/services/api.ts)
4. **Zustand store** manages state in [usePlayerStore.ts](frontend/src/store/usePlayerStore.ts)
5. **Screens render** data with color-coded insights

---

## MVP Acceptance Criteria

- ✅ User can open the app and see today's slate of players
- ✅ User can tap a player to see detailed stats and game logs
- ✅ User can see sportsbook lines with delta calculations vs averages
- ✅ No machine learning or training pipeline used
- ✅ All data manipulation is simple, deterministic aggregation

---

## Next Steps (Post-MVP)

- Add real NBA data ingestion (nba_api, BallDontLie, etc.)
- Implement sportsbook scraping or API integration
- Add authentication (Firebase, Supabase)
- Build data collection pipeline for historical stats
- Add charts/visualizations for trends
- Implement favorites sync across devices
- Add push notifications for favorite players

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React Native + Expo |
| State | Zustand |
| Navigation | React Navigation |
| Backend | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| API Client | Axios |
| Language | TypeScript (Frontend), Python (Backend) |

---

## Development Notes

- **No ML:** This MVP intentionally avoids machine learning to ship faster
- **Simple metrics:** All calculations are transparent averages and deltas
- **Modular design:** Easy to add ML layer later without major refactoring
- **Type safety:** TypeScript interfaces ensure data consistency
- **Mobile-first:** Optimized for iOS and Android via Expo

---

## Contributing

1. Clone the repository
2. Create a feature branch
3. Make changes following the existing architecture
4. Test on both iOS and Android
5. Submit a pull request

---

## License

MIT

---

## Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for sports bettors who want clean, data-driven insights.**
