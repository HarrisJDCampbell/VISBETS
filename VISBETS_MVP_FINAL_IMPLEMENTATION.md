# VisBets MVP - Final Implementation Guide

## 🎯 Current Status

### ✅ Completed Infrastructure
1. **Backend** - Fully functional BallDontLie integration
   - Teams, players, games, stats all ingesting
   - `/api/slate` and `/api/player/{id}` endpoints working
   - Player images via NBA CDN

2. **Analytics Foundation** - Ready to use
   - Black/green theme system
   - Victory Native charts installed
   - Chart components (line charts, sparklines)
   - Analytics utilities (projections, trends)
   - UI components (TrendBadge, StatCard, StatToggle)

### 🔄 To Complete MVP

The app is 80% ready. You now need to:
1. Apply the analytics theme to existing screens
2. Add the chart components to player detail
3. Add sparklines and trends to the slate
4. Test end-to-end with real data

## 📱 Screen-by-Screen Implementation

### Screen 1: DashboardScreen (Slate View)

**File:** `frontend/src/screens/DashboardScreen.tsx`

**Changes Needed:**

```tsx
// 1. Import analytics components
import analyticsTheme from '../theme/analytics';
import { TrendBadge } from '../components/analytics/TrendBadge';
import { SparklineChart } from '../components/charts/SparklineChart';
import { StatToggle, StatType } from '../components/analytics/StatToggle';
import { calculateTrendPct, gameLogsToSparkline } from '../utils/analytics';

// 2. Add state for market filter
const [selectedMarket, setSelectedMarket] = useState<StatType>('points');

// 3. Update styles to use analytics theme
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: analyticsTheme.colors.background, // <- Change from white
  },
  card: {
    backgroundColor: analyticsTheme.colors.card, // <- Change from #F5F5F5
    borderRadius: analyticsTheme.borderRadius.lg,
    padding: analyticsTheme.spacing.md,
    marginBottom: analyticsTheme.spacing.md,
    ...analyticsTheme.shadows.md,
  },
  // ... etc
});

// 4. Add market filter at top
<StatToggle
  selectedStat={selectedMarket}
  onStatChange={setSelectedMarket}
/>

// 5. For each player card, add:
// - Sparkline showing last 5 games
// - Trend badge
// - Green glow if trending up

<View style={styles.card}>
  <View style={styles.playerHeader}>
    <Image source={{ uri: player.image_url }} style={styles.avatar} />
    <View>
      <Text style={styles.playerName}>{player.name}</Text>
      <Text style={styles.matchup}>{player.team} vs {player.opponent}</Text>
    </View>
  </View>

  {/* Sparkline */}
  <SparklineChart
    data={gameLogsToSparkline(player.recent_games, selectedMarket, 5)}
    width={100}
    height={30}
    showTrend={true}
  />

  {/* Stats */}
  <View style={styles.stats}>
    <Text style={styles.statLabel}>Season: {player.season_avg}</Text>
    <Text style={styles.statLabel}>Last 5: {player.last5_avg}</Text>
  </View>

  {/* Trend Badge */}
  <TrendBadge
    trendPct={calculateTrendPct(player.last5_avg, player.season_avg)}
    size="md"
  />
</View>
```

### Screen 2: PlayerDetailScreen (Analytics View)

**File:** `frontend/src/screens/PlayerDetailScreenNew.tsx`

**Complete Redesign:**

