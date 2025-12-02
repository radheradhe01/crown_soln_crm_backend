import asyncio
from app.core.database import engine, Base
from app.models import * # Import models to ensure metadata is populated

async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Tables dropped.")

if __name__ == "__main__":
    asyncio.run(drop_tables())
