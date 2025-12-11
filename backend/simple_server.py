"""
Simple standalone FastAPI server for testing the VisBets MVP frontend.
This bypasses all the configuration and dependency issues.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random

app = FastAPI(title="VisBets MVP - Simple Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
PLAYERS = [
    {"id": 1, "name": "LeBron James", "team": "LAL", "position": "F", "opponent": "BOS"},
    {"id": 2, "name": "Stephen Curry", "team": "GSW", "position": "G", "opponent": "PHX"},
    {"id": 3, "name": "Jayson Tatum", "team": "BOS", "position": "F", "opponent": "LAL"},
    {"id": 4, "name": "Jimmy Butler", "team": "MIA", "position": "F", "opponent": "NYK"},
    {"id": 5, "name": "Kevin Durant", "team": "PHX", "position": "F", "opponent": "GSW"},
]

PLAYER_STATS = {
    1: {"season_avg": 26.5, "last5_avg": 28.3, "last10_avg": 27.1},
    2: {"season_avg": 28.0, "last5_avg": 27.5, "last10_avg": 28.2},
    3: {"season_avg": 27.0, "last5_avg": 29.1, "last10_avg": 28.0},
    4: {"season_avg": 22.0, "last5_avg": 24.1, "last10_avg": 23.2},
    5: {"season_avg": 29.0, "last5_avg": 30.2, "last10_avg": 29.5},
}


def generate_market_data(player_id, market, base_avg):
    """Generate mock market data."""
    line = base_avg + random.uniform(-2, 2)
    season_avg = PLAYER_STATS[player_id]["season_avg"] if market == "points" else base_avg
    last5_avg = PLAYER_STATS[player_id]["last5_avg"] if market == "points" else base_avg * 1.1

    return {
        "market": market,
        "line_value": round(line, 1),
        "book": "PrizePicks",
        "season_avg": round(season_avg, 1),
        "last5_avg": round(last5_avg, 1),
        "last10_avg": round((season_avg + last5_avg) / 2, 1),
        "delta_line_vs_season": round(line - season_avg, 1),
        "delta_line_vs_last5": round(line - last5_avg, 1),
        "pct_diff_line_vs_season": round(((line - season_avg) / season_avg * 100), 1) if season_avg else None,
        "pct_diff_line_vs_last5": round(((line - last5_avg) / last5_avg * 100), 1) if last5_avg else None,
    }


@app.get("/")
def root():
    return {"message": "VisBets MVP API", "status": "running"}


@app.get("/api/slate")
def get_slate(date_str: str = None):
    """Get today's slate of players."""
    date = date_str or datetime.now().strftime("%Y-%m-%d")

    players_data = []
    for player in PLAYERS:
        markets = [
            generate_market_data(player["id"], "points", 25),
            generate_market_data(player["id"], "rebounds", 7),
            generate_market_data(player["id"], "assists", 6),
            generate_market_data(player["id"], "pra", 38),
        ]

        players_data.append({
            "player_id": player["id"],
            "name": player["name"],
            "team": player["team"],
            "position": player["position"],
            "opponent": player["opponent"],
            "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player['name'].replace(' ', '_')}.png",
            "markets": markets
        })

    return {
        "date": date,
        "players": players_data
    }


@app.get("/api/player/{player_id}")
def get_player_detail(player_id: int):
    """Get player detail."""
    player = next((p for p in PLAYERS if p["id"] == player_id), None)
    if not player:
        return {"error": "Player not found"}, 404

    # Generate game logs
    game_logs = []
    for i in range(10):
        date = (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d")
        points = PLAYER_STATS[player_id]["season_avg"] + random.uniform(-5, 5)
        rebounds = 7 + random.uniform(-2, 2)
        assists = 6 + random.uniform(-2, 2)

        game_logs.append({
            "date": date,
            "opponent": random.choice(["BOS", "LAL", "GSW", "PHX", "MIA"]),
            "points": round(points, 1),
            "rebounds": round(rebounds, 1),
            "assists": round(assists, 1),
            "minutes": round(random.uniform(30, 38), 1),
            "pra": round(points + rebounds + assists, 1),
        })

    # Current lines
    current_lines = [
        generate_market_data(player_id, "points", PLAYER_STATS[player_id]["season_avg"]),
        generate_market_data(player_id, "rebounds", 7),
        generate_market_data(player_id, "assists", 6),
        generate_market_data(player_id, "pra", 38),
    ]

    return {
        "player": {
            "id": player_id,
            "name": player["name"],
            "team": player["team"],
            "position": player["position"],
            "image_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player['name'].replace(' ', '_')}.png",
            "height": "6-9",
            "weight": "250",
            "jersey_number": str(player_id * 10),
        },
        "season_averages": {
            "points": PLAYER_STATS[player_id]["season_avg"],
            "rebounds": 7.5,
            "assists": 6.2,
            "pra": PLAYER_STATS[player_id]["season_avg"] + 13.7,
        },
        "rolling_averages": {
            "last5_points": PLAYER_STATS[player_id]["last5_avg"],
            "last5_rebounds": 7.8,
            "last5_assists": 6.5,
            "last5_pra": PLAYER_STATS[player_id]["last5_avg"] + 14.3,
            "last10_points": PLAYER_STATS[player_id]["last10_avg"],
            "last10_rebounds": 7.6,
            "last10_assists": 6.3,
            "last10_pra": PLAYER_STATS[player_id]["last10_avg"] + 13.9,
        },
        "game_logs": game_logs,
        "current_lines": current_lines,
    }


if __name__ == "__main__":
    import uvicorn
    print("🏀 Starting VisBets MVP Simple Server on http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🎯 Test slate: http://localhost:8000/api/slate")
    uvicorn.run(app, host="0.0.0.0", port=8000)
