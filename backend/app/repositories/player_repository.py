from typing import Dict, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Player, PlayerStats, Team
from app.services.api_sports import APISportsService
from datetime import datetime
from sqlalchemy import select, update, insert

logger = logging.getLogger(__name__)

class PlayerRepository:
    def __init__(self, session: AsyncSession, api_service: APISportsService):
        self.session = session
        self.api_service = api_service

    async def get_player_details(self, player_id: int) -> Dict:
        """
        Get detailed player information including stats.
        First check local database, then fall back to API if needed.
        """
        # Try to get player from database first
        local_player = await self._get_player_from_db(player_id)
        
        if local_player and self._is_data_fresh(local_player.updated_at):
            logger.info(f"Using local data for player {player_id}")
            return await self._format_player_data(local_player)
        
        # If not found or stale, fetch from API and save to DB
        logger.info(f"Fetching player {player_id} from API")
        player_info = await self.api_service.get_player_info(self.session, player_id)
        player_stats = await self.api_service.get_player_stats(self.session, player_id)
        
        # Save to database
        await self._save_player_data(player_id, player_info, player_stats)
        
        # Get updated player from database
        updated_player = await self._get_player_from_db(player_id)
        if updated_player:
            return await self._format_player_data(updated_player)
        
        # Fallback to direct API response if database save failed
        return {
            "player": player_info.get("response", [{}])[0] if "response" in player_info else {},
            "stats": player_stats.get("response", []) if "response" in player_stats else []
        }

    async def get_players_by_team(self, team_id: int) -> List[Dict]:
        """
        Get all players from a specific team.
        First check local database, then fall back to API if needed.
        """
        # Try to get team from database first
        team = await self.session.execute(
            select(Team).where(Team.api_id == team_id)
        )
        team = team.scalars().first()
        
        if team and self._is_data_fresh(team.updated_at):
            # Get players from this team
            players = await self.session.execute(
                select(Player).where(Player.team_id == team.id)
            )
            players = players.scalars().all()
            
            if players:
                logger.info(f"Using local data for team {team_id} players")
                return [await self._format_player_data(player, include_stats=False) for player in players]
        
        # If not found or stale, fetch from API
        logger.info(f"Fetching team {team_id} players from API")
        team_players = await self.api_service.get_team_players(self.session, team_id)
        
        if "response" not in team_players or not team_players["response"]:
            return []
        
        # Save team if needed
        if not team:
            team_info = await self.api_service.get_team_info(self.session, team_id)
            if "response" in team_info and team_info["response"]:
                team_data = team_info["response"][0]
                team = Team(
                    api_id=team_id,
                    name=team_data.get("name", ""),
                    full_name=team_data.get("name", ""),
                    abbreviation=team_data.get("code", ""),
                    city=team_data.get("city", ""),
                    logo_url=team_data.get("logo", ""),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.session.add(team)
                await self.session.commit()
                await self.session.refresh(team)
        
        # Save players
        players_data = []
        for player_data in team_players["response"]:
            api_player_id = player_data.get("id")
            if not api_player_id:
                continue
                
            # Save player
            await self._save_player_basic_data(api_player_id, player_data, team.id if team else None)
            
            # Format response
            players_data.append({
                "id": api_player_id,
                "firstName": player_data.get("firstname", ""),
                "lastName": player_data.get("lastname", ""),
                "position": player_data.get("position", ""),
                "jerseyNumber": player_data.get("jersey", ""),
                "height": player_data.get("height", {}).get("meters", ""),
                "weight": player_data.get("weight", {}).get("kilograms", ""),
                "photo": player_data.get("photo", "")
            })
            
        return players_data

    async def get_top_players(self, limit: int = 10) -> List[Dict]:
        """
        Get top players based on stats.
        """
        # Check if the season info needs to be updated
        await self.api_service.get_season_info(self.session)
        
        # Get players with highest points average
        try:
            players_with_stats = await self.session.execute(
                select(Player, PlayerStats)
                .join(PlayerStats, Player.id == PlayerStats.player_id)
                .order_by(PlayerStats.points_per_game.desc())
                .limit(limit)
            )
            
            result = []
            for player, stats in players_with_stats:
                player_data = await self._format_player_data(player)
                player_data["stats"] = {
                    "pointsPerGame": stats.points_per_game,
                    "reboundsPerGame": stats.rebounds_per_game,
                    "assistsPerGame": stats.assists_per_game,
                    "minutesPerGame": stats.minutes_per_game
                }
                result.append(player_data)
            
            if result:
                return result
                
            # If no results from database, fetch from API directly
            logger.info("No top players found in database, fetching from API")
            # This is just a fallback - we would normally want to implement API-based top players
            # fetching, but for now we'll get data for a few known top players
            top_player_ids = [242, 265, 115, 79, 490, 55, 253, 457, 125, 561]  # Example ids
            result = []
            for pid in top_player_ids[:limit]:
                try:
                    player_data = await self.get_player_details(pid)
                    if player_data:
                        result.append(player_data)
                except Exception as e:
                    logger.error(f"Error fetching top player {pid}: {str(e)}")
            
            return result
        except Exception as e:
            logger.error(f"Error fetching top players: {str(e)}")
            return []

    async def search_players(self, query: str) -> List[Dict]:
        """
        Search for players by name.
        """
        # Search in local database first
        players = await self.session.execute(
            select(Player).where(
                (Player.first_name.ilike(f"%{query}%")) | 
                (Player.last_name.ilike(f"%{query}%"))
            ).limit(10)
        )
        players = players.scalars().all()
        
        if players:
            logger.info(f"Found {len(players)} players in local database for query '{query}'")
            return [await self._format_player_data(player, include_stats=False) for player in players]
        
        # TODO: Implement API search if needed
        logger.info(f"No players found in local database for query '{query}'")
        return []

    async def _get_player_from_db(self, player_id: int) -> Optional[Player]:
        """Get player from database by API ID"""
        player = await self.session.execute(
            select(Player).where(Player.api_id == player_id)
        )
        return player.scalars().first()

    async def _save_player_data(self, player_id: int, player_info: Dict, player_stats: Dict) -> None:
        """Save player data to database"""
        try:
            # Extract player info
            player_data = player_info.get("response", [{}])[0] if "response" in player_info else {}
            if not player_data:
                logger.error(f"No player data found for player {player_id}")
                return
                
            # Get team info
            team_id = None
            if "team" in player_data and "id" in player_data["team"]:
                api_team_id = player_data["team"]["id"]
                team = await self.session.execute(
                    select(Team).where(Team.api_id == api_team_id)
                )
                team = team.scalars().first()
                
                if not team:
                    # Create team if it doesn't exist
                    team_info = await self.api_service.get_team_info(self.session, api_team_id)
                    if "response" in team_info and team_info["response"]:
                        team_data = team_info["response"][0]
                        team = Team(
                            api_id=api_team_id,
                            name=team_data.get("name", ""),
                            full_name=team_data.get("name", ""),
                            abbreviation=team_data.get("code", ""),
                            city=team_data.get("city", ""),
                            logo_url=team_data.get("logo", ""),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        self.session.add(team)
                        await self.session.commit()
                        await self.session.refresh(team)
                
                if team:
                    team_id = team.id
            
            # Save player basic info
            player = await self._get_player_from_db(player_id)
            
            if player:
                # Update existing player
                await self.session.execute(
                    update(Player)
                    .where(Player.api_id == player_id)
                    .values(
                        first_name=player_data.get("firstname", ""),
                        last_name=player_data.get("lastname", ""),
                        full_name=f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}",
                        position=player_data.get("position", ""),
                        jersey_number=player_data.get("jersey", ""),
                        height=player_data.get("height", {}).get("meters", ""),
                        weight=player_data.get("weight", {}).get("kilograms", ""),
                        image_url=player_data.get("photo", ""),
                        team_id=team_id,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Create new player
                stmt = insert(Player).values(
                    api_id=player_id,
                    first_name=player_data.get("firstname", ""),
                    last_name=player_data.get("lastname", ""),
                    full_name=f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}",
                    position=player_data.get("position", ""),
                    jersey_number=player_data.get("jersey", ""),
                    height=player_data.get("height", {}).get("meters", ""),
                    weight=player_data.get("weight", {}).get("kilograms", ""),
                    image_url=player_data.get("photo", ""),
                    team_id=team_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                result = await self.session.execute(stmt)
                await self.session.commit()
                
                # Get the ID of the newly inserted player
                player = await self._get_player_from_db(player_id)
            
            # Process stats if player was created/updated successfully
            if player and "response" in player_stats and player_stats["response"]:
                # Calculate averages from all games
                games = player_stats["response"]
                if not games:
                    return
                    
                # Filter out games with no minutes played
                valid_games = [g for g in games if g.get("min") and g["min"] != "0"]
                if not valid_games:
                    return
                    
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
                
                try:
                    # Get existing stats
                    stats_query = await self.session.execute(
                        select(PlayerStats).where(PlayerStats.player_id == player.id)
                    )
                    stats = stats_query.scalars().first()
                    
                    if stats:
                        # Update existing stats
                        await self.session.execute(
                            update(PlayerStats)
                            .where(PlayerStats.player_id == player.id)
                            .values(
                                points=ppg,
                                rebounds=rpg,
                                assists=apg,
                                steals=spg,
                                blocks=bpg,
                                minutes_played=mpg,
                                games_played=total_games,
                                updated_at=datetime.utcnow(),
                                season=self.api_service.current_season
                            )
                        )
                    else:
                        # Create new stats
                        self.session.add(PlayerStats(
                            player_id=player.id,
                            points=ppg,
                            rebounds=rpg,
                            assists=apg,
                            steals=spg,
                            blocks=bpg,
                            minutes_played=mpg,
                            games_played=total_games,
                            season=self.api_service.current_season,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        ))
                    
                    await self.session.commit()
                except Exception as e:
                    logger.error(f"Error saving player stats: {str(e)}")
                    await self.session.rollback()
                
        except Exception as e:
            logger.error(f"Error saving player data: {str(e)}")
            await self.session.rollback()

    async def _save_player_basic_data(self, player_id: int, player_data: Dict, team_id: Optional[int] = None) -> None:
        """Save basic player info without stats"""
        try:
            player = await self._get_player_from_db(player_id)
            
            if player:
                # Update existing player
                await self.session.execute(
                    update(Player)
                    .where(Player.api_id == player_id)
                    .values(
                        first_name=player_data.get("firstname", ""),
                        last_name=player_data.get("lastname", ""),
                        full_name=f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}",
                        position=player_data.get("position", ""),
                        jersey_number=player_data.get("jersey", ""),
                        height=player_data.get("height", {}).get("meters", ""),
                        weight=player_data.get("weight", {}).get("kilograms", ""),
                        image_url=player_data.get("photo", ""),
                        team_id=team_id,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Create new player
                self.session.add(Player(
                    api_id=player_id,
                    first_name=player_data.get("firstname", ""),
                    last_name=player_data.get("lastname", ""),
                    full_name=f"{player_data.get('firstname', '')} {player_data.get('lastname', '')}",
                    position=player_data.get("position", ""),
                    jersey_number=player_data.get("jersey", ""),
                    height=player_data.get("height", {}).get("meters", ""),
                    weight=player_data.get("weight", {}).get("kilograms", ""),
                    image_url=player_data.get("photo", ""),
                    team_id=team_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
            
            await self.session.commit()
                
        except Exception as e:
            logger.error(f"Error saving basic player data: {str(e)}")
            await self.session.rollback()
    
    async def _format_player_data(self, player: Player, include_stats: bool = True) -> Dict:
        """Format player data from database model to API-like response"""
        result = {
            "id": player.api_id,
            "firstName": player.first_name,
            "lastName": player.last_name,
            "position": player.position,
            "jerseyNumber": player.jersey_number,
            "height": player.height,
            "weight": player.weight,
            "photo": player.image_url
        }
        
        # Add team info if available
        if player.team_id:
            team = await self.session.execute(
                select(Team).where(Team.id == player.team_id)
            )
            team = team.scalars().first()
            if team:
                result["team"] = {
                    "id": team.api_id,
                    "name": team.name,
                    "code": team.abbreviation,
                    "logo": team.logo_url
                }
        
        # Add stats if requested
        if include_stats:
            stats = await self.session.execute(
                select(PlayerStats).where(PlayerStats.player_id == player.id)
            )
            stats = stats.scalars().first()
            if stats:
                result["stats"] = {
                    "pointsPerGame": round(stats.points, 1),
                    "reboundsPerGame": round(stats.rebounds, 1),
                    "assistsPerGame": round(stats.assists, 1),
                    "stealsPerGame": round(stats.steals, 1),
                    "blocksPerGame": round(stats.blocks, 1),
                    "minutesPerGame": round(stats.minutes_played, 1),
                    "gamesPlayed": stats.games_played,
                    "season": stats.season
                }
            else:
                # If no stats available but they were requested, try to fetch from API
                try:
                    player_stats = await self.api_service.get_player_stats(self.session, player.api_id)
                    if "response" in player_stats and player_stats["response"]:
                        result["stats"] = player_stats["response"]
                except Exception as e:
                    logger.error(f"Error fetching stats for player {player.api_id}: {str(e)}")
                    result["stats"] = []
        
        return result
    
    def _is_data_fresh(self, updated_at: datetime) -> bool:
        """Check if data is fresh (less than 12 hours old)"""
        if not updated_at:
            return False
        return (datetime.utcnow() - updated_at).total_seconds() < 43200  # 12 hours 