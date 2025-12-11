# VisBets MVP - Currently Running

## ✅ Active Services

### Backend API
- **Status:** Running
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Test Endpoints:**
  ```bash
  curl http://localhost:8000/api/slate
  curl http://localhost:8000/api/player/1
  ```

### Frontend (React Native + Expo)
- **Status:** Running on port 8083
- **Metro Bundler:** Active
- **To open app:**
  - Press `i` for iOS Simulator
  - Press `a` for Android Emulator
  - Scan QR code with Expo Go (physical device)

## 📊 Available Data

The backend is serving **mock data** for 5 NBA players:
1. LeBron James (LAL)
2. Stephen Curry (GSW)
3. Jayson Tatum (BOS)
4. Jimmy Butler (MIA)
5. Kevin Durant (PHX)

Each player has:
- Season averages
- Last 5 game averages
- Last 10 game averages
- Current sportsbook lines (points, rebounds, assists, PRA)
- 10 recent game logs
- Delta calculations vs lines

## 🎯 What to Test

1. **Dashboard Screen**
   - See all 5 players with markets
   - Search for players by name
   - Filter by market (tap chips)
   - Pull to refresh
   - Color-coded deltas (green = good, red = bad)

2. **Player Detail Screen**
   - Tap any player card
   - View player header with image
   - See Overview tab:
     - Season averages grid
     - Last 5 and Last 10 averages
     - Current lines with deltas
   - Switch to Game Log tab:
     - Last 10 games table
     - Stats per game

3. **Favorites**
   - Tap star button on player detail
   - Go to Favorites tab
   - See favorited players

4. **Settings**
   - Toggle dark mode
   - Toggle notifications
   - Check favorites count

## 🛠 Troubleshooting

### Backend not responding
```bash
# Check if running
curl http://localhost:8000

# Restart if needed
cd backend
source venv/bin/activate
python3 simple_server.py
```

### Frontend errors
```bash
# Reload Metro bundler
# Press 'r' in Expo terminal

# Or restart
cd frontend
npx expo start --clear --port 8083
```

### App won't load
1. Make sure both backend and frontend are running
2. Check that API_URL in `src/config.js` is `http://localhost:8000`
3. For physical devices, use your computer's IP instead of localhost

## 📝 Files Created

**Backend:**
- `simple_server.py` - Standalone FastAPI server with mock data
- `.env` - Updated with SQLite database URL

**Frontend:**
- `src/config/theme.ts` - Color theme configuration
- `src/screens/DashboardScreen.tsx` - Today's slate view
- `src/screens/PlayerDetailScreenNew.tsx` - Player detail with tabs
- `src/screens/SettingsScreenNew.tsx` - Settings screen
- `src/store/usePlayerStore.ts` - Zustand state management
- `src/services/api.ts` - API client
- `src/navigation/AppNavigatorMVP.tsx` - Navigation setup

## 🚀 Next Steps

1. **Test the full flow** - Make sure everything works end-to-end
2. **Replace mock data** - Integrate real NBA API when ready
3. **Add persistence** - Save favorites to AsyncStorage
4. **Deploy** - When ready to share

## 📚 Documentation

- [MVP_README.md](MVP_README.md) - Full project overview
- [QUICK_START.md](QUICK_START.md) - Setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built

---

**Enjoy testing your MVP! 🏀📊**
