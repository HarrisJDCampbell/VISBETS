# VisBets 2.0.0

A React Native mobile app for NBA player statistics and predictions.

## Features

- **Featured Players**: View predictions for top NBA players (Curry, LeBron, Tatum)
- **Player Details**: Comprehensive player statistics with:
  - Season stats
  - Recent performance graphs
  - Multiple model predictions
  - Recent game logs
- **Favorites**: Save your favorite players for quick access
- **All Players**: Browse and search through all NBA players

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

3. Run on your preferred platform:
- iOS: Press `i` in the terminal or run `npm run ios`
- Android: Press `a` in the terminal or run `npm run android`

## API Requirements

The app expects a backend API running at `http://192.168.68.120:8000` with the following endpoints:

- `GET /players` - Get all players
- `GET /players/:id` - Get player details
- `GET /players/:id/details` - Get detailed player statistics

## Dependencies

- React Native
- Expo
- React Navigation
- React Native Chart Kit
- Axios
- AsyncStorage

## Development

The app is built with:
- TypeScript for type safety
- React Navigation for routing
- React Native Chart Kit for data visualization
- AsyncStorage for local data persistence

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 