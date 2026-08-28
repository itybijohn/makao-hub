from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User
import jwt
from datetime import datetime, timedelta
import bcrypt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Makao Digital Hub - Auth Module (Secure)")

# Allow the frontend (port 8000) to talk to this API (port 8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
SECRET_KEY = "makao_super_secret_production_key_change_this_later"
ALGORITHM = "HS256"

class RegisterReq(BaseModel):
    username: str
    password: str
    role: str

class LoginReq(BaseModel):
    username: str
    password: str

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@app.post("/api/v1/auth/register")
def register(req: RegisterReq, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == req.username)).first()
    if existing: 
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(req.password)
    new_user = User(username=req.username, password=hashed_password, role=req.role)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    token = jwt.encode(
        {"user_id": str(new_user.id), "role": new_user.role, "exp": datetime.utcnow() + timedelta(hours=24)}, 
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer", "user_id": str(new_user.id)}

@app.post("/api/v1/auth/login")
def login(req: LoginReq, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == req.username)).first()
    
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = jwt.encode(
        {"user_id": str(user.id), "role": user.role, "exp": datetime.utcnow() + timedelta(hours=24)}, 
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer", "user_id": str(user.id)}

@app.get("/api/v1/auth/verify")
def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")