from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import Property, TenantApplication, FundiJob, UserBalance
import jwt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Makao Digital Hub - Integrated Platform (DB Edition)")
security = HTTPBearer()
SECRET_KEY = "makao_super_secret_production_key_change_this_later"
ALGORITHM = "HS256"

# Allow CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper: Verify Auth Token ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- THE TOP: Unified Dashboards ---

# 1. Landlord Dashboard
@app.get("/api/v1/dashboard/landlord")
def landlord_dashboard(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    properties = session.exec(select(Property).where(Property.landlord_id == user["user_id"])).all()
    applications = session.exec(select(TenantApplication).where(TenantApplication.status == "pending")).all()
    balance_obj = session.exec(select(UserBalance).where(UserBalance.user_id == user["user_id"])).first()
    balance = balance_obj.balance if balance_obj else 0.0

    return {
        "user": user,
        "my_properties": [p.model_dump() for p in properties],
        "pending_applications": [a.model_dump() for a in applications],
        "real_balance": balance,
        "message": "Live data pulled from makao_hub.db"
    }

# 2. Tenant Dashboard
@app.get("/api/v1/dashboard/tenant")
def tenant_dashboard(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    properties = session.exec(select(Property)).all()
    applications = session.exec(select(TenantApplication)).all() 

    return {
        "user": user,
        "available_properties": [p.model_dump() for p in properties],
        "my_applications": [a.model_dump() for a in applications],
        "message": "Live data pulled from makao_hub.db"
    }

# 3. Fundi Dashboard
@app.get("/api/v1/dashboard/fundi")
def fundi_dashboard(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    jobs = session.exec(select(FundiJob).where(FundiJob.status == "available")).all()
    
    return {
        "user": user,
        "available_jobs": [j.model_dump() for j in jobs],
        "message": "Live data pulled from makao_hub.db"
    }

# 4. System Health
@app.get("/api/v1/system/health")
def system_health():
    return {
        "status": "operational",
        "database": "makao_hub.db (SQLite)",
        "modules": ["Landlord", "Tenant", "Fundi", "Gatekeeper", "Shop", "Delivery", "Financial", "Auth"]
    }

# --- NEW BRICK: Create Property (UPDATED WITH NEW FIELDS) ---
class PropertyCreate(BaseModel):
    title: str
    location: str
    rent_amount: float
    bedrooms: int
    deposit: float = 0.0
    description: str = ""
    virtual_tour_url: str = ""

@app.post("/api/v1/landlord/properties", status_code=201)
def create_property(data: PropertyCreate, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    """Create a new property from the frontend."""
    new_prop = Property(
        title=data.title,
        location=data.location,
        rent_amount=data.rent_amount,
        bedrooms=data.bedrooms,
        deposit=data.deposit,
        description=data.description,
        virtual_tour_url=data.virtual_tour_url,
        landlord_id=user["user_id"] # Links property to the logged-in user!
    )
    session.add(new_prop)
    session.commit()
    session.refresh(new_prop)
    return {"message": "Property added successfully", "property": new_prop.model_dump()}

# 5. Serve the Frontend UI
@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")