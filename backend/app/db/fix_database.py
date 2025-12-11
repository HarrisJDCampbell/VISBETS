import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from .models import Base

# Get the database URL from environment variable or use a default value
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "sqlite+aiosqlite:///./visbets.db")

async def fix_database():
    """Fix database issues by recreating tables with correct schema."""
    # Create async engine
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=True
    )
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Create all tables with correct schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database schema has been fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_database()) 