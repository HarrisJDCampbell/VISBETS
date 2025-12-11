from .database import Base, get_db, get_async_db, init_db, init_db_sync
from .models import Team, Player, PlayerStats, ApiCache
from .repositories import TeamRepository, PlayerRepository, StatsRepository
from .service import DatabaseService

# Initialize database synchronously at module import
init_db_sync()

__all__ = [
    'Base',
    'get_db',
    'get_async_db',
    'init_db',
    'init_db_sync',
    'Team',
    'Player',
    'PlayerStats',
    'ApiCache',
    'TeamRepository',
    'PlayerRepository',
    'StatsRepository',
    'DatabaseService'
] 