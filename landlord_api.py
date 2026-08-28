from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import uuid
from sqlmodel import Session, select
from database import get_session
from models import Property

app = FastAPI(title="Makao Digital Hub - Landlord Module (DB Edition)")

# --- GRASSROOTS: Enums ---
class PropertyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class MaintenanceStatus(str, Enum):
    REPORTED = "reported"
    LANDLORD_REVIEW = "landlord_review"
    FUNDI_ASSIGNED = "fundi_assigned"
    COMPLETED = "completed"

# --- GRASSROOTS: Pydantic Schemas ---
class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    location: str
    rent_amount: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)

class PropertyResponse(BaseModel):
    id: str
    title: str
    location: str
    rent_amount: float
    bedrooms: int
    status: str
    landlord_id: str

class ApplicationResponse(BaseModel):
    id: str
    property_id: str
    tenant_name: str
    status: ApplicationStatus
    credit_score: int

class MaintenanceRequest(BaseModel):
    property_id: str
    issue: str
    urgency: int = Field(..., ge=1, le=5)

class MaintenanceResponse(BaseModel):
    id: str
    property_id: str
    issue: str
    status: MaintenanceStatus
    fundi_id: str
    budget_released: float

# --- In-Memory DB (Only for Applications & Maintenance for now) ---
FAKE_DB = {"applications": {}, "maintenance": {}}

# --- THE TOP: Landlord API Routes ---

# 1. Portfolio (NOW USING REAL DATABASE)
@app.post("/api/v1/landlord/properties", response_model=PropertyResponse, status_code=201)
def create_property(data: PropertyCreate, session: Session = Depends(get_session)):
    new_prop = Property(
        title=data.title,
        location=data.location,
        rent_amount=data.rent_amount,
        bedrooms=data.bedrooms
    )
    session.add(new_prop)
    session.commit()
    session.refresh(new_prop)
    return new_prop

@app.get("/api/v1/landlord/properties", response_model=List[PropertyResponse])
def list_properties(session: Session = Depends(get_session)):
    properties = session.exec(select(Property)).all()
    return properties

# 2. Gatekeeping (Tenant Applications)
@app.get("/api/v1/landlord/applications/{property_id}", response_model=List[ApplicationResponse])
def view_applications(property_id: str):
    return [
        ApplicationResponse(id="app_1", property_id=property_id, tenant_name="John Doe", status=ApplicationStatus.PENDING, credit_score=750),
        ApplicationResponse(id="app_2", property_id=property_id, tenant_name="Jane Smith", status=ApplicationStatus.PENDING, credit_score=620)
    ]

@app.patch("/api/v1/landlord/applications/{app_id}/decide")
def decide_application(app_id: str, decision: ApplicationStatus):
    if decision not in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Must be APPROVED or REJECTED")
    return {"message": f"Application {app_id} marked as {decision}"}

# 3. Maintenance Dispatch (Fundi)
@app.post("/api/v1/landlord/maintenance/authorize", response_model=MaintenanceResponse)
def authorize_maintenance(req: MaintenanceRequest, fundi_id: str, budget: float):
    maint_id = str(uuid.uuid4())
    response = MaintenanceResponse(
        id=maint_id, property_id=req.property_id, issue=req.issue,
        status=MaintenanceStatus.FUNDI_ASSIGNED, fundi_id=fundi_id, budget_released=budget
    )
    FAKE_DB["maintenance"][maint_id] = response
    return response

# 4. Evidence/Report Review (The final 5%)
@app.get("/api/v1/landlord/maintenance/reports")
def view_tenant_reports():
    """Landlord views maintenance issues reported by tenants."""
    return [
        {"report_id": "rep_1", "property_id": "fdc39daf-2b12-44cf-9346-6e035573771a", "issue": "Broken AC", "status": "SUBMITTED_TO_LANDLORD"}
    ]