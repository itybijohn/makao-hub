from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import Visitor
from datetime import datetime

app = FastAPI(title="Makao Digital Hub - Gatekeeper Module (DB Edition)")

# --- GRASSROOTS: Data Models ---
class VerifyRequest(BaseModel):
    visitor_id: str
    gate_code: str

class LogEntry(BaseModel):
    log_id: str
    visitor_id: str
    name: str
    entry_time: str
    status: str

# --- THE TOP: Gatekeeper API Routes ---

# 1. View Expected Visitors (NOW USING REAL DATABASE)
@app.get("/api/v1/gatekeeper/expected", response_model=List[Visitor])
def get_expected_visitors(session: Session = Depends(get_session)):
    """Gatekeeper sees who is scheduled to enter the property today."""
    visitors = session.exec(select(Visitor).where(Visitor.status == "expected")).all()
    return visitors

# 2. Verify and Grant Entry (NOW USING REAL DATABASE)
@app.post("/api/v1/gatekeeper/verify", response_model=LogEntry)
def verify_entry(req: VerifyRequest, session: Session = Depends(get_session)):
    """Gatekeeper checks the visitor's ID and security code."""
    if req.gate_code != "MAKAO123":
        raise HTTPException(status_code=403, detail="Invalid Gate Code - Access Denied")
    
    visitor = session.get(Visitor, req.visitor_id)
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not on the expected list")
    
    visitor.status = "entered"
    visitor.entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.add(visitor)
    session.commit()
    
    return LogEntry(
        log_id=visitor.id,
        visitor_id=visitor.id,
        name=visitor.name,
        entry_time=visitor.entry_time,
        status="GRANTED"
    )

# Helper to seed a test visitor for the DB
@app.post("/api/v1/gatekeeper/seed-test-visitor")
def seed_test_visitor(session: Session = Depends(get_session)):
    visitor = Visitor(name="Pizza Delivery", role="Delivery", destination="Westlands Studio")
    session.add(visitor)
    session.commit()
    return {"message": "Test visitor created"}