from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["mock"])


class MarketData(BaseModel):
    market: str
    line_value: float
    book: str
    season_avg: float
    last5_avg: float
    last10_avg: float
    delta_line_vs_season: float
    delta_line_vs_last5: float
    pct_diff_line_vs_season: float
    pct_diff_line_vs_last5: float


class SlatePlayer(BaseModel):
    player_id: int
    name: str
    team: str
    position: str
    opponent: str
    image_url: str
    markets: List[MarketData]


class SlateResponse(BaseModel):
    date: str
    players: List[SlatePlayer]


# Mock NBA players with real headshot URLs from ESPN
MOCK_PLAYERS = [
    {"id": 1, "name": "LeBron James", "team": "LAL", "pos": "F", "opponent": "DEN", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/1966.png"},
    {"id": 2, "name": "Stephen Curry", "team": "GSW", "pos": "G", "opponent": "PHX", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3975.png"},
    {"id": 3, "name": "Kevin Durant", "team": "PHX", "pos": "F", "opponent": "GSW", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3202.png"},
    {"id": 4, "name": "Giannis Antetokounmpo", "team": "MIL", "pos": "F", "opponent": "BOS", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3032977.png"},
    {"id": 5, "name": "Nikola Jokic", "team": "DEN", "pos": "C", "opponent": "LAL", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3112335.png"},
    {"id": 6, "name": "Luka Doncic", "team": "DAL", "pos": "G", "opponent": "LAC", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3945274.png"},
    {"id": 7, "name": "Joel Embiid", "team": "PHI", "pos": "C", "opponent": "MIA", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3059318.png"},
    {"id": 8, "name": "Jayson Tatum", "team": "BOS", "pos": "F", "opponent": "MIL", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/4065648.png"},
    {"id": 9, "name": "Damian Lillard", "team": "MIL", "pos": "G", "opponent": "BOS", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/6606.png"},
    {"id": 10, "name": "Anthony Davis", "team": "LAL", "pos": "F-C", "opponent": "DEN", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/6583.png"},
    {"id": 11, "name": "Kawhi Leonard", "team": "LAC", "pos": "F", "opponent": "DAL", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/6450.png"},
    {"id": 12, "name": "Jimmy Butler", "team": "MIA", "pos": "F", "opponent": "PHI", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/6430.png"},
    {"id": 13, "name": "Devin Booker", "team": "PHX", "pos": "G", "opponent": "GSW", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3136193.png"},
    {"id": 14, "name": "Ja Morant", "team": "MEM", "pos": "G", "opponent": "SAC", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/4279888.png"},
    {"id": 15, "name": "Trae Young", "team": "ATL", "pos": "G", "opponent": "CLE", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/4277905.png"},
    {"id": 16, "name": "Domantas Sabonis", "team": "SAC", "pos": "C-F", "opponent": "MEM", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3155942.png"},
    {"id": 17, "name": "Donovan Mitchell", "team": "CLE", "pos": "G", "opponent": "ATL", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3908809.png"},
    {"id": 18, "name": "Paul George", "team": "LAC", "pos": "F", "opponent": "DAL", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/4251.png"},
    {"id": 19, "name": "Karl-Anthony Towns", "team": "MIN", "pos": "C", "opponent": "OKC", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/3136195.png"},
    {"id": 20, "name": "Shai Gilgeous-Alexander", "team": "OKC", "pos": "G", "opponent": "MIN", "image": "https://a.espncdn.com/combiner/i?img=/i/headshots/nba/players/full/4278073.png"},
]


def generate_mock_market_data(market: str, base_avg: float) -> MarketData:
    """Generate realistic mock market data for a player"""
    # Add some variance to make it realistic
    season_avg = base_avg + random.uniform(-2, 2)
    last10_avg = season_avg + random.uniform(-3, 3)
    last5_avg = last10_avg + random.uniform(-2, 2)

    # Line is usually close to recent averages
    line_value = round(last5_avg + random.uniform(-1, 1), 1)

    # Calculate deltas
    delta_season = line_value - season_avg
    delta_last5 = line_value - last5_avg
    pct_season = (delta_season / season_avg * 100) if season_avg > 0 else 0
    pct_last5 = (delta_last5 / last5_avg * 100) if last5_avg > 0 else 0

    return MarketData(
        market=market,
        line_value=line_value,
        book="DraftKings",
        season_avg=round(season_avg, 1),
        last5_avg=round(last5_avg, 1),
        last10_avg=round(last10_avg, 1),
        delta_line_vs_season=round(delta_season, 1),
        delta_line_vs_last5=round(delta_last5, 1),
        pct_diff_line_vs_season=round(pct_season, 1),
        pct_diff_line_vs_last5=round(pct_last5, 1),
    )


@router.get("/mock/slate", response_model=SlateResponse)
async def get_mock_slate():
    """
    Get a mock daily slate with realistic NBA players and stats.
    Perfect for prototype/demo purposes.
    """
    slate_players = []

    for player in MOCK_PLAYERS:
        # Generate realistic base stats based on position
        if player["pos"] in ["G", "PG", "SG"]:
            points_base = random.uniform(18, 30)
            rebounds_base = random.uniform(3, 6)
            assists_base = random.uniform(5, 9)
        elif player["pos"] in ["F", "SF", "PF", "F-G"]:
            points_base = random.uniform(20, 28)
            rebounds_base = random.uniform(6, 10)
            assists_base = random.uniform(3, 6)
        else:  # Centers
            points_base = random.uniform(18, 26)
            rebounds_base = random.uniform(10, 14)
            assists_base = random.uniform(2, 5)

        markets = [
            generate_mock_market_data("points", points_base),
            generate_mock_market_data("rebounds", rebounds_base),
            generate_mock_market_data("assists", assists_base),
            generate_mock_market_data("pra", points_base + rebounds_base + assists_base),
        ]

        slate_players.append(SlatePlayer(
            player_id=player["id"],
            name=player["name"],
            team=player["team"],
            position=player["pos"],
            opponent=player["opponent"],
            image_url=player["image"],
            markets=markets
        ))

    return SlateResponse(
        date="2024-12-08",
        players=slate_players
    )


class PlayerProfile(BaseModel):
    id: int
    name: str
    team: str
    position: Optional[str]
    image_url: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    jersey_number: Optional[str]


class SeasonAverages(BaseModel):
    points: Optional[float]
    rebounds: Optional[float]
    assists: Optional[float]
    pra: Optional[float]


class RollingAverages(BaseModel):
    last5_points: Optional[float]
    last5_rebounds: Optional[float]
    last5_assists: Optional[float]
    last5_pra: Optional[float]
    last10_points: Optional[float]
    last10_rebounds: Optional[float]
    last10_assists: Optional[float]
    last10_pra: Optional[float]


class GameLog(BaseModel):
    date: str
    opponent: str
    points: int
    rebounds: int
    assists: int
    minutes: int
    pra: int


class PlayerDetailResponse(BaseModel):
    player: PlayerProfile
    season_averages: SeasonAverages
    rolling_averages: RollingAverages
    game_logs: List[GameLog]
    current_lines: List[MarketData]


@router.get("/mock/player/{player_id}", response_model=PlayerDetailResponse)
async def get_mock_player_detail(player_id: int):
    """
    Get mock player detail with game logs and stats.
    Perfect for prototype/demo purposes.
    """
    # Find the player
    player_data = next((p for p in MOCK_PLAYERS if p["id"] == player_id), None)
    if not player_data:
        raise HTTPException(status_code=404, detail="Player not found")

    # Generate realistic base stats based on position
    if player_data["pos"] in ["G", "PG", "SG"]:
        points_base = random.uniform(18, 30)
        rebounds_base = random.uniform(3, 6)
        assists_base = random.uniform(5, 9)
    elif player_data["pos"] in ["F", "SF", "PF", "F-G"]:
        points_base = random.uniform(20, 28)
        rebounds_base = random.uniform(6, 10)
        assists_base = random.uniform(3, 6)
    else:  # Centers
        points_base = random.uniform(18, 26)
        rebounds_base = random.uniform(10, 14)
        assists_base = random.uniform(2, 5)

    # Season averages
    season_avg = SeasonAverages(
        points=round(points_base, 1),
        rebounds=round(rebounds_base, 1),
        assists=round(assists_base, 1),
        pra=round(points_base + rebounds_base + assists_base, 1),
    )

    # Rolling averages with some variance
    rolling_avg = RollingAverages(
        last5_points=round(points_base + random.uniform(-3, 3), 1),
        last5_rebounds=round(rebounds_base + random.uniform(-2, 2), 1),
        last5_assists=round(assists_base + random.uniform(-2, 2), 1),
        last5_pra=round(points_base + rebounds_base + assists_base + random.uniform(-4, 4), 1),
        last10_points=round(points_base + random.uniform(-2, 2), 1),
        last10_rebounds=round(rebounds_base + random.uniform(-1, 1), 1),
        last10_assists=round(assists_base + random.uniform(-1, 1), 1),
        last10_pra=round(points_base + rebounds_base + assists_base + random.uniform(-3, 3), 1),
    )

    # Generate game logs for last 15 games
    game_logs = []
    opponents = ["PHX", "GSW", "LAL", "DEN", "MEM", "SAC", "DAL", "LAC", "UTA", "POR", "MIN", "OKC", "NOP", "SAS", "HOU"]
    for i in range(15):
        game_date = datetime.now() - timedelta(days=i * 2 + 1)
        pts = max(0, int(points_base + random.uniform(-8, 8)))
        reb = max(0, int(rebounds_base + random.uniform(-4, 4)))
        ast = max(0, int(assists_base + random.uniform(-4, 4)))
        mins = random.randint(28, 38)

        game_logs.append(GameLog(
            date=game_date.strftime("%Y-%m-%d"),
            opponent=opponents[i],
            points=pts,
            rebounds=reb,
            assists=ast,
            minutes=mins,
            pra=pts + reb + ast,
        ))

    # Current lines
    current_lines = [
        generate_mock_market_data("points", points_base),
        generate_mock_market_data("rebounds", rebounds_base),
        generate_mock_market_data("assists", assists_base),
        generate_mock_market_data("pra", points_base + rebounds_base + assists_base),
    ]

    return PlayerDetailResponse(
        player=PlayerProfile(
            id=player_data["id"],
            name=player_data["name"],
            team=player_data["team"],
            position=player_data["pos"],
            image_url=player_data["image"],
            height="6'8\"",
            weight="250 lbs",
            jersey_number=str(random.randint(0, 99)),
        ),
        season_averages=season_avg,
        rolling_averages=rolling_avg,
        game_logs=game_logs,
        current_lines=current_lines,
    )
