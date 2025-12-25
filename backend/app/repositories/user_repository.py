"""
User repository for database operations
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User, Player
from app.schemas.auth import UserCreate, UserUpdate


class UserRepository:
    """Repository for User database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """
        Create a new user

        Args:
            user_data: User registration data
            hashed_password: Hashed password string

        Returns:
            Created User object
        """
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            primary_betting_app=user_data.primary_betting_app.value,
            subscription_tier="Free",
            is_active=True,
            email_verified=False,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def create_oauth_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        primary_betting_app: str,
        google_id: Optional[str] = None,
        oauth_provider: Optional[str] = None,
    ) -> User:
        """
        Create a new user via OAuth

        Args:
            email: User email
            first_name: User first name
            last_name: User last name
            primary_betting_app: Primary betting platform
            google_id: Google OAuth ID
            oauth_provider: OAuth provider name

        Returns:
            Created User object
        """
        user = User(
            email=email,
            hashed_password=None,  # No password for OAuth users
            first_name=first_name,
            last_name=last_name,
            primary_betting_app=primary_betting_app,
            google_id=google_id,
            oauth_provider=oauth_provider,
            subscription_tier="Free",
            is_active=True,
            email_verified=True,  # OAuth emails are pre-verified
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: Email address

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get user by Google OAuth ID

        Args:
            google_id: Google OAuth ID

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, updates: UserUpdate) -> Optional[User]:
        """
        Update user profile

        Args:
            user_id: User ID
            updates: User update data

        Returns:
            Updated User object or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update only provided fields
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "primary_betting_app" and value:
                setattr(user, field, value.value)
            else:
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp

        Args:
            user_id: User ID
        """
        user = await self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.commit()

    async def add_favorite_player(self, user_id: int, player_id: int) -> bool:
        """
        Add a player to user's favorites

        Args:
            user_id: User ID
            player_id: Player ID

        Returns:
            True if added successfully, False otherwise
        """
        user = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.favorite_players))
        )
        user = user.scalar_one_or_none()

        if not user:
            return False

        # Check if player exists
        player = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = player.scalar_one_or_none()

        if not player:
            return False

        # Check if already favorited
        if player in user.favorite_players:
            return True

        user.favorite_players.append(player)
        await self.db.commit()

        return True

    async def remove_favorite_player(self, user_id: int, player_id: int) -> bool:
        """
        Remove a player from user's favorites

        Args:
            user_id: User ID
            player_id: Player ID

        Returns:
            True if removed successfully, False otherwise
        """
        user = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.favorite_players))
        )
        user = user.scalar_one_or_none()

        if not user:
            return False

        # Find and remove player from favorites
        player_to_remove = None
        for player in user.favorite_players:
            if player.id == player_id:
                player_to_remove = player
                break

        if player_to_remove:
            user.favorite_players.remove(player_to_remove)
            await self.db.commit()
            return True

        return False

    async def get_user_favorites(self, user_id: int) -> List[Player]:
        """
        Get all favorite players for a user

        Args:
            user_id: User ID

        Returns:
            List of Player objects
        """
        user = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.favorite_players))
        )
        user = user.scalar_one_or_none()

        if not user:
            return []

        return user.favorite_players
