from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.lead import Lead, PipelineStatus
from app.schemas.lead import LeadCreate, LeadUpdate

class CRUDLead(CRUDBase[Lead, LeadCreate, LeadUpdate]):
    async def get_by_frn(self, db: AsyncSession, *, frn: str) -> Optional[Lead]:
        result = await db.execute(select(Lead).filter(Lead.frn == frn))
        return result.scalars().first()
    
    async def get_unassigned(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Lead]:
        result = await db.execute(
            select(Lead)
            .filter(Lead.pipelineStatus == PipelineStatus.Unassigned)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
        
    async def get_by_employee(
        self, db: AsyncSession, *, employee_id: str, skip: int = 0, limit: int = 100
    ) -> List[Lead]:
        result = await db.execute(
            select(Lead)
            .filter(Lead.assignedEmployeeId == employee_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

lead_crud = CRUDLead(Lead)
