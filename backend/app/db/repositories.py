from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, delete, desc
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional
import logging

from .models import Team, Player, PlayerStats, ApiCache

logger = logging.getLogger(__name__)

class TeamRepository:
    @staticmethod
    async def create_team(db: AsyncSession, team_data: Dict[str, Any]) -> Team:
        """Create a new team or update an existing one."""
        try:
            team = Team(
                name=team_data.get("name", "Unknown"),
                full_name=team_data.get("fullName"),
                abbreviation=team_data.get("code"),
                city=team_data.get("city"),
                conference=team_data.get("leagues", {}).get("standard", {}).get("conference"),
                division=team_data.get("leagues", {}).get("standard", {}).get("division"),
                logo_url=team_data.get("logo"),
                api_id=team_data.get("id"),
                is_nba=team_data.get("nbaFranchise", True),
            )
            db.add(team)
            await db.commit()
            await db.refresh(team)
            return team
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating team: {e}")
            raise
    
    @staticmethod
    async def get_team_by_api_id(db: AsyncSession, api_id: int) -> Optional[Team]:
        """Get a team by its API ID."""
        try:
            result = await db.execute(select(Team).where(Team.api_id == api_id))
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting team by API ID: {e}")
            raise
    
    @staticmethod
    async def get_all_teams(db: AsyncSession, nba_only: bool = True) -> List[Team]:
        """Get all teams, optionally filtering for NBA teams only."""
        try:
            if nba_only:
                query = select(Team).where(Team.is_nba == True)
            else:
                query = select(Team)
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all teams: {e}")
            raise
    
    @staticmethod
    async def save_teams_from_api(db: AsyncSession, teams_data: List[Dict[str, Any]]) -> List[Team]:
        """Save multiple teams from API data."""
        try:
            saved_teams = []
            for team_data in teams_data:
                # Check if team already exists
                api_id = team_data.get("id")
                if not api_id:
                    continue
                    
                existing_team = await TeamRepository.get_team_by_api_id(db, api_id)
                
                if existing_team:
                    # Update existing team
                    update_data = {
                        "name": team_data.get("name", existing_team.name),
                        "full_name": team_data.get("fullName", existing_team.full_name),
                        "abbreviation": team_data.get("code", existing_team.abbreviation),
                        "city": team_data.get("city", existing_team.city),
                        "conference": team_data.get("leagues", {}).get("standard", {}).get("conference", existing_team.conference),
                        "division": team_data.get("leagues", {}).get("standard", {}).get("division", existing_team.division),
                        "logo_url": team_data.get("logo", existing_team.logo_url),
                        "is_nba": team_data.get("nbaFranchise", existing_team.is_nba),
                        "updated_at": datetime.utcnow()
                    }
                    
                    stmt = update(Team).where(Team.id == existing_team.id).values(**update_data)
                    await db.execute(stmt)
                    await db.commit()
                    
                    # Refresh the team object
                    result = await db.execute(select(Team).where(Team.id == existing_team.id))
                    saved_teams.append(result.scalars().first())
                else:
                    # Create new team
                    new_team = await TeamRepository.create_team(db, team_data)
                    saved_teams.append(new_team)
            
            return saved_teams
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving teams from API: {e}")
            raise

