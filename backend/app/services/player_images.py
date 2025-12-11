"""
Player Image URL Generator

This module generates player image URLs using the NBA CDN.
BallDontLie provides the official NBA player ID which we can use directly
with the NBA CDN - this is free, legal, and used by ESPN and official NBA sites.
"""

from typing import Optional


def get_nba_headshot_url(player_id: int, size: str = "1040x760") -> str:
    """
    Get player headshot URL from NBA.com CDN using the official NBA player ID.

    BallDontLie API provides the official NBA player ID, which we can use directly
    with the NBA CDN. This is free, legal, and used by ESPN and official NBA sites.

    Args:
        player_id: Official NBA player ID (from BallDontLie API)
        size: Image size - "1040x760" (full) or "260x190" (thumbnail)

    Returns:
        Full URL to player headshot

    Example:
        >>> get_nba_headshot_url(2544)  # LeBron James
        'https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png'
    """
    return f"https://cdn.nba.com/headshots/nba/latest/{size}/{player_id}.png"


def get_nba_thumbnail_url(player_id: int) -> str:
    """
    Get player thumbnail URL (smaller size for lists/cards).

    Args:
        player_id: Official NBA player ID

    Returns:
        Full URL to player thumbnail (260x190)
    """
    return get_nba_headshot_url(player_id, size="260x190")


def get_player_image_url(player_id: int, thumbnail: bool = False) -> str:
    """
    Get player image URL (convenience function for ingestion).

    Args:
        player_id: Official NBA player ID from BallDontLie
        thumbnail: If True, return smaller thumbnail size

    Returns:
        Full URL to player headshot
    """
    if thumbnail:
        return get_nba_thumbnail_url(player_id)
    return get_nba_headshot_url(player_id)
