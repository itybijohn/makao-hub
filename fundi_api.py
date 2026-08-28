from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import FundiJob
from datetime import datetime

app = FastAPI(title="Makao Digital Hub - Fundi Module (DB Edition)")

# --- GRASSROOTS: Data Models ---
class JobAcceptRequest(BaseModel):
    job_id: str
    fundi_id: str

class JobCompleteRequest(BaseModel):
    job_id: str
    fundi_id: str
    evidence_description: str

# --- THE TOP: Fundi API Routes ---

# 1. View Available Jobs (NOW USING REAL DATABASE)
@app.get("/api/v1/fundi/jobs", response_model=List[FundiJob])
def view_available_jobs(session: Session = Depends(get_session)):
    """Fundi browses available maintenance jobs."""
    jobs = session.exec(select(FundiJob).where(FundiJob.status == "available")).all()
    return jobs

# 2. Accept Job (NOW USING REAL DATABASE)
@app.patch("/api/v1/fundi/jobs/accept")
def accept_job(req: JobAcceptRequest, session: Session = Depends(get_session)):
    """Fundi accepts a specific job."""
    job = session.get(FundiJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "accepted"
    job.fundi_id = req.fundi_id
    session.add(job)
    session.commit()
    
    return {"message": "Job accepted", "job_id": job.id, "fundi_id": job.fundi_id, "status": job.status}

# 3. Complete Job (NOW USING REAL DATABASE)
@app.patch("/api/v1/fundi/jobs/complete")
def complete_job(req: JobCompleteRequest, session: Session = Depends(get_session)):
    """Fundi marks the job as done and provides evidence."""
    job = session.get(FundiJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "completed"
    job.fundi_id = req.fundi_id
    job.evidence = req.evidence_description
    session.add(job)
    session.commit()
    
    return {"message": "Job completed", "job_id": job.id, "evidence": job.evidence}

# Helper to seed a test job for the DB
@app.post("/api/v1/fundi/seed-test-job")
def seed_test_job(session: Session = Depends(get_session)):
    job = FundiJob(property_id="prop_1", issue="Leaking pipe", budget=15000.0)
    session.add(job)
    session.commit()
    return {"message": "Test job created"}