class PlayerRepository:
    @staticmethod
    async def create_player(db: AsyncSession, player_data: Dict[str, Any], team_id: int = None) -> Player:
        """Create a new player or update an existing one."""
        try:
            player = Player(
                first_name=player_data.get("firstname", ""),
                last_name=player_data.get("lastname", ""),
                full_name=f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}".strip(),
                position=player_data.get("leagues", {}).get("standard", {}).get("pos"),
                height=player_data.get("height", {}).get("meters"),
                weight=player_data.get("weight", {}).get("kilograms"),
                jersey_number=player_data.get("leagues", {}).get("standard", {}).get("jersey"),
                country=player_data.get("birth", {}).get("country"),
                college=player_data.get("college"),
                birth_date=player_data.get("birth", {}).get("date"),
                image_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_data.get('id')}.png",
                api_id=player_data.get("id"),
                team_id=team_id
            )
            db.add(player)
            await db.commit()
            await db.refresh(player)
            return player
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating player: {e}")
            raise
    
    @staticmethod
    async def get_player_by_api_id(db: AsyncSession, api_id: int) -> Optional[Player]:
        """Get a player by API ID."""
        try:
            result = await db.execute(select(Player).where(Player.api_id == api_id))
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting player by API ID: {e}")
            raise
    
    @staticmethod
    async def get_all_players(db: AsyncSession, 
                              skip: int = 0, 
                              limit: int = 100,
                              team_id: Optional[int] = None) -> List[Player]:
        """Get all players with pagination and optional team filter."""
        try:
            query = select(Player)
            
            if team_id:
                query = query.where(Player.team_id == team_id)
                
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all players: {e}")
            raise
    
    @staticmethod
    async def save_players_from_api(db: AsyncSession, 
                                    players_data: List[Dict[str, Any]], 
                                    team_data: Dict[str, Any]) -> List[Player]:
        """Save multiple players from API data with team association."""
        try:
            saved_players = []
            
            # Get or create the team first
            team_api_id = team_data.get("id")
            if not team_api_id:
                return saved_players
                
            team = await TeamRepository.get_team_by_api_id(db, team_api_id)
            if not team:
                team = await TeamRepository.create_team(db, team_data)
            
            for player_data in players_data:
                # Check if player already exists
                api_id = player_data.get("id")
                if not api_id:
                    continue
                    
                existing_player = await PlayerRepository.get_player_by_api_id(db, api_id)
                
                if existing_player:
                    # Update existing player
                    update_data = {
                        "first_name": player_data.get("firstname", existing_player.first_name),
                        "last_name": player_data.get("lastname", existing_player.last_name),
                        "full_name": f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}".strip(),
                        "position": player_data.get("leagues", {}).get("standard", {}).get("pos", existing_player.position),
                        "height": player_data.get("height", {}).get("meters", existing_player.height),
                        "weight": player_data.get("weight", {}).get("kilograms", existing_player.weight),
                        "jersey_number": player_data.get("leagues", {}).get("standard", {}).get("jersey", existing_player.jersey_number),
                        "country": player_data.get("birth", {}).get("country", existing_player.country),
                        "college": player_data.get("college", existing_player.college),
                        "birth_date": player_data.get("birth", {}).get("date", existing_player.birth_date),
                        "team_id": team.id,
                        "updated_at": datetime.utcnow()
                    }
                    
                    stmt = update(Player).where(Player.id == existing_player.id).values(**update_data)
                    await db.execute(stmt)
                    await db.commit()
                    
                    # Refresh the player object
                    result = await db.execute(select(Player).where(Player.id == existing_player.id))
                    saved_players.append(result.scalars().first())
                else:
                    # Create new player
                    new_player = await PlayerRepository.create_player(db, player_data, team.id)
                    saved_players.append(new_player)
            
            return saved_players
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving players from API: {e}")
            raise
    
    @staticmethod
    async def get_top_scorers(db: AsyncSession, limit: int = 20, season: str = "2023") -> List[Dict[str, Any]]:
        """Get top scorers with their stats."""
        try:
            query = (
                select(Player, PlayerStats)
                .join(PlayerStats, Player.id == PlayerStats.player_id)
                .where(PlayerStats.season == season)
                .order_by(desc(PlayerStats.points))
                .limit(limit)
            )
            
            result = await db.execute(query)
            rows = result.all()
            
            return [
                {
                    "id": player.api_id,
                    "name": player.full_name,
                    "team": player.team.name if player.team else "Unknown",
                    "imageUrl": player.image_url,
                    "predictions": {
                        "points": stats.points,
                        "assists": stats.assists,
                        "rebounds": stats.rebounds
                    },
                    "last_updated": stats.updated_at.isoformat() if stats.updated_at else None
                }
                for player, stats in rows
            ]
        except Exception as e:
            logger.error(f"Error getting top scorers: {e}")
            raise

