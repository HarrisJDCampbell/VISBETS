# VisBets Analytics Transformation - Implementation Guide

## 🎨 What's Been Built

I've implemented the foundation for transforming VisBets into a black/green analytics dashboard. Here's everything that's ready:

### ✅ Completed Components

1. **Analytics Theme System** ([src/theme/analytics.ts](frontend/src/theme/analytics.ts))
   - Black + Neon Green color scheme
   - `#050608` background, `#00FF7F` primary accent
   - Complete typography, spacing, and shadow definitions
   - Helper functions: `getTrendColor()`, `formatTrendPct()`, `getTrendArrow()`

2. **Charting Library**
   - ✅ Installed `victory-native` and `react-native-svg`
   - Production-ready for Expo

3. **Chart Components** ([src/components/charts/](frontend/src/components/charts/))
   - `PlayerStatLineChart.tsx` - Full-featured line charts with:
     - Interactive tooltips
     - Projection overlays (dashed green line)
     - Grid lines and axes
     - Dark theme styling
   - `SparklineChart.tsx` - Compact charts for cards:
     - Auto-colored by trend direction
     - No axes (space-efficient)
     - Smooth curves

4. **Analytics Utilities** ([src/utils/analytics.ts](frontend/src/utils/analytics.ts))
   - `calculateProjectedStat()` - Weighted average projection (40% season, 30% last10, 30% last5)
   - `calculatePlayerProjections()` - All projections for a player
   - `calculatePlayerTrends()` - Trend percentages
   - `gameLogsToChartData()` - Convert API data to chart format
   - `gameLogsToSparkline()` - Convert to sparkline format

## 🚀 Next Steps: Complete Implementation

### Phase 1: Redesign PlayerDetailScreen

Create a new version with three clear sections:

```tsx
// frontend/src/screens/PlayerDetailAnalyticsScreen.tsx

import { PlayerStatLineChart } from '../components/charts/PlayerStatLineChart';
import { calculatePlayerProjections, calculatePlayerTrends, gameLogsToChartData } from '../utils/analytics';
import analyticsTheme from '../theme/analytics';

// Structure:
// 1. PAST Section - How they've played
//    - Stat toggle: [Points] [Rebounds] [Assists] [PRA]
//    - PlayerStatLineChart showing last 10-15 games
//
// 2. PRESENT Section - How they're playing now
//    - Trend cards comparing Season vs Last10 vs Last5
//    - Visual indicators: ↑ green, ↓ red, → gray
//
// 3. FUTURE Section - Simple projection
//    - Projected stat (weighted average)
//    - Breakdown showing the weights
```

**Key Features:**
- Segmented control to switch stats
- Animated transitions when changing stats
- Green glow on "heating up" metrics
- Red tint on "cooling off" metrics

### Phase 2: Upgrade DashboardScreen (Slate)

Transform into an analytics slate:

```tsx
// frontend/src/screens/DashboardAnalyticsScreen.tsx

// Structure:
// 1. Top Bar
//    - Date selector: [< Today >]
//    - Market chips: [Points] [Rebounds] [Assists] [PRA]
//
// 2. Player Cards (for each player in slate)
//    - Name, team, opponent
//    - SparklineChart of last 5 games
//    - Stats: Season avg | Last 5 avg
//    - Trend badge: "+12.3%" in green or "-5.2%" in red
//
// 3. Interactive Features
//    - Search bar
//    - Sort: "Trending Up" | "Trending Down" | "Season Avg"
//    - Filter by position
```

**Styling:**
- Cards with `analyticsTheme.colors.card` background
- Green glow shadow on high-trend players
- Subtle animations on filter/sort changes

### Phase 3: Create Shared Components

Build these reusable UI components:

```tsx
// frontend/src/components/analytics/TrendBadge.tsx
// Shows trend percentage with color and arrow

// frontend/src/components/analytics/StatCard.tsx
// Reusable card for displaying a single stat metric

// frontend/src/components/analytics/StatToggle.tsx
// Segmented control for switching between stats

// frontend/src/components/analytics/ProjectionCard.tsx
// Card showing projected performance with breakdown
```

