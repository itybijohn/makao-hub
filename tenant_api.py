from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
import uuid
from sqlmodel import Session, select
from database import get_session
from models import TenantApplication

app = FastAPI(title="Makao Digital Hub - Tenant Module (DB Edition)")

# --- GRASSROOTS: Data Models ---
class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PropertyView(BaseModel):
    id: str
    title: str
    location: str
    rent_amount: float

class ApplicationCreate(BaseModel):
    property_id: str
    tenant_name: str

class ApplicationResponse(BaseModel):
    id: str
    property_id: str
    tenant_name: str
    status: str
    credit_score: int

# --- In-Memory DB (Only for browsing properties for now) ---
FAKE_PROPERTIES = [
    {"id": "prop_1", "title": "3 Bed Villa in Karen", "location": "Karen", "rent_amount": 36500.0},
    {"id": "prop_2", "title": "1 Bed Studio in Westlands", "location": "Westlands", "rent_amount": 25000.0}
]

# --- THE TOP: Tenant API Routes ---
# 1. Browse (Still using fake data for property listings)
@app.get("/api/v1/tenant/properties", response_model=List[PropertyView])
def browse_properties():
    return FAKE_PROPERTIES

# 2. Apply (NOW USING REAL DATABASE)
@app.post("/api/v1/tenant/applications", response_model=ApplicationResponse, status_code=201)
def submit_application(app_data: ApplicationCreate, session: Session = Depends(get_session)):
    # Simulate a credit score check
    import random
    score = random.randint(600, 800)
    
    new_app = TenantApplication(
        property_id=app_data.property_id,
        tenant_name=app_data.tenant_name,
        status="pending",
        credit_score=score
    )
    session.add(new_app)
    session.commit()
    session.refresh(new_app)
    
    return ApplicationResponse(
        id=new_app.id,
        property_id=new_app.property_id,
        tenant_name=new_app.tenant_name,
        status=new_app.status,
        credit_score=new_app.credit_score
    )

# 3. Track (NOW USING REAL DATABASE)
@app.get("/api/v1/tenant/applications/{app_id}", response_model=ApplicationResponse)
def track_application(app_id: str, session: Session = Depends(get_session)):
    app = session.get(TenantApplication, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return ApplicationResponse(
        id=app.id,
        property_id=app.property_id,
        tenant_name=app.tenant_name,
        status=app.status,
        credit_score=app.credit_score
    )