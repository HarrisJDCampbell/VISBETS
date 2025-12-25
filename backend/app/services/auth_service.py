"""
Authentication service with business logic for user authentication
"""
from typing import Optional
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests
import os

from app.schemas.auth import UserCreate, UserLogin, GoogleOAuthRequest, AuthResponse, Token, UserResponse
from app.repositories.user_repository import UserRepository
from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    validate_password_strength,
)


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        Register a new user with email and password

        Args:
            user_data: User registration data

        Returns:
            AuthResponse with token and user data

        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        try:
            validate_password_strength(user_data.password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = await self.user_repo.create_user(user_data, hashed_password)

        # Update last login
        await self.user_repo.update_last_login(user.id)

        # Generate access token
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        # Create response
        user_response = UserResponse.from_orm(user)

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def login_user(self, credentials: UserLogin) -> AuthResponse:
        """
        Login user with email and password

        Args:
            credentials: User login credentials

        Returns:
            AuthResponse with token and user data

        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_user_by_email(credentials.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Verify password
        if not user.hashed_password or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        # Update last login
        await self.user_repo.update_last_login(user.id)

        # Generate access token
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        # Create response
        user_response = UserResponse.from_orm(user)

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def google_oauth_login(self, oauth_data: GoogleOAuthRequest) -> AuthResponse:
        """
        Login or register user with Google OAuth

        Args:
            oauth_data: Google OAuth request data

        Returns:
            AuthResponse with token and user data

        Raises:
            HTTPException: If OAuth verification fails
        """
        try:
            # Verify the Google ID token with multiple client IDs (Web, iOS, Android)
            google_client_ids = [
                os.getenv("GOOGLE_CLIENT_ID"),  # Web Client ID
                "254361116090-pp7bvgu4i8ptdp1j1e124jui49busunj.apps.googleusercontent.com",  # iOS
                "254361116090-fpa07ugteb684s9mvi9tcqclq5gv65qk.apps.googleusercontent.com",  # Android
            ]

            idinfo = None
            for client_id in google_client_ids:
                if not client_id:
                    continue
                try:
                    idinfo = id_token.verify_oauth2_token(
                        oauth_data.id_token,
                        requests.Request(),
                        client_id
                    )
                    break  # Successfully verified
                except ValueError:
                    continue  # Try next client ID

            if not idinfo:
                raise ValueError("Failed to verify token with any client ID")

            # Extract user info from token
            google_id = idinfo['sub']
            email = idinfo['email']
            email_verified = idinfo.get('email_verified', False)

            if not email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not verified with Google"
                )

            # Check if user already exists by Google ID
            user = await self.user_repo.get_user_by_google_id(google_id)

            if not user:
                # Check if user exists by email
                user = await self.user_repo.get_user_by_email(email)

                if user:
                    # Link Google account to existing user
                    user.google_id = google_id
                    user.oauth_provider = "google"
                    await self.db.commit()
                    await self.db.refresh(user)
                else:
                    # Create new user
                    # Extract name from Google profile
                    first_name = idinfo.get('given_name', oauth_data.first_name or 'User')
                    last_name = idinfo.get('family_name', oauth_data.last_name or '')

                    # Use provided betting app or default to PrizePicks
                    betting_app = oauth_data.primary_betting_app.value if oauth_data.primary_betting_app else 'PrizePicks'

                    user = await self.user_repo.create_oauth_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        primary_betting_app=betting_app,
                        google_id=google_id,
                        oauth_provider="google"
                    )

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive"
                )

            # Update last login
            await self.user_repo.update_last_login(user.id)

            # Generate access token
            access_token = create_access_token(
                data={"user_id": user.id, "email": user.email}
            )

            # Create response
            user_response = UserResponse.from_orm(user)

            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                user=user_response
            )

        except ValueError as e:
            # Invalid token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google OAuth token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google OAuth error: {str(e)}"
            )

    async def get_current_user_data(self, user_id: int) -> UserResponse:
        """
        Get current user data

        Args:
            user_id: User ID from JWT token

        Returns:
            UserResponse with user data

        Raises:
            HTTPException: If user not found
        """
        user = await self.user_repo.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        return UserResponse.from_orm(user)
