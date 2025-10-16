"""
Backend startup script for Railway deployment.
This script handles database migrations, seeding, and starting the server.

To enable/disable features, comment/uncomment the sections below.
"""

import os
import sys
import subprocess
from pathlib import Path

# ============================================================================
# CONFIGURATION - Comment/uncomment sections as needed
# ============================================================================

# Set to True to run migrations on startup
RUN_MIGRATIONS = False

# Set to True to seed database on startup (only runs if DB is empty)
RUN_SEEDING = False

# Set to True to create admin user (requires ADMIN_EMAIL env var)
CREATE_ADMIN = False

# ============================================================================
# FUNCTIONS
# ============================================================================

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False


def check_database_connection():
    """Check if database is accessible."""
    print("\n🔍 Checking database connection...")
    try:
        from app.config import settings
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def run_migrations():
    """Run Alembic migrations."""
    if not RUN_MIGRATIONS:
        print("\n⏭️  Skipping migrations (RUN_MIGRATIONS=False)")
        return True
    
    return run_command(
        "alembic upgrade head",
        "Running database migrations"
    )


def seed_database():
    """Seed the database with initial data."""
    if not RUN_SEEDING:
        print("\n⏭️  Skipping seeding (RUN_SEEDING=False)")
        return True
    
    # Check if database is already seeded
    try:
        from app.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        
        if user_count > 0:
            print("\n⏭️  Skipping seeding (database already has users)")
            return True
    except Exception as e:
        print(f"⚠️  Could not check if database is seeded: {e}")
    
    return run_command(
        "python scripts/seed.py",
        "Seeding database with initial data"
    )


def create_admin_user():
    """Create admin user if ADMIN_EMAIL is set."""
    if not CREATE_ADMIN:
        print("\n⏭️  Skipping admin creation (CREATE_ADMIN=False)")
        return True
    
    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        print("\n⚠️  Skipping admin creation (ADMIN_EMAIL not set)")
        return True
    
    return run_command(
        f"python scripts/create_admin.py {admin_email}",
        f"Creating admin user: {admin_email}"
    )


def start_server():
    """Start the Uvicorn server."""
    print("\n" + "="*60)
    print("🚀 Starting Uvicorn server...")
    print("="*60 + "\n")
    
    # Get port from environment or use default
    port = os.getenv("PORT", "8080")
    host = "0.0.0.0"
    
    # Start uvicorn (this will block)
    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", port,
        "--log-level", "info"
    ])


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🎯 LAUNCH LOOP BACKEND - STARTUP SCRIPT")
    print("="*60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check environment
    env = os.getenv("ENV", "development")
    print(f"🌍 Environment: {env}")
    
    # Step 1: Check database connection
    if not check_database_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        print("\n⚠️  Migrations failed, but continuing...")
    
    # Step 3: Seed database
    if not seed_database():
        print("\n⚠️  Seeding failed, but continuing...")
    
    # Step 4: Create admin user
    if not create_admin_user():
        print("\n⚠️  Admin creation failed, but continuing...")
    
    # Step 5: Start the server
    print("\n" + "="*60)
    print("✅ All startup tasks completed!")
    print("="*60)
    
    start_server()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
