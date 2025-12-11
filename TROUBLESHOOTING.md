# VisBets MVP - Troubleshooting Guide

Common issues and their solutions when running the VisBets MVP.

---

## iOS Build Issues

### Issue: `TurboModuleRegistry.getEnforcing(...): 'PlatformConstants' could not be found`

**Cause:** Native modules not properly linked or iOS folder needs to be rebuilt.

**Solution:**
```bash
cd frontend

# Step 1: Clean everything
rm -rf ios node_modules package-lock.json

# Step 2: Reinstall dependencies
npm install --legacy-peer-deps

# Step 3: Rebuild iOS native code
export LANG=en_US.UTF-8
npx expo prebuild --platform ios --clean

# Step 4: Install CocoaPods
cd ios && pod install && cd ..

# Step 5: Run the app
npx expo run:ios
```

### Issue: `Unicode Normalization not appropriate for ASCII-8BIT`

**Cause:** Terminal encoding not set correctly for CocoaPods.

**Solution:**
```bash
# Add to ~/.zshrc or ~/.bash_profile
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Then reload
source ~/.zshrc  # or source ~/.bash_profile

# Retry pod install
cd frontend/ios && pod install
```

### Issue: `pod install` fails with dependency conflicts

**Solution:**
```bash
cd frontend/ios

# Clear CocoaPods cache
rm -rf ~/Library/Caches/CocoaPods
rm -rf Pods
rm -rf ~/Library/Developer/Xcode/DerivedData/*
rm Podfile.lock

# Reinstall
pod deintegrate
pod install --repo-update
```

### Issue: Xcode build fails with module not found

**Solution:**
```bash
# In Xcode:
# 1. Product > Clean Build Folder (Cmd + Shift + K)
# 2. Close Xcode
# 3. Delete DerivedData
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# 4. Reopen Xcode and build again
```

---

## Android Build Issues

### Issue: Gradle build fails

**Solution:**
```bash
cd frontend/android

# Clean Gradle
./gradlew clean

# Clear cache
rm -rf .gradle
rm -rf app/build

# Rebuild
cd ..
npx expo run:android
```

### Issue: `ANDROID_HOME` not set

**Solution:**
```bash
# Add to ~/.zshrc or ~/.bash_profile
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Reload
source ~/.zshrc
```

---

## Backend Issues

### Issue: `ModuleNotFoundError: No module named 'app'`

**Cause:** Virtual environment not activated or not in correct directory.

**Solution:**
```bash
cd backend

# Activate venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Verify you're in backend directory
pwd  # Should show .../Visbets_2.0.0/backend

# Run server
uvicorn app.main:app --reload
```

### Issue: Database connection error

**Solutions:**

**1. PostgreSQL not running:**
```bash
# Mac (Homebrew)
brew services start postgresql

# Check status
brew services list

# Or manually start
pg_ctl -D /usr/local/var/postgres start
```

**2. Database doesn't exist:**
```bash
# Create database
createdb visbets

# Or using psql
psql postgres
CREATE DATABASE visbets;
\q
```

**3. Wrong credentials in .env:**
```bash
# Check .env file
cat backend/.env

# Should have:
DATABASE_URL=postgresql://username:password@localhost:5432/visbets

# Test connection
psql postgresql://username:password@localhost:5432/visbets
```

### Issue: Alembic migration fails

**Solution:**
```bash
cd backend

# Check current migration
alembic current

# Rollback to previous
alembic downgrade -1

# Or reset completely
alembic downgrade base

# Recreate migration
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Issue: Import errors in Python

**Solution:**
```bash
cd backend

# Reinstall dependencies
pip install -r requirements.txt

# Or create fresh venv
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Frontend Network Issues

### Issue: Can't connect to backend API

**Causes & Solutions:**

**1. Backend not running:**
```bash
# In backend terminal, you should see:
INFO:     Uvicorn running on http://0.0.0.0:8000

# If not, start it:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Wrong API URL:**
```javascript
// frontend/src/config.js
// For iOS Simulator
API_URL: 'http://localhost:8000'

// For Android Emulator
API_URL: 'http://10.0.2.2:8000'

// For Physical Device
API_URL: 'http://192.168.1.XXX:8000'  // Your computer's IP
```

**3. Find your local IP:**
```bash
# Mac
ipconfig getifaddr en0

# Linux
hostname -I

# Windows
ipconfig | findstr IPv4
```

**4. Firewall blocking connection:**
```bash
# Mac - Allow incoming connections
System Preferences > Security & Privacy > Firewall > Firewall Options
# Allow connections for uvicorn/Python

# Test connection from phone
# Open browser on phone
# Go to http://YOUR_IP:8000/docs
# Should see FastAPI Swagger docs
```

---

## Common Runtime Errors

### Issue: `Invariant Violation` or module errors

**Solution:**
```bash
cd frontend

