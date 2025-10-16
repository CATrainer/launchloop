#!/usr/bin/env python3
"""
Upgrade user tier and reset usage limits.
Usage: python scripts/upgrade_user.py <email> <tier>
Example: python scripts/upgrade_user.py user@example.com pro
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.user import User, Tier
from app.utils.helpers import get_usage_reset_date


def upgrade_user(email: str, tier: str):
    """Upgrade user to specified tier and reset usage"""
    db = SessionLocal()
    
    try:
        # Validate tier
        tier = tier.lower()
        if tier not in ["free", "pro", "ultimate"]:
            print(f"❌ Invalid tier: {tier}")
            print(f"   Valid options: free, pro, ultimate")
            return False
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Get tier enum
        tier_enum = Tier.FREE if tier == "free" else (Tier.PRO if tier == "pro" else Tier.ULTIMATE)
        
        # Update user
        old_tier = user.tier.value
        user.tier = tier_enum
        user.generations_used_this_month = 0
        user.revisions_used_this_month = 0
        user.usage_reset_date = get_usage_reset_date()
        
        db.commit()
        
        print(f"✅ User upgraded successfully!")
        print(f"   Email: {email}")
        print(f"   Old tier: {old_tier}")
        print(f"   New tier: {tier}")
        print(f"   Generations used: {user.generations_used_this_month}")
        print(f"   Revisions used: {user.revisions_used_this_month}")
        print(f"   Usage resets: {user.usage_reset_date.strftime('%Y-%m-%d')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/upgrade_user.py <email> <tier>")
        print("Tiers: free, pro, ultimate")
        print("\nExample:")
        print("  python scripts/upgrade_user.py user@example.com pro")
        sys.exit(1)
    
    email = sys.argv[1]
    tier = sys.argv[2]
    
    success = upgrade_user(email, tier)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
