#!/usr/bin/env python3
"""
Script to make a user an admin.
Usage: python scripts/create_admin.py <email>
"""

import sys
import os

# Add parent directory to path (backend/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.user import User, Role


def make_admin(email: str):
    """Make a user an admin by email"""
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        if user.role == Role.ADMIN:
            print(f"ℹ️  User is already an admin: {email}")
            return True
        
        user.role = Role.ADMIN
        db.commit()
        
        print(f"✅ User is now an admin: {email}")
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1)