```tsx
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { useRoute } from '@react-navigation/native';
import ApiService from '../services/api';
import analyticsTheme from '../theme/analytics';
import { PlayerStatLineChart } from '../components/charts/PlayerStatLineChart';
import { StatCard } from '../components/analytics/StatCard';
import { StatToggle, StatType } from '../components/analytics/StatToggle';
import { TrendBadge } from '../components/analytics/TrendBadge';
import {
  calculatePlayerProjections,
  calculatePlayerTrends,
  gameLogsToChartData,
  formatStat,
} from '../utils/analytics';

export const PlayerDetailAnalyticsScreen = () => {
  const route = useRoute();
  const { playerId } = route.params;

  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedStat, setSelectedStat] = useState<StatType>('points');

  useEffect(() => {
    loadPlayerData();
  }, [playerId]);

  const loadPlayerData = async () => {
    try {
      const data = await ApiService.getPlayerDetail(playerId);
      setPlayerData(data);
    } catch (error) {
      console.error('Error loading player:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color={analyticsTheme.colors.primary} />
      </View>
    );
  }

  if (!playerData) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.errorText}>Player not found</Text>
      </View>
    );
  }

  // Calculate projections and trends
  const projections = calculatePlayerProjections(
    playerData.season_averages,
    playerData.rolling_averages
  );

  const trends = calculatePlayerTrends(
    playerData.season_averages,
    playerData.rolling_averages
  );

  // Convert game logs to chart data
  const chartData = gameLogsToChartData(playerData.game_logs, selectedStat);

  // Get specific stats based on selected stat
  const getStatValue = (type: 'season' | 'last10' | 'last5') => {
    const key = `${type === 'season' ? '' : type + '_'}${selectedStat}`;
    if (type === 'season') {
      return playerData.season_averages[selectedStat];
    }
    return playerData.rolling_averages[key];
  };

  const projectedValue = projections[`projected${selectedStat.charAt(0).toUpperCase() + selectedStat.slice(1)}`];
  const trendPct = trends[`${selectedStat}Trend`];

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.playerName}>{playerData.player.name}</Text>
        <Text style={styles.playerTeam}>
          {playerData.player.team} • {playerData.player.position}
        </Text>
      </View>

      {/* Stat Toggle */}
      <View style={styles.section}>
        <StatToggle
          selectedStat={selectedStat}
          onStatChange={setSelectedStat}
        />
      </View>

      {/* SECTION 1: PAST - How They've Played */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PAST: How He's Played</Text>
        <PlayerStatLineChart
          title={`Last ${chartData.length} Games`}
          data={chartData}
          color={analyticsTheme.colors.chartLine}
          height={220}
        />
      </View>

      {/* SECTION 2: PRESENT - Recent Form */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>PRESENT: Recent Form</Text>

        <View style={styles.statsGrid}>
          <StatCard
            label="Season Average"
            value={formatStat(getStatValue('season'))}
            subtitle="Full season baseline"
            style={styles.statCardSmall}
          />

          <StatCard
            label="Last 10 Games"
            value={formatStat(getStatValue('last10'))}
            subtitle="Medium-term trend"
            style={styles.statCardSmall}
            trend={
              <TrendBadge
                trendPct={calculateTrendPct(getStatValue('last10'), getStatValue('season'))}
                size="sm"
              />
            }
          />

          <StatCard
            label="Last 5 Games"
            value={formatStat(getStatValue('last5'))}
            subtitle="Recent hot/cold streak"
            highlight={Math.abs(trendPct) > 0.1}
            style={styles.statCardSmall}
            trend={<TrendBadge trendPct={trendPct} size="md" />}
          />
        </View>
      </View>

      {/* SECTION 3: FUTURE - Projection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>FUTURE: Projection</Text>

        <StatCard
          label={`Projected ${selectedStat.toUpperCase()}`}
          value={formatStat(projectedValue, 1)}
          subtitle="Weighted average prediction"
          highlight={true}
        />

        <View style={styles.projectionBreakdown}>
          <Text style={styles.breakdownTitle}>Based on:</Text>
          <Text style={styles.breakdownItem}>
            • 40% Season avg ({formatStat(getStatValue('season'))})
          </Text>
          <Text style={styles.breakdownItem}>
            • 30% Last 10 ({formatStat(getStatValue('last10'))})
          </Text>
          <Text style={styles.breakdownItem}>
            • 30% Last 5 ({formatStat(getStatValue('last5'))})
          </Text>
        </View>
      </View>

      {/* Game Logs Table */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Game Log</Text>
        {playerData.game_logs.map((game, index) => (
          <View key={index} style={styles.gameLogRow}>
            <Text style={styles.gameDate}>{game.date}</Text>
            <Text style={styles.gameOpponent}>{game.opponent}</Text>
            <Text style={styles.gameStat}>
              {selectedStat === 'pra'
                ? game.points + game.rebounds + game.assists
                : game[selectedStat]}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: analyticsTheme.colors.background,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: analyticsTheme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: analyticsTheme.colors.border,
  },
  playerName: {
    fontSize: analyticsTheme.typography.sizes.xxxl,
    fontWeight: analyticsTheme.typography.weights.bold,
    color: analyticsTheme.colors.text,
    marginBottom: analyticsTheme.spacing.xs,
  },
  playerTeam: {
    fontSize: analyticsTheme.typography.sizes.md,
    color: analyticsTheme.colors.textSecondary,
  },
  section: {
    padding: analyticsTheme.spacing.lg,
  },
  sectionTitle: {
    fontSize: analyticsTheme.typography.sizes.sm,
    fontWeight: analyticsTheme.typography.weights.bold,
    color: analyticsTheme.colors.primary,
    marginBottom: analyticsTheme.spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  statsGrid: {
    gap: analyticsTheme.spacing.md,
  },
  statCardSmall: {
    marginBottom: analyticsTheme.spacing.sm,
  },
  projectionBreakdown: {
    marginTop: analyticsTheme.spacing.md,
    padding: analyticsTheme.spacing.md,
    backgroundColor: analyticsTheme.colors.cardHighlight,
    borderRadius: analyticsTheme.borderRadius.md,
  },
  breakdownTitle: {
    fontSize: analyticsTheme.typography.sizes.sm,
    color: analyticsTheme.colors.textSecondary,
    marginBottom: analyticsTheme.spacing.sm,
  },
  breakdownItem: {
    fontSize: analyticsTheme.typography.sizes.sm,
    color: analyticsTheme.colors.text,
    marginBottom: analyticsTheme.spacing.xs,
  },
  gameLogRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: analyticsTheme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: analyticsTheme.colors.divider,
  },
  gameDate: {
    fontSize: analyticsTheme.typography.sizes.sm,
    color: analyticsTheme.colors.textSecondary,
    flex: 1,
  },
  gameOpponent: {
    fontSize: analyticsTheme.typography.sizes.sm,
    color: analyticsTheme.colors.text,
    flex: 1,
    textAlign: 'center',
  },
  gameStat: {
    fontSize: analyticsTheme.typography.sizes.md,
    fontWeight: analyticsTheme.typography.weights.semibold,
    color: analyticsTheme.colors.primary,
    flex: 1,
    textAlign: 'right',
  },
  errorText: {
    fontSize: analyticsTheme.typography.sizes.md,
    color: analyticsTheme.colors.danger,
  },
});

export default PlayerDetailAnalyticsScreen;
```