### Phase 4: Wire Up Data Flow

Update API types to include trend data:

```typescript
// frontend/src/services/api.ts

// Add to SlatePlayer interface:
export interface SlatePlayer {
  // ... existing fields
  trend_pct_points?: number;
  trend_pct_rebounds?: number;
  trend_pct_assists?: number;
  trend_pct_pra?: number;
}

// The backend already has season_avg and last5_avg
// Calculate trends on the frontend using calculateTrendPct()
```

## 📊 Implementation Example

Here's how to use the components you now have:

```tsx
import React, { useState } from 'react';
import { View } from 'react-native';
import { PlayerStatLineChart } from '../components/charts/PlayerStatLineChart';
import { gameLogsToChartData, calculatePlayerProjections } from '../utils/analytics';
import analyticsTheme from '../theme/analytics';

const PlayerDetailExample = ({ playerData }) => {
  const [selectedStat, setSelectedStat] = useState<'points' | 'rebounds' | 'assists'>('points');

  // Convert game logs to chart data
  const chartData = gameLogsToChartData(playerData.game_logs, selectedStat);

  // Calculate projections
  const projections = calculatePlayerProjections(
    playerData.season_averages,
    playerData.rolling_averages
  );

  return (
    <View style={{ backgroundColor: analyticsTheme.colors.background }}>
      {/* Stat Toggle */}
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <TouchableOpacity
          onPress={() => setSelectedStat('points')}
          style={{
            backgroundColor: selectedStat === 'points'
              ? analyticsTheme.colors.primary
              : analyticsTheme.colors.card
          }}
        >
          <Text>Points</Text>
        </TouchableOpacity>
        {/* ... other stat toggles */}
      </View>

      {/* Chart */}
      <PlayerStatLineChart
        title={`${selectedStat.toUpperCase()} - Last 10 Games`}
        data={chartData}
        color={analyticsTheme.colors.chartLine}
      />

      {/* Projection */}
      <View style={styles.projectionCard}>
        <Text style={styles.projectionLabel}>Projected {selectedStat}</Text>
        <Text style={styles.projectionValue}>
          {projections[`projected${selectedStat}`]}
        </Text>
      </View>
    </View>
  );
};
```

## 🎨 Theme Usage

Apply the theme consistently:

```tsx
import analyticsTheme from '../theme/analytics';

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: analyticsTheme.colors.background,
  },
  card: {
    backgroundColor: analyticsTheme.colors.card,
    borderRadius: analyticsTheme.borderRadius.lg,
    padding: analyticsTheme.spacing.md,
    ...analyticsTheme.shadows.md,
  },
  title: {
    fontSize: analyticsTheme.typography.sizes.xl,
    fontWeight: analyticsTheme.typography.weights.bold,
    color: analyticsTheme.colors.text,
  },
  trendUp: {
    color: analyticsTheme.colors.success, // Green
  },
  trendDown: {
    color: analyticsTheme.colors.danger, // Red
  },
});
```

## 🔥 Quick Wins

Implement these first for immediate impact:

1. **Apply Black Theme to Existing Screens**
   ```tsx
   // In DashboardScreen.tsx, PlayerDetailScreen.tsx
   import analyticsTheme from '../theme/analytics';

   // Replace all background colors:
   backgroundColor: analyticsTheme.colors.background

   // Replace card colors:
   backgroundColor: analyticsTheme.colors.card

   // Replace text colors:
   color: analyticsTheme.colors.text
   ```

2. **Add Sparklines to Player Cards**
   ```tsx
   import { SparklineChart } from '../components/charts/SparklineChart';
   import { gameLogsToSparkline } from '../utils/analytics';

   // In player card rendering:
   const sparklineData = gameLogsToSparkline(player.recent_games, 'points', 5);

   <SparklineChart
     data={sparklineData}
     width={60}
     height={24}
     showTrend={true}
   />
   ```

3. **Add Trend Badges**
   ```tsx
   import { getTrendColor, formatTrendPct } from '../theme/analytics';
   import { calculateTrendPct } from '../utils/analytics';

   const trendPct = calculateTrendPct(player.last5_avg, player.season_avg);

   <Text style={{ color: getTrendColor(trendPct) }}>
     {formatTrendPct(trendPct)}
   </Text>
   ```

## 📁 File Structure

```
frontend/src/
├── theme/
│   └── analytics.ts ✅ NEW - Black/green theme
├── components/
│   └── charts/
│       ├── PlayerStatLineChart.tsx ✅ NEW - Full charts
│       └── SparklineChart.tsx ✅ NEW - Mini charts
├── utils/
│   └── analytics.ts ✅ NEW - Projections & trends
├── screens/
│   ├── PlayerDetailAnalyticsScreen.tsx 🔄 TO CREATE
│   └── DashboardAnalyticsScreen.tsx 🔄 TO CREATE
└── services/
    └── api.ts ✅ EXISTING - Already has types
```

## 🎯 Expected Visual Result

### Player Detail Screen
```
┌─────────────────────────────────────┐
│  LEBRON JAMES                   LAL │
│  vs BOS                             │
├─────────────────────────────────────┤
│  [POINTS] REBOUNDS ASSISTS PRA      │ ← Stat toggle
├─────────────────────────────────────┤
│  ┌─── PAST: How He's Played ─────┐ │
│  │                                 │ │
│  │  30 ┤    •                      │ │  Line chart
│  │  25 ┤  •   •   •                │ │
│  │  20 ┤•       •     •            │ │
│  │     └──────────────────         │ │
│  │     12/1  12/3  12/5            │ │
│  └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│  ┌─── PRESENT: Recent Form ───────┐ │
│  │  Season: 26.1 ppg               │ │
│  │  Last 10: 27.0 ppg ↑            │ │  Trend cards
│  │  Last 5:  29.3 ppg ↑ +12.3%    │ │  (green)
│  └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│  ┌─── FUTURE: Projection ──────────┐ │
│  │  PROJECTED: 28.1 points         │ │  Big number
│  │  Based on:                      │ │
│  │  • 40% season avg (26.1)        │ │  Breakdown
│  │  • 30% last 10 (27.0)           │ │
│  │  • 30% last 5 (29.3)            │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Slate Screen
```
┌─────────────────────────────────────┐
│  [< 12/07/24 >]                     │ ← Date picker
│  [POINTS] Rebounds Assists PRA      │ ← Market filter
│  [Search players...]                │
├─────────────────────────────────────┤
│  ┌─ LEBRON JAMES ──────────────────┐│
│  │  LAL vs BOS                      ││
│  │  Season: 26.1  Last5: 29.3  ↑   ││
│  │  [mini sparkline chart]   +12.3%││ ← Green badge
│  └──────────────────────────────────┘│
│  ┌─ STEPHEN CURRY ─────────────────┐│
│  │  GSW vs PHX                      ││
│  │  Season: 28.0  Last5: 25.2  ↓   ││
│  │  [mini sparkline chart]   -10.0%││ ← Red badge
│  └──────────────────────────────────┘│
└─────────────────────────────────────┘
```

## 🚦 Priority Order

1. **CRITICAL** - Apply black/green theme to all existing screens
2. **HIGH** - Add sparklines to player cards on slate
3. **HIGH** - Add trend badges/percentages to slate
4. **MEDIUM** - Redesign PlayerDetailScreen with charts
5. **MEDIUM** - Add stat toggles and projections
6. **LOW** - Animations and micro-interactions

## 📚 Resources Created

- ✅ Theme system with all colors, spacing, typography
- ✅ Chart components ready to use
- ✅ Analytics utilities for all calculations
- ✅ TypeScript types already in place
- ✅ Victory Native installed and configured

## 🎬 Next Action

Start by creating `PlayerDetailAnalyticsScreen.tsx` following the structure above, then move to upgrading the Dashboard. All the building blocks are ready!

The transformation from a basic data viewer to an analytics powerhouse is now just about assembling these components!
