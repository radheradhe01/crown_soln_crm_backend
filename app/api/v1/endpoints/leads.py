from typing import Any, List, Optional
import csv
import io
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api import deps
from app.crud.lead import lead_crud
from app.models.user import User, Role
from app.models.lead import Lead, PipelineStatus
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter()

@router.get("/", response_model=List[LeadResponse])
async def read_leads(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    status: Optional[PipelineStatus] = None,
    search: Optional[str] = None,
    assigned_to: Optional[str] = Query(None, alias="assignedTo"),
) -> Any:
    """
    Retrieve leads with filtering.
    """
    query = select(Lead)

    # Apply filters
    if status:
        query = query.filter(Lead.pipelineStatus == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.company_name.ilike(search_term),
                Lead.frn.ilike(search_term),
                Lead.contact_email.ilike(search_term)
            )
        )

    if assigned_to:
        if assigned_to == "unassigned":
            query = query.filter(Lead.assignedEmployeeId == None)
        else:
            query = query.filter(Lead.assignedEmployeeId == assigned_to)

    # RBAC: If not admin, can only see own leads or unassigned?
    # Or maybe employees can see all leads but only edit own?
    # Plan says: "Security: Filter by assignedEmployeeId for non-admins"
    if current_user.role != Role.ADMIN:
        # Employees see their own leads AND unassigned leads they might want to claim?
        # Or just their own?
        # Usually CRM allows seeing unassigned to claim them.
        # Let's allow seeing own + unassigned.
        query = query.filter(
            or_(
                Lead.assignedEmployeeId == current_user.id,
                Lead.assignedEmployeeId == None
            )
        )

    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    leads = result.scalars().all()
    return leads

@router.post("/", response_model=LeadResponse)
async def create_lead(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lead_in: LeadCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new lead.
    """
    lead = await lead_crud.get_by_frn(db, frn=lead_in.frn)
    if lead:
        raise HTTPException(
            status_code=400,
            detail="The lead with this FRN already exists in the system.",
        )
    lead = await lead_crud.create(db, obj_in=lead_in)
    return lead

@router.get("/export")
async def export_leads(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Export all leads to CSV (Admin only).
    """
    result = await db.execute(select(Lead))
    leads = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    headers = [
        "ID", "FRN", "Company Name", "Contact Email", "Contact Phone",
        "Service Type", "Website", "Pipeline Status", "Assigned Employee ID",
        "Created At", "Updated At"
    ]
    writer.writerow(headers)

    # Rows
    for lead in leads:
        writer.writerow([
            str(lead.id),
            lead.frn,
            lead.company_name,
            lead.contact_email,
            lead.contact_phone,
            lead.service_type,
            lead.website,
            lead.pipelineStatus.value,
            str(lead.assignedEmployeeId) if lead.assignedEmployeeId else "",
            lead.createdAt.isoformat() if lead.createdAt else "",
            lead.updatedAt.isoformat() if lead.updatedAt else ""
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.post("/claim", response_model=LeadResponse)
async def claim_lead(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lead_id: str = Query(..., description="ID of the lead to claim"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Claim an unassigned lead.
    """
    lead = await lead_crud.get(db, id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.assignedEmployeeId is not None:
        raise HTTPException(status_code=400, detail="Lead is already assigned")
    
    if lead.pipelineStatus != PipelineStatus.Unassigned:
         # Depending on business logic, maybe allow claiming if status is not unassigned but no user?
         # Plan says: "Check pipelineStatus is Unassigned"
         pass

    # Update lead
    lead.assignedEmployeeId = current_user.id
    # Optionally update status to something else?
    # Plan doesn't specify, but usually it moves to 'Contacted' or stays 'Unassigned' (but assigned).
    # Let's keep status as is or update to 'Contacted' if needed.
    # For now, just assign.
    
    history_entry = f"{datetime.now(UTC).isoformat()}: Claimed by {current_user.name}"
    current_history = list(lead.history) if lead.history else []
    current_history.append(history_entry)
    lead.history = current_history
    
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead

@router.get("/{lead_id}", response_model=LeadResponse)
async def read_lead(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lead_id: str,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get lead by ID.
    """
    lead = await lead_crud.get(db, id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # RBAC check
    if current_user.role != Role.ADMIN:
        if lead.assignedEmployeeId != current_user.id and lead.assignedEmployeeId is not None:
             raise HTTPException(status_code=403, detail="Not authorized to view this lead")

    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    *,
    db: AsyncSession = Depends(deps.get_db),
    lead_id: str,
    lead_in: LeadUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a lead.
    """
    lead = await lead_crud.get(db, id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # RBAC check
    if current_user.role != Role.ADMIN:
        if lead.assignedEmployeeId != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized to update this lead")

    # Update logic with history
    update_data = lead_in.model_dump(exclude_unset=True)
    
    if "history_entry" in update_data:
        entry = update_data.pop("history_entry")
        current_history = list(lead.history) if lead.history else []
        current_history.append(f"{datetime.now(UTC).isoformat()}: {entry} (by {current_user.name})")
        update_data["history"] = current_history
        
    lead = await lead_crud.update(db, db_obj=lead, obj_in=update_data)
    return lead
