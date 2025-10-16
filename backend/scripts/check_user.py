#!/usr/bin/env python3
"""
Check user status, tier, and usage limits.
Usage: python scripts/check_user.py <email>
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.user import User
from app.utils.helpers import get_tier_limits, should_reset_usage


def check_user(email: str):
    """Display user information"""
    db = SessionLocal()
    
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Get tier limits
        limits = get_tier_limits(user.tier.value)
        
        # Check if usage should reset
        needs_reset = should_reset_usage(user.usage_reset_date)
        
        print(f"\n{'='*60}")
        print(f"👤 USER INFORMATION")
        print(f"{'='*60}")
        print(f"Email:              {user.email}")
        print(f"ID:                 {user.id}")
        print(f"Role:               {user.role.value}")
        print(f"Tier:               {user.tier.value.upper()}")
        print(f"Payment Status:     {user.payment_status.value}")
        
        if user.stripe_customer_id:
            print(f"Stripe Customer:    {user.stripe_customer_id}")
        if user.subscription_status:
            print(f"Subscription:       {user.subscription_status.value}")
        
        print(f"\n{'='*60}")
        print(f"📊 USAGE & LIMITS")
        print(f"{'='*60}")
        
        # Generations
        gen_limit = limits["generations_per_month"]
        gen_limit_str = "Unlimited" if gen_limit == -1 else str(gen_limit)
        print(f"Generations:        {user.generations_used_this_month} / {gen_limit_str}")
        
        # Revisions
        rev_limit = limits["revisions_per_month"]
        rev_limit_str = "Unlimited" if rev_limit == -1 else str(rev_limit)
        print(f"Revisions:          {user.revisions_used_this_month} / {rev_limit_str}")
        
        # Published projects
        pub_limit = limits["published_projects"]
        pub_limit_str = "Unlimited" if pub_limit == -1 else str(pub_limit)
        print(f"Published Projects: {pub_limit_str}")
        
        print(f"\nUsage Resets:       {user.usage_reset_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if needs_reset:
            print(f"                    ⚠️  Usage reset is DUE!")
        
        print(f"\n{'='*60}")
        print(f"📅 METADATA")
        print(f"{'='*60}")
        print(f"Created:            {user.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Last Active:        {user.last_active_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*60}\n")
        
        # Check if user can generate
        if gen_limit != -1 and user.generations_used_this_month >= gen_limit:
            print(f"⚠️  User has reached generation limit!")
            print(f"   To upgrade: python scripts/upgrade_user.py {email} pro")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_user.py <email>")
        print("\nExample:")
        print("  python scripts/check_user.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    success = check_user(email)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
