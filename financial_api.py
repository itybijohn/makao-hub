from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import Transaction, UserBalance
from datetime import datetime
import uuid

app = FastAPI(title="Makao Digital Hub - Financial Engine (DB Edition)")

# --- GRASSROOTS: Data Models ---
class DepositRequest(BaseModel):
    payer_id: str
    amount: float = Field(..., gt=0)
    transaction_type: str
    purpose: str

class TransactionResponse(BaseModel):
    transaction_id: str
    payer_id: str
    payee_id: str
    amount: float
    type: str
    status: str
    created_at: str

class ReleaseRequest(BaseModel):
    transaction_id: str
    payee_id: str

class ReleaseResponse(BaseModel):
    transaction_id: str
    payee_id: str
    amount: float
    released_at: str
    status: str

# --- THE TOP: Financial API Routes ---

# 1. Deposit to Escrow (NOW USING REAL DATABASE)
@app.post("/api/v1/financial/deposit", response_model=TransactionResponse, status_code=201)
def deposit_to_escrow(req: DepositRequest, session: Session = Depends(get_session)):
    tx = Transaction(
        payer_id=req.payer_id,
        amount=req.amount,
        transaction_type=req.transaction_type,
        status="held_in_escrow",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    
    return TransactionResponse(
        transaction_id=tx.id,
        payer_id=tx.payer_id,
        payee_id=tx.payee_id,
        amount=tx.amount,
        type=tx.transaction_type,
        status=tx.status,
        created_at=tx.created_at
    )

# 2. Release from Escrow (NOW USING REAL DATABASE)
@app.patch("/api/v1/financial/release", response_model=ReleaseResponse)
def release_from_escrow(req: ReleaseRequest, session: Session = Depends(get_session)):
    tx = session.get(Transaction, req.transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.status != "held_in_escrow":
        raise HTTPException(status_code=400, detail="Transaction not in escrow")
    
    tx.status = "released"
    tx.payee_id = req.payee_id
    
    # Update or create payee balance
    balance = session.exec(select(UserBalance).where(UserBalance.user_id == req.payee_id)).first()
    if not balance:
        balance = UserBalance(user_id=req.payee_id, balance=0.0)
        session.add(balance)
    balance.balance += tx.amount
    
    session.add(tx)
    session.commit()
    
    return ReleaseResponse(
        transaction_id=tx.id,
        payee_id=tx.payee_id,
        amount=tx.amount,
        released_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="released"
    )

# 3. Check Balance (NOW USING REAL DATABASE)
@app.get("/api/v1/financial/balance/{user_id}")
def check_balance(user_id: str, session: Session = Depends(get_session)):
    balance = session.exec(select(UserBalance).where(UserBalance.user_id == user_id)).first()
    if not balance:
        return {"user_id": user_id, "balance": 0.0}
    return {"user_id": balance.user_id, "balance": balance.balance}