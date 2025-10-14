import uuid
from datetime import datetime, timedelta
from typing import Optional


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def get_usage_reset_date() -> datetime:
    """Get the next month's start date for usage reset"""
    now = datetime.utcnow()
    if now.month == 12:
        return datetime(now.year + 1, 1, 1)
    else:
        return datetime(now.year, now.month + 1, 1)


def should_reset_usage(reset_date: datetime) -> bool:
    """Check if usage should be reset"""
    return datetime.utcnow() >= reset_date


def get_tier_limits(tier: str) -> dict:
    """Get usage limits for a tier"""
    limits = {
        "free": {
            "generations_per_month": 1,
            "revisions_per_month": 10,
            "published_projects": 0,
        },
        "pro": {
            "generations_per_month": 5,
            "revisions_per_month": -1,  # unlimited
            "published_projects": 1,
        },
        "ultimate": {
            "generations_per_month": -1,  # unlimited
            "revisions_per_month": -1,  # unlimited
            "published_projects": -1,  # unlimited
        },
    }
    return limits.get(tier.lower(), limits["free"])


def calculate_expiry(days: int = 7) -> datetime:
    """Calculate expiry datetime"""
    return datetime.utcnow() + timedelta(days=days)