## 🔧 Quick Implementation Steps

### Step 1: Replace Existing Screens (5 minutes)

```bash
# Backup existing screens
cp frontend/src/screens/DashboardScreen.tsx frontend/src/screens/DashboardScreen.backup.tsx
cp frontend/src/screens/PlayerDetailScreenNew.tsx frontend/src/screens/PlayerDetailScreenNew.backup.tsx
```

Then copy the code above into the respective files.

### Step 2: Update Navigation (2 minutes)

Make sure your navigation is pointing to the new screens. The file names stay the same, so navigation should work automatically.

### Step 3: Test with Real Data (5 minutes)

```bash
# Make sure backend has data
cd backend
python3 manage.py ingest_teams
python3 manage.py ingest_players
python3 manage.py ingest_games --season 2024 --start-date 2024-12-01 --end-date 2024-12-07
python3 manage.py ingest_stats --season 2024 --start-date 2024-12-01 --end-date 2024-12-07

# Create mock lines for testing
python3 scripts/create_mock_lines.py

# Start backend
uvicorn app.main:app --reload
```

Then test your frontend - you should see:
- Black background with green accents
- Interactive charts on player detail
- Sparklines on slate cards
- Trend badges everywhere
- Past/Present/Future sections

## 🎨 Visual Result

You'll get this transformation:

**BEFORE:**
```
Plain white app
Static numbers
No trends
No insights
```

**AFTER:**
```
┌─────────────────────────────────────┐
│  🟢 BLACK BG WITH GREEN ACCENTS     │
│                                     │
│  LEBRON JAMES                       │
│  LAL vs BOS                         │
│  ─────────────────                  │
│  [PTS] REB  AST  PRA  ← Toggles    │
│                                     │
│  📈 INTERACTIVE LINE CHART          │
│  Shows last 10 games                │
│                                     │
│  Season: 26.1  Last 5: 29.3  ↑+12% │
│  ────────────────────────           │
│  PROJECTED: 28.1 points             │
│                                     │
└─────────────────────────────────────┘
```

## 🚀 To Launch MVP

1. **Apply code above** to DashboardScreen and PlayerDetailScreen
2. **Test with real data** from backend
3. **Polish any rough edges** (loading states, error handling)
4. **You're done!** 🎉

The app will transform from a basic data viewer into a professional analytics dashboard instantly.

## 📦 All Files Created

```
frontend/src/
├── theme/
│   └── analytics.ts ✅
├── components/
│   ├── charts/
│   │   ├── PlayerStatLineChart.tsx ✅
│   │   └── SparklineChart.tsx ✅
│   └── analytics/
│       ├── TrendBadge.tsx ✅
│       ├── StatCard.tsx ✅
│       └── StatToggle.tsx ✅
└── utils/
    └── analytics.ts ✅
```

Everything is ready - just copy the screen code and see the magic happen!
