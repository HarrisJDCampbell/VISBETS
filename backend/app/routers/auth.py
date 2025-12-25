"""
Authentication router for user registration, login, and profile management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.database import get_async_db
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    GoogleOAuthRequest,
    AuthResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.utils.auth import decode_access_token, security
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_db)
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        # Decode token
        payload = decode_access_token(credentials.credentials)
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        # Get user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_id(user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return UserResponse.from_orm(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user with email and password

    **Request body:**
    - email: Valid email address
    - password: Minimum 8 characters, 1 uppercase, 1 number
    - first_name: User's first name
    - last_name: User's last name
    - phone_number: Optional phone number
    - primary_betting_app: Primary sportsbook (DraftKings, FanDuel, PrizePicks, Underdog Fantasy)

    **Returns:**
    - access_token: JWT token for authentication
    - user: User profile data
    """
    try:
        auth_service = AuthService(session)
        result = await auth_service.register_user(user_data)
        logger.info(f"New user registered: {user_data.email}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_async_db)
):
    """
    Login with email and password

    **Request body:**
    - email: User's email address
    - password: User's password

    **Returns:**
    - access_token: JWT token for authentication
    - user: User profile data
    """
    try:
        auth_service = AuthService(session)
        result = await auth_service.login_user(credentials)
        logger.info(f"User logged in: {credentials.email}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/google", response_model=AuthResponse)
async def google_oauth(
    oauth_data: GoogleOAuthRequest,
    session: AsyncSession = Depends(get_async_db)
):
    """
    Login or register with Google OAuth

    **Request body:**
    - id_token: Google ID token from OAuth flow
    - first_name: Optional for new users
    - last_name: Optional for new users
    - primary_betting_app: Optional (defaults to PrizePicks)

    **Returns:**
    - access_token: JWT token for authentication
    - user: User profile data
    """
    try:
        logger.info(f"Google OAuth login attempt")
        auth_service = AuthService(session)
        result = await auth_service.google_oauth_login(oauth_data)
        logger.info(f"User logged in via Google OAuth: {result.user.email}")
        return result
    except HTTPException as he:
        logger.error(f"Google OAuth HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error during Google OAuth: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication error: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get current authenticated user's profile

    **Requires:** Valid JWT token in Authorization header

    **Returns:**
    - User profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    updates: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Update current user's profile

    **Requires:** Valid JWT token in Authorization header

    **Request body:**
    - first_name: Optional new first name
    - last_name: Optional new last name
    - phone_number: Optional new phone number
    - primary_betting_app: Optional new primary sportsbook

    **Returns:**
    - Updated user profile data
    """
    try:
        user_repo = UserRepository(session)
        updated_user = await user_repo.update_user(current_user.id, updates)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(f"User profile updated: {current_user.email}")
        return UserResponse.from_orm(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating profile"
        )


@router.post("/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Logout current user

    **Requires:** Valid JWT token in Authorization header

    Note: This endpoint is primarily for logging purposes.
    The frontend should delete the stored token.

    **Returns:**
    - Success message
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}


# Favorite players endpoints
@router.post("/favorites/{player_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite_player(
    player_id: int,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Add a player to user's favorites

    **Requires:** Valid JWT token in Authorization header

    **Path parameters:**
    - player_id: ID of the player to add to favorites

    **Returns:**
    - Success message
    """
    try:
        user_repo = UserRepository(session)
        success = await user_repo.add_favorite_player(current_user.id, player_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )

        logger.info(f"User {current_user.email} added player {player_id} to favorites")
        return {"message": "Player added to favorites", "player_id": player_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite player: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while adding favorite"
        )


@router.delete("/favorites/{player_id}")
async def remove_favorite_player(
    player_id: int,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Remove a player from user's favorites

    **Requires:** Valid JWT token in Authorization header

    **Path parameters:**
    - player_id: ID of the player to remove from favorites

    **Returns:**
    - Success message
    """
    try:
        user_repo = UserRepository(session)
        success = await user_repo.remove_favorite_player(current_user.id, player_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found in favorites"
            )

        logger.info(f"User {current_user.email} removed player {player_id} from favorites")
        return {"message": "Player removed from favorites", "player_id": player_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite player: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while removing favorite"
        )


@router.get("/favorites")
async def get_favorite_players(
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_db)
):
    """
    Get all favorite players for current user

    **Requires:** Valid JWT token in Authorization header

    **Returns:**
    - List of favorite players
    """
    try:
        user_repo = UserRepository(session)
        favorites = await user_repo.get_user_favorites(current_user.id)

        # Convert to simple dict format
        result = [
            {
                "id": player.id,
                "full_name": player.full_name,
                "position": player.position,
                "team_id": player.team_id,
                "image_url": player.image_url,
            }
            for player in favorites
        ]

        return {"favorites": result, "count": len(result)}

    except Exception as e:
        logger.error(f"Error getting favorite players: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching favorites"
        )
