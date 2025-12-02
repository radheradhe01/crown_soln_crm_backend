from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.lead import PipelineStatus
from app.schemas.user import UserResponse

# Shared properties
class LeadBase(BaseModel):
    frn: Optional[str] = None
    company_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_type: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    pipelineStatus: Optional[PipelineStatus] = PipelineStatus.Unassigned
    assignedEmployeeId: Optional[str] = None

# Properties to receive via API on creation
class LeadCreate(LeadBase):
    frn: str
    company_name: str

# Properties to receive via API on update
class LeadUpdate(LeadBase):
    history_entry: Optional[str] = None # Helper to append to history

class LeadInDBBase(LeadBase):
    id: str
    history: List[str] = []
    createdAt: datetime
    updatedAt: datetime
    
    # Include the relationship data if needed, but be careful with circular deps
    assigned_employee: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class LeadResponse(LeadInDBBase):
    pass

# Additional properties stored in DB
class LeadInDB(LeadInDBBase):
    pass