class StatsRepository:
    @staticmethod
    async def create_or_update_player_stats(db: AsyncSession, 
                                            player_id: int, 
                                            stats_data: List[Dict[str, Any]],
                                            season: str = "2023") -> PlayerStats:
        """Create or update player statistics."""
        try:
            # Check if stats already exist for this player and season
            result = await db.execute(
                select(PlayerStats)
                .where(and_(
                    PlayerStats.player_id == player_id,
                    PlayerStats.season == season
                ))
            )
            existing_stats = result.scalars().first()
            
            # Calculate averages from all games
            if not stats_data:
                logger.error("No stats data provided")
                return None
                
            # Filter out games with no minutes played
            valid_games = [g for g in stats_data if g.get("min") and g["min"] != "0"]
            if not valid_games:
                logger.error("No valid games found in stats data")
                return None
                
            total_games = len(valid_games)
            total_points = sum(float(g.get("points", 0) or 0) for g in valid_games)
            total_rebounds = sum(float(g.get("totReb", 0) or 0) for g in valid_games)
            total_assists = sum(float(g.get("assists", 0) or 0) for g in valid_games)
            total_steals = sum(float(g.get("steals", 0) or 0) for g in valid_games)
            total_blocks = sum(float(g.get("blocks", 0) or 0) for g in valid_games)
            total_minutes = sum(float(g.get("min", "0").split(":")[0] or 0) for g in valid_games)
            
            # Calculate averages
            ppg = total_points / total_games if total_games > 0 else 0
            rpg = total_rebounds / total_games if total_games > 0 else 0
            apg = total_assists / total_games if total_games > 0 else 0
            spg = total_steals / total_games if total_games > 0 else 0
            bpg = total_blocks / total_games if total_games > 0 else 0
            mpg = total_minutes / total_games if total_games > 0 else 0
            
            if existing_stats:
                # Update existing stats
                update_data = {
                    "points": ppg,
                    "assists": apg,
                    "rebounds": rpg,
                    "steals": spg,
                    "blocks": bpg,
                    "games_played": total_games,
                    "minutes_played": mpg,
                    "updated_at": datetime.utcnow()
                }
                
                stmt = update(PlayerStats).where(PlayerStats.id == existing_stats.id).values(**update_data)
                await db.execute(stmt)
                await db.commit()
                
                # Refresh the stats object
                result = await db.execute(select(PlayerStats).where(PlayerStats.id == existing_stats.id))
                return result.scalars().first()
            else:
                # Create new stats
                stats = PlayerStats(
                    player_id=player_id,
                    season=season,
                    points=ppg,
                    assists=apg,
                    rebounds=rpg,
                    steals=spg,
                    blocks=bpg,
                    games_played=total_games,
                    minutes_played=mpg,
                    raw_data=stats_data
                )
                db.add(stats)
                await db.commit()
                await db.refresh(stats)
                return stats
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating/updating player stats: {e}")
            raise

class CacheRepository:
    @staticmethod
    async def get_cached_response(db: AsyncSession, endpoint: str, params: Dict[str, Any]) -> Optional[str]:
        """Get cached API response if it exists and is not expired."""
        try:
            params_str = json.dumps(params, sort_keys=True)
            result = await db.execute(
                select(ApiCache)
                .where(and_(
                    ApiCache.endpoint == endpoint,
                    ApiCache.params == params_str,
                    ApiCache.expires_at > datetime.utcnow()
                ))
            )
            cache_entry = result.scalars().first()
            return cache_entry.response if cache_entry else None
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            raise
    
    @staticmethod
    async def cache_response(db: AsyncSession, 
                             endpoint: str, 
                             params: Dict[str, Any], 
                             response: str, 
                             expiry_hours: int = 24) -> ApiCache:
        """Cache API response with expiration."""
        try:
            params_str = json.dumps(params, sort_keys=True)
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            cache_entry = ApiCache(
                endpoint=endpoint,
                params=params_str,
                response=response,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            await db.commit()
            await db.refresh(cache_entry)
            return cache_entry
        except Exception as e:
            await db.rollback()
            logger.error(f"Error caching response: {e}")
            raise
    
    @staticmethod
    async def clear_expired_cache(db: AsyncSession) -> int:
        """Clear expired cache entries."""
        try:
            result = await db.execute(
                delete(ApiCache)
                .where(ApiCache.expires_at <= datetime.utcnow())
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            logger.error(f"Error clearing expired cache: {e}")
            raise 