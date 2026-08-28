from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import DeliveryJob

app = FastAPI(title="Makao Digital Hub - Delivery Module (DB Edition)")

class AcceptRequest(BaseModel):
    delivery_id: str
    agent_id: str

class CompleteRequest(BaseModel):
    delivery_id: str
    agent_id: str
    proof: str

@app.get("/api/v1/delivery/jobs", response_model=List[DeliveryJob])
def view_jobs(session: Session = Depends(get_session)):
    return session.exec(select(DeliveryJob).where(DeliveryJob.status == "pending")).all()

@app.patch("/api/v1/delivery/jobs/accept")
def accept_job(req: AcceptRequest, session: Session = Depends(get_session)):
    job = session.get(DeliveryJob, req.delivery_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    job.status = "accepted"
    job.agent_id = req.agent_id
    session.add(job)
    session.commit()
    return {"message": "Job accepted"}

@app.patch("/api/v1/delivery/jobs/complete")
def complete_job(req: CompleteRequest, session: Session = Depends(get_session)):
    job = session.get(DeliveryJob, req.delivery_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    job.status = "delivered"
    job.proof = req.proof
    session.add(job)
    session.commit()
    return {"message": "Job completed"}