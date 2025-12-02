import uuid
from datetime import datetime, UTC
from typing import List, Optional
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from app.core.database import Base

class PipelineStatus(str, enum.Enum):
    Unassigned = "Unassigned"
    Email_Sent = "Email_Sent"
    Client_Replied = "Client_Replied"
    Plan_Sent = "Plan_Sent"
    Rate_Finalized = "Rate_Finalized"
    Docs_Signed = "Docs_Signed"
    Testing = "Testing"
    Approved = "Approved"
    Rejected = "Rejected"

class Lead(Base):
    __tablename__ = "Lead"

    id: Mapped[str] = mapped_column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    frn: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    service_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    pipelineStatus: Mapped[PipelineStatus] = mapped_column(
        SQLEnum(PipelineStatus, name="PipelineStatus", create_type=False), 
        default=PipelineStatus.Unassigned, 
        index=True,
        nullable=False
    )
    
    history: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    
    assignedEmployeeId: Mapped[Optional[str]] = mapped_column(
        String, 
        ForeignKey("User.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(UTC), 
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    assigned_employee = relationship("User", back_populates="leads")
