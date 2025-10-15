#!/usr/bin/env python3
"""
Script to seed test data for development.
Usage: python scripts/seed.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path (backend/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.user import User, Role, Tier, PaymentStatus
from app.models.project import Project, ProjectStatus
from app.services.auth import hash_password
from app.utils.helpers import generate_uuid, get_usage_reset_date


def seed_data():
    """Seed test users and projects"""
    
    db = SessionLocal()
    
    try:
        print("🌱 Seeding test data...")
        
        # Check if data already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("ℹ️  Test data already exists. Skipping...")
            return
        
        # Create test users
        users = []
        
        # Free tier user
        free_user = User(
            id=generate_uuid(),
            email="free@example.com",
            password_hash=hash_password("password123"),
            tier=Tier.FREE,
            role=Role.USER,
            payment_status=PaymentStatus.ACTIVE,
            usage_reset_date=get_usage_reset_date(),
            generations_used_this_month=0,
            revisions_used_this_month=0
        )
        db.add(free_user)
        users.append(free_user)
        
        # Pro tier user
        pro_user = User(
            id=generate_uuid(),
            email="pro@example.com",
            password_hash=hash_password("password123"),
            tier=Tier.PRO,
            role=Role.USER,
            payment_status=PaymentStatus.ACTIVE,
            usage_reset_date=get_usage_reset_date(),
            generations_used_this_month=1,
            revisions_used_this_month=3
        )
        db.add(pro_user)
        users.append(pro_user)
        
        # Ultimate tier user
        ultimate_user = User(
            id=generate_uuid(),
            email="ultimate@example.com",
            password_hash=hash_password("password123"),
            tier=Tier.ULTIMATE,
            role=Role.USER,
            payment_status=PaymentStatus.ACTIVE,
            usage_reset_date=get_usage_reset_date(),
            generations_used_this_month=10,
            revisions_used_this_month=50
        )
        db.add(ultimate_user)
        users.append(ultimate_user)
        
        # Admin user
        admin_user = User(
            id=generate_uuid(),
            email="admin@example.com",
            password_hash=hash_password("password123"),
            tier=Tier.ULTIMATE,
            role=Role.ADMIN,
            payment_status=PaymentStatus.ACTIVE,
            usage_reset_date=get_usage_reset_date(),
            generations_used_this_month=0,
            revisions_used_this_month=0
        )
        db.add(admin_user)
        users.append(admin_user)
        
        db.commit()
        
        # Create test projects
        # Draft project for free user
        draft_project = Project(
            id=generate_uuid(),
            user_id=free_user.id,
            name="My First Product",
            status=ProjectStatus.DRAFT
        )
        db.add(draft_project)
        
        # Published project for pro user
        published_project = Project(
            id=generate_uuid(),
            user_id=pro_user.id,
            name="SaaS Landing Page",
            status=ProjectStatus.PUBLISHED,
            subdomain="test-saas",
            template_id="problem-first",
            html_content="<html><body><h1>Test Landing Page</h1></body></html>",
            signups_count=5,
            published_at=datetime.utcnow()
        )
        db.add(published_project)
        
        # Multiple projects for ultimate user
        for i in range(3):
            project = Project(
                id=generate_uuid(),
                user_id=ultimate_user.id,
                name=f"Product {i + 1}",
                status=ProjectStatus.GENERATED if i == 0 else ProjectStatus.PUBLISHED,
                subdomain=f"test-product-{i+1}" if i > 0 else None,
                template_id="problem-first",
                signups_count=i * 2
            )
            db.add(project)
        
        db.commit()
        
        print("\n✅ Test data seeded successfully!\n")
        print("Test accounts:")
        print("  Free user:     free@example.com / password123")
        print("  Pro user:      pro@example.com / password123")
        print("  Ultimate user: ultimate@example.com / password123")
        print("  Admin user:    admin@example.com / password123")
        print()
    
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
