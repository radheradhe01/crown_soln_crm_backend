import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add the parent directory to sys.path to allow imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    # Fallback if app config is not ready
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/crm_dev?schema=public"
    )

async def verify_connection():
    print(f"🔌 Connecting to database...")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.connect() as conn:
            # Check connection
            result = await conn.execute(text("SELECT 1"))
            print("   ✅ Database connection successful")
            
            # Check tables
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            required_tables = ["User", "Lead"]
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"   ❌ Missing tables: {', '.join(missing_tables)}")
                sys.exit(1)
            else:
                print(f"   ✅ Required tables exist: {', '.join(required_tables)}")
                
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_connection())