# Clear Metro bundler cache
npx expo start --clear

# Or manually clear all caches
rm -rf node_modules
rm -rf .expo
rm package-lock.json
npm install --legacy-peer-deps
npx expo start --clear
```

### Issue: Red screen errors on app launch

**Steps to debug:**

1. **Read the error message carefully** - it usually tells you what's wrong
2. **Check Metro bundler logs** - errors appear in terminal running `expo start`
3. **Open Chrome debugger** - Shake device → "Debug" → Check console
4. **Check import paths** - Ensure all imports are correct

### Issue: Zustand store not updating

**Solution:**
```typescript
// Make sure you're destructuring correctly
const { slateData, setSlateData } = usePlayerStore();

// NOT
const slateData = usePlayerStore(state => state.slateData); // This won't re-render

// Use selective subscription for performance
const slateData = usePlayerStore(state => state.slateData);
```

### Issue: Navigation not working

**Check:**
1. Routes defined correctly in AppNavigatorMVP.tsx
2. Screen names match exactly (case-sensitive)
3. Params passed correctly: `navigation.navigate('PlayerDetail', { playerId: 123 })`

---

## Expo Specific Issues

### Issue: Expo Go app shows error

**Note:** This project uses **native modules** that don't work with Expo Go.

**Solution:**
```bash
# You MUST use development build
npx expo run:ios    # For iOS
npx expo run:android  # For Android

# NOT:
npx expo start  # Then scanning QR in Expo Go (won't work)
```

### Issue: `expo run:ios` command not found

**Solution:**
```bash
# Install Expo CLI globally
npm install -g expo-cli

# Or use npx
npx expo run:ios
```

---

## Data/API Issues

### Issue: No players showing on dashboard

**Possible causes:**

**1. No data in database:**
```bash
cd backend
python scripts/populate_sample_data.py
```

**2. Wrong date:**
```bash
# Check backend logs - what date is it querying?
# Sample data creates games for TODAY

# Or test with specific date
curl http://localhost:8000/api/slate?date_str=2025-12-07
```

**3. API returning empty array:**
```bash
# Check backend response
curl http://localhost:8000/api/slate

# Should return:
{
  "date": "2025-12-07",
  "players": [...]  # Should have players
}

# If empty, check database:
psql visbets
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM sportsbook_lines;
```

### Issue: Player detail shows "N/A" for all stats

**Cause:** No game stats in database for that player.

**Solution:**
```bash
cd backend

# Check if player has stats
psql visbets
SELECT * FROM player_game_stats WHERE player_id = 1;

# If empty, run population script
python scripts/populate_sample_data.py
```

---

## Performance Issues

### Issue: App is slow/laggy

**Solutions:**

1. **Enable Hermes engine** (should be default in Expo SDK 54+)
2. **Use production build:**
   ```bash
   npx expo run:ios --configuration Release
   ```
3. **Optimize FlatList:**
   - Add `removeClippedSubviews={true}`
   - Add `maxToRenderPerBatch={10}`
   - Add `windowSize={10}`

4. **Reduce re-renders:**
   ```typescript
   // Use React.memo for components
   const PlayerCard = React.memo(({ player }) => { ... });

   // Use useCallback for functions
   const handlePress = useCallback(() => { ... }, []);
   ```

---

## Getting Help

If you're still stuck:

1. **Check logs:**
   - Backend: Terminal running uvicorn
   - Frontend: Metro bundler terminal
   - Device: Expo Dev Tools → Console

2. **Enable debug mode:**
   ```typescript
   // In api.ts
   console.log('API Request:', config);
   console.log('API Response:', response.data);
   ```

3. **Test endpoints directly:**
   ```bash
   # Swagger UI
   http://localhost:8000/docs

   # Test with curl
   curl -v http://localhost:8000/api/slate
   ```

4. **Check versions:**
   ```bash
   # Node
   node --version  # Should be 18+

   # Python
   python --version  # Should be 3.11+

   # Expo
   npx expo --version

   # CocoaPods
   pod --version
   ```

5. **Create minimal reproduction:**
   - Comment out all code
   - Add back piece by piece
   - Find which part breaks

---

## Quick Reset (Nuclear Option)

If nothing works, complete clean reset:

```bash
# Backend
cd backend
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
dropdb visbets && createdb visbets
alembic upgrade head
python scripts/populate_sample_data.py
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
rm -rf node_modules package-lock.json ios android .expo
npm install --legacy-peer-deps
export LANG=en_US.UTF-8
npx expo prebuild --clean
cd ios && pod install && cd ..
npx expo run:ios
```

---

## Still Having Issues?

Open an issue on GitHub with:
- Error message (full stack trace)
- Steps to reproduce
- Environment details (OS, Node version, Python version)
- Logs from backend and frontend

**Good luck! 🏀**
