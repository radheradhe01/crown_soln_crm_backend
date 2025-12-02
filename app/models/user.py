import uuid
from datetime import datetime, UTC
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"

class User(Base):
    __tablename__ = "User"

    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False) # Hashed password
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="Role", create_type=False), default=Role.EMPLOYEE, nullable=False)
    
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(UTC), 
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    leads = relationship("Lead", back_populates="assigned_employee")
