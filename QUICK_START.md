# VisBets MVP - Quick Start Guide

Get the app running in under 10 minutes!

## Prerequisites

- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL
- ✅ Expo CLI (`npm install -g expo-cli`)

---

## Step 1: Backend Setup (5 minutes)

### 1.1 Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Set Up Database

Create a PostgreSQL database:
```bash
createdb visbets
```

Or using PostgreSQL client:
```sql
CREATE DATABASE visbets;
```

### 1.3 Configure Environment

Create `.env` file in `backend/` directory:
```bash
# backend/.env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/visbets
NBA_API_KEY=your_api_key_here
```

Replace `your_user`, `your_password`, and `your_api_key_here` with your actual values.

### 1.4 Initialize Database

```bash
# Run migrations to create tables
alembic upgrade head

# Populate with sample data
python scripts/populate_sample_data.py
```

You should see:
```
✅ Database population complete!

Summary:
  - Teams: 5
  - Players: 5
  - Games: 18
  - Player Stats: 60
  - Sportsbook Lines: 20
```

### 1.5 Start Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's working:
- Open http://localhost:8000/docs
- You should see Swagger API documentation
- Test the `/api/slate` endpoint

---

## Step 2: Frontend Setup (3 minutes)

### 2.1 Install Dependencies

```bash
cd frontend
npm install
```

### 2.2 Configure API URL

The API URL is already set to `http://localhost:8000` in [src/config.js](frontend/src/config.js).

If your backend is on a different host:
```javascript
// frontend/src/config.js
const ENV = {
  dev: {
    API_URL: 'http://YOUR_IP:8000',  // Change this
  },
  // ...
};
```

### 2.3 Start Expo

```bash
npm start
```

This will open the Expo Dev Tools in your browser.

### 2.4 Run on Device

Choose your platform:

**iOS (Simulator):**
```bash
npm run ios
```
Or press `i` in the Expo terminal.

**Android (Emulator):**
```bash
npm run android
```
Or press `a` in the Expo terminal.

**Physical Device:**
- Install Expo Go app from App Store / Play Store
- Scan the QR code in your terminal

---

## Step 3: Test the App (2 minutes)

### Dashboard Screen
1. You should see "Today's Slate" with 5 players
2. Each player card shows multiple markets (POINTS, REBOUNDS, ASSISTS, PRA)
3. Try searching for "LeBron"
4. Try filtering by market (tap POINTS chip)

### Player Detail Screen
1. Tap on any player card
2. You should see:
   - Player header with image, team, position
   - Season averages
   - Last 5 and Last 10 game averages
   - Current lines with deltas
3. Switch to "Game Log" tab
4. You should see recent games with stats

### Favorites
1. Tap the "☆ Add to Favorites" button on player detail
2. Go to Favorites tab (bottom navigation)
3. Your favorite should appear

### Settings
1. Tap Settings tab (bottom navigation)
2. Toggle dark mode (should update theme)
3. Check your favorites count

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'app'`
```bash
# Make sure you're in the backend directory
cd backend
# And virtual environment is activated
source venv/bin/activate
```

**Problem:** Database connection error
```bash
# Check PostgreSQL is running
pg_ctl status

# Verify database exists
psql -l | grep visbets

# Check .env file has correct credentials
cat .env
```

**Problem:** Port 8000 already in use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --reload --port 8001
# Then update frontend/src/config.js
```

### Frontend Issues

**Problem:** `Unable to resolve module`
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm start -- --clear
```

**Problem:** Can't connect to backend
```bash
# If using physical device, use your computer's IP
# Find your IP: ipconfig (Windows) or ifconfig (Mac/Linux)
# Update frontend/src/config.js:
API_URL: 'http://192.168.1.XXX:8000'
```

**Problem:** Blank screen on app launch
```bash
# Check Metro bundler logs for errors
# Common issue: missing dependencies
npm install @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs
```

---

## Verifying Everything Works

### Backend Health Check

```bash
# Test slate endpoint
curl http://localhost:8000/api/slate

# Expected response:
{
  "date": "2025-12-07",
  "players": [
    {
      "player_id": 1,
      "name": "LeBron James",
      "team": "LAL",
      ...
    }
  ]
}
```

```bash
# Test player detail endpoint (use actual player ID from slate)
curl http://localhost:8000/api/player/1

# Expected response:
{
  "player": {
    "id": 1,
    "name": "LeBron James",
    ...
  },
  "season_averages": { ... },
  "rolling_averages": { ... },
  "game_logs": [ ... ]
}
```

### Frontend Health Check

1. Open app on device/simulator
2. Check console logs in Expo Dev Tools
3. You should see:
   ```
   [API Request] GET /slate
   [API Response] /slate - 200
   ```

---

## Next Steps

### Add Real NBA Data

Replace sample data with real NBA stats:
1. Sign up for [RapidAPI NBA API](https://rapidapi.com/api-sports/api/api-nba)
2. Update `NBA_API_KEY` in `.env`
3. Create data ingestion script (see `backend/services/data_collector.py`)

### Add Sportsbook Lines

Integrate real sportsbook data:
1. Use PrizePicks API (if available)
2. Or create a scraper (legal considerations apply)
3. Update `SportsbookLine` table daily

### Deploy to Production

Backend:
```bash
# Deploy to Railway, Heroku, or GCP
# Example with Railway:
railway login
railway init
railway up
```

Frontend:
```bash
# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android
```

---

## Useful Commands

### Backend

```bash
# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create migration
alembic revision --autogenerate -m "Your message"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Populate sample data
python scripts/populate_sample_data.py

# Run tests
pytest
```

### Frontend

```bash
# Start Expo
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android

# Clear cache
npm start -- --clear

# Type check
npx tsc --noEmit
```

---

## Project Structure Quick Reference

```
Visbets_2.0.0/
├── backend/
│   ├── app/
│   │   ├── db/models.py           # Database schema
│   │   ├── routers/slate.py       # Daily slate API
│   │   ├── routers/player_detail.py # Player detail API
│   │   └── services/metrics_service.py # Metrics logic
│   └── scripts/populate_sample_data.py # Sample data
├── frontend/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── DashboardScreen.tsx      # Main screen
│   │   │   ├── PlayerDetailScreenNew.tsx # Player details
│   │   │   └── SettingsScreenNew.tsx    # Settings
│   │   ├── store/usePlayerStore.ts      # State management
│   │   └── services/api.ts              # API client
│   └── App.tsx                          # Entry point
├── MVP_README.md                        # Full documentation
├── IMPLEMENTATION_SUMMARY.md            # What was built
└── QUICK_START.md                       # This file
```

---

## Support

If you run into issues:
1. Check the logs (backend terminal and Expo Dev Tools)
2. Refer to [MVP_README.md](MVP_README.md) for detailed documentation
3. Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
4. Open an issue on GitHub

---

**Happy Building! 🏀📊**
