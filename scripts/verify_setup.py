import asyncio
import sys
import os
import httpx

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def verify_setup():
    print("🔍 Verifying complete setup...")
    
    # 1. Check Database Connection
    print("\n1️⃣  Checking Database Connection...")
    exit_code = os.system("python scripts/verify_db_connection.py")
    if exit_code != 0:
        print("❌ Database connection failed")
        sys.exit(1)
        
    # 2. Check Dependencies
    print("\n2️⃣  Checking Dependencies...")
    try:
        import fastapi
        import sqlalchemy
        import alembic
        print("✅ Dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        sys.exit(1)

    # 3. Check Environment Variables
    print("\n3️⃣  Checking Environment Variables...")
    if not os.path.exists(".env"):
        print("❌ .env file missing")
        sys.exit(1)
    print("✅ .env file exists")

    print("\n✨ All checks passed! Backend is ready.")

if __name__ == "__main__":
    asyncio.run(verify_setup())
