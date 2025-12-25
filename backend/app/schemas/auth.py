"""
Authentication schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class BettingApp(str, Enum):
    """Supported betting/sportsbook platforms"""
    DRAFTKINGS = "DraftKings"
    FANDUEL = "FanDuel"
    PRIZEPICKS = "PrizePicks"
    UNDERDOG = "Underdog Fantasy"


class SubscriptionTier(str, Enum):
    """User subscription tiers"""
    FREE = "Free"
    VIS_PLUS = "VisPlus"
    VIS_MAX = "VisMax"


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    primary_betting_app: BettingApp

    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets strength requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class GoogleOAuthRequest(BaseModel):
    """Schema for Google OAuth login"""
    id_token: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    primary_betting_app: Optional[BettingApp] = None


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    primary_betting_app: str
    subscription_tier: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Schema for authentication response with token and user data"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    primary_betting_app: Optional[BettingApp] = None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_new_password(cls, v):
        """Ensure new password meets strength requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        return v
