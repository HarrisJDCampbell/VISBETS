from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255))
    abbreviation = Column(String(5))
    city = Column(String(100))
    conference = Column(String(50))
    division = Column(String(50))
    logo_url = Column(String(255))
    api_id = Column(Integer, unique=True)  # Store the external API ID
    is_nba = Column(Boolean, default=True)
    
    # Relationship
    players = relationship("Player", back_populates="team", lazy="selectin")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255), nullable=False)
    position = Column(String(50))
    height = Column(String(10))
    weight = Column(String(10))
    jersey_number = Column(String(10))
    country = Column(String(100))
    college = Column(String(255))
    birth_date = Column(String(50))
    image_url = Column(String(255))
    api_id = Column(Integer, unique=True)  # Store the external API ID
    
    # Foreign keys
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    # Relationships
    team = relationship("Team", back_populates="players", lazy="selectin")
    stats = relationship("PlayerStats", back_populates="player", lazy="selectin")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlayerStats(Base):
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True)
    season = Column(String(10), nullable=False)
    points = Column(Float, default=0.0)
    assists = Column(Float, default=0.0)
    rebounds = Column(Float, default=0.0)
    steals = Column(Float, default=0.0)
    blocks = Column(Float, default=0.0)
    field_goal_percentage = Column(Float)
    three_point_percentage = Column(Float)
    free_throw_percentage = Column(Float)
    games_played = Column(Integer, default=0)
    minutes_played = Column(Float, default=0.0)
    
    # Store raw data as JSON for flexibility
    raw_data = Column(JSON)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey("players.id"))
    
    # Relationships
    player = relationship("Player", back_populates="stats", lazy="selectin")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, unique=True)  # BallDontLie game ID
    date = Column(DateTime, nullable=False)
    season = Column(Integer)  # e.g., 2024 for 2024-25 season
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    visitor_team_id = Column(Integer, ForeignKey("teams.id"))
    home_team_score = Column(Integer)
    visitor_team_score = Column(Integer)
    status = Column(String(50), default='scheduled')  # scheduled, in_progress, Final
    postseason = Column(Boolean, default=False)

    # Keep legacy fields for compatibility
    home_team = Column(String(100))  # abbreviation
    away_team = Column(String(100))  # abbreviation
    home_score = Column(Integer)
    away_score = Column(Integer)

    # Relationships
    player_game_stats = relationship("PlayerGameStats", back_populates="game", lazy="selectin")
    home_team_rel = relationship("Team", foreign_keys=[home_team_id], lazy="selectin")
    visitor_team_rel = relationship("Team", foreign_keys=[visitor_team_id], lazy="selectin")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"
    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', name='uix_player_game'),
    )

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    minutes = Column(String(10))  # BallDontLie returns as "35:24" format
    points = Column(Integer, default=0)
    rebounds = Column(Integer, default=0)  # Total rebounds (offensive + defensive)
    assists = Column(Integer, default=0)
    steals = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)

    # Field Goals
    fgm = Column(Integer, default=0)  # field goals made
    fga = Column(Integer, default=0)  # field goals attempted
    fg_pct = Column(Float)

    # 3-Pointers
    fg3m = Column(Integer, default=0)  # 3-pointers made
    fg3a = Column(Integer, default=0)  # 3-pointers attempted
    fg3_pct = Column(Float)

    # Free Throws
    ftm = Column(Integer, default=0)  # free throws made
    fta = Column(Integer, default=0)  # free throws attempted
    ft_pct = Column(Float)

    # Rebounds breakdown
    oreb = Column(Integer, default=0)  # offensive rebounds
    dreb = Column(Integer, default=0)  # defensive rebounds

    # Additional stats
    pf = Column(Integer, default=0)  # personal fouls

    # Keep legacy column names for compatibility
    field_goals_made = Column(Integer, default=0)
    field_goals_attempted = Column(Integer, default=0)
    three_pointers_made = Column(Integer, default=0)
    three_pointers_attempted = Column(Integer, default=0)
    free_throws_made = Column(Integer, default=0)
    free_throws_attempted = Column(Integer, default=0)

    # Relationships
    player = relationship("Player", lazy="selectin")
    game = relationship("Game", back_populates="player_game_stats", lazy="selectin")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SportsbookLine(Base):
    __tablename__ = "sportsbook_lines"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    market = Column(String(50), nullable=False)  # points, rebounds, assists, pra
    line_value = Column(Float, nullable=False)
    book = Column(String(100), default='PrizePicks')

    # Relationships
    player = relationship("Player", lazy="selectin")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ApiCache(Base):
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True)
    key = Column(String(255))  # For scraper cache
    endpoint = Column(String(255))  # For API cache
    params = Column(Text)  # JSON string of parameters
    response = Column(Text)  # JSON string of response
    data = Column(Text)  # For scraper data
    expires_at = Column(DateTime, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 