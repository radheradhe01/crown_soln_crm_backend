from typing import Any, List, Dict
import shutil
from pathlib import Path
import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.api import deps
from app.crud.user import user_crud
from app.models.user import User
from app.models.lead import Lead, PipelineStatus
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.utils.csv_parser import parse_csv

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Retrieve users.
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/users", response_model=UserResponse)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Create new user.
    """
    user = await user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await user_crud.create(db, obj_in=user_in)
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Update a user.
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = await user_crud.update(db, db_obj=user, obj_in=user_in)
    return user

# Metrics Endpoint
@router.get("/metrics")
async def get_metrics(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Get admin metrics:
    - Leads by status
    - Leads by employee
    """
    # Leads by Status
    status_query = select(Lead.pipelineStatus, func.count(Lead.id)).group_by(Lead.pipelineStatus)
    status_result = await db.execute(status_query)
    leads_by_status = {status.value: count for status, count in status_result.all()}
    
    # Ensure all statuses are present with 0 count if missing
    for status in PipelineStatus:
        if status.value not in leads_by_status:
            leads_by_status[status.value] = 0

    # Leads by Employee
    employee_query = select(
        User.name, 
        func.count(Lead.id)
    ).join(
        Lead, Lead.assignedEmployeeId == User.id
    ).group_by(User.name)
    
    employee_result = await db.execute(employee_query)
    leads_by_employee = {name: count for name, count in employee_result.all()}

    # Unassigned count
    unassigned_query = select(func.count(Lead.id)).where(Lead.assignedEmployeeId == None)
    unassigned_result = await db.execute(unassigned_query)
    unassigned_count = unassigned_result.scalar_one_or_none() or 0
    leads_by_employee["Unassigned"] = unassigned_count

    status_data = [{"name": k, "value": v} for k, v in leads_by_status.items()]
    employee_data = [{"name": k, "value": v} for k, v in leads_by_employee.items()]

    return {
        "totalLeads": sum(leads_by_status.values()),
        "statusData": status_data,
        "employeeData": employee_data,
    }

# Upload CSV
@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Upload a CSV file for processing.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}_{file.filename}"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"file_id": file_id, "filename": file.filename, "path": str(file_path.absolute())}

# Process CSV
@router.post("/process-csv")
async def process_csv(
    file_path: str = Body(..., embed=True),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Process an uploaded CSV file.
    """
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    content = path.read_bytes()
    
    try:
        records = parse_csv(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
        
    processed_count = 0
    errors = []
    seen_frns = set()
    
    for idx, record in enumerate(records):
        try:
            # Validate required fields
            frn = (record.get("frn") or "").strip()
            if not frn:
                continue

            # Check for duplicate in current batch
            if frn in seen_frns:
                errors.append(f"Row {idx+1}: Duplicate FRN in CSV {frn}")
                continue

            # Check for existing FRN in database
            existing_lead = await db.execute(select(Lead).where(Lead.frn == frn))
            if existing_lead.scalar_one_or_none():
                errors.append(f"Row {idx+1}: Duplicate FRN in DB {frn}")
                continue
                
            # Create Lead
            lead_data = {
                "frn": frn,
                "company_name": record.get("company_name", "Unknown"),
                "contact_email": record.get("contact_email"),
                "contact_phone": record.get("contact_phone"),
                "service_type": record.get("service_type"),
                "website": record.get("website"),
                "notes": record.get("notes"),
                "pipelineStatus": PipelineStatus.Unassigned, # Default
                "history": [f"Imported from CSV on {datetime.now(UTC).isoformat()}"]
            }
            
            # Handle pipeline status if provided
            if "pipeline_status" in record and record["pipeline_status"]:
                try:
                    status = PipelineStatus(record["pipeline_status"])
                    lead_data["pipelineStatus"] = status
                except ValueError:
                    pass # Keep default Unassigned
            
            new_lead = Lead(**lead_data)
            db.add(new_lead)
            seen_frns.add(frn)
            processed_count += 1
            
        except Exception as e:
            errors.append(f"Row {idx+1}: {str(e)}")
            
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        errors.append(f"Commit failed: {str(e)}")

    return {
        "message": "CSV processing complete",
        "processed_count": processed_count,
        "errors": errors
    }
