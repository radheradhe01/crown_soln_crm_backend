import asyncio
import logging
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_factory
# Import models to ensure they are registered
import app.models
from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.models.user import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_admin():
    async with async_session_factory() as session:
        email = "admin@crm.com"
        password = "admin123456"
        
        existing_user = await user_crud.get_by_email(session, email=email)
        if existing_user:
            logger.info(f"Admin user {email} already exists.")
            return

        logger.info(f"Creating admin user {email}...")
        user_in = UserCreate(
            email=email,
            password=password,
            name="Admin User",
            role=Role.ADMIN
        )
        await user_crud.create(session, obj_in=user_in)
        logger.info("Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(create_admin())
