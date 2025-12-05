#!/usr/bin/env python3
"""
Database initialization script
Run this once before starting the application
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models import user, image, job, project  # Import all models


async def init_db():
    """Initialize database tables"""
    print("🔧 Initializing database...")
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            return True
        except Exception as e:
            if "Connection refused" in str(e) or "could not connect" in str(e).lower():
                print(f"⏳ Waiting for database... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
            elif "already exists" in str(e).lower():
                print("ℹ️ Tables already exist - OK")
                return True
            else:
                print(f"❌ Database error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    return False
    
    print("❌ Failed to initialize database after max retries")
    return False


if __name__ == "__main__":
    success = asyncio.run(init_db())
    sys.exit(0 if success else 1)
