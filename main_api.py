from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session, create_db_and_tables
from models import Property, TenantApplication, FundiJob, UserBalance, User
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Makao Digital Hub - Integrated Platform")

security = HTTPBearer()
SECRET_KEY = "makao_super_secret_production_key_change_this_later"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- MODELS FOR AUTH & PROPERTIES ---
class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "landlord"

class UserLogin(BaseModel):
    username: str
    password: str

class PropertyCreate(BaseModel):
    title: str
    location: str
    rent_amount: float
    bedrooms: int
    deposit: float = 0.0
    description: str = ""
    image_url: str = ""
    virtual_tour_url: str = ""

class ApplicationCreate(BaseModel):
    property_id: str
    message: str = ""

class ApplicationUpdate(BaseModel):
    status: str

# --- AUTH ENDPOINTS ---
@app.post("/api/v1/auth/register", status_code=201)
def register_user(data: UserRegister, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(username=data.username, password=get_password_hash(data.password), role=data.role)
    session.add(new_user)
    session.commit()
    return {"message": "User registered successfully"}

@app.post("/api/v1/auth/login")
def login_user(data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == data.username)).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    payload = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "role": user.role}

# --- DASHBOARDS ---
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
        "message": "Live data pulled from database"
    }

@app.get("/api/v1/dashboard/tenant")
def tenant_dashboard(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    properties = session.exec(select(Property)).all()
    applications = session.exec(select(TenantApplication).where(TenantApplication.tenant_id == user["user_id"])).all()
    return {
        "user": user,
        "available_properties": [p.model_dump() for p in properties],
        "my_applications": [a.model_dump() for a in applications],
        "message": "Live data pulled from database"
    }

@app.get("/api/v1/dashboard/fundi")
def fundi_dashboard(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    jobs = session.exec(select(FundiJob).where(FundiJob.status == "available")).all()
    return {
        "user": user,
        "available_jobs": [j.model_dump() for j in jobs],
        "message": "Live data pulled from database"
    }

@app.get("/api/v1/system/health")
def system_health():
    return {"status": "operational", "database": "Connected"}

# --- PROPERTY ENDPOINTS ---
@app.post("/api/v1/landlord/properties", status_code=201)
def create_property(data: PropertyCreate, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
        new_prop = Property(
        title=data.title, location=data.location, rent_amount=data.rent_amount,
        bedrooms=data.bedrooms, deposit=data.deposit, description=data.description,
        image_url=data.image_url, virtual_tour_url=data.virtual_tour_url, landlord_id=user["user_id"]
    )
    session.add(new_prop)
    session.commit()
    session.refresh(new_prop)
    return {"message": "Property added successfully", "property": new_prop.model_dump()}

@app.get("/api/v1/properties")
def get_public_properties(session: Session = Depends(get_session)):
    properties = session.exec(select(Property)).all()
    return [p.model_dump() for p in properties]

# --- APPLICATION ENDPOINTS ---
@app.post("/api/v1/applications", status_code=201)
def create_application(data: ApplicationCreate, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    existing = session.exec(select(TenantApplication).where(TenantApplication.property_id == data.property_id, TenantApplication.tenant_id == user["user_id"])).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied for this property")
    new_app = TenantApplication(property_id=data.property_id, tenant_id=user["user_id"], message=data.message, status="pending")
    session.add(new_app)
    session.commit()
    session.refresh(new_app)
    return {"message": "Application submitted successfully!", "application": new_app.model_dump()}

@app.get("/api/v1/landlord/applications")
def get_landlord_applications(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    my_properties = session.exec(select(Property).where(Property.landlord_id == user["user_id"])).all()
    my_property_ids = [p.id for p in my_properties]
    if not my_property_ids: return []
    applications = session.exec(select(TenantApplication).where(TenantApplication.property_id.in_(my_property_ids))).all()
    result = []
    for app in applications:
        prop = next((p for p in my_properties if p.id == app.property_id), None)
        app_dict = app.model_dump()
        app_dict["property_title"] = prop.title if prop else "Unknown Property"
        result.append(app_dict)
    return result

@app.get("/api/v1/tenant/applications")
def get_tenant_applications(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    applications = session.exec(select(TenantApplication).where(TenantApplication.tenant_id == user["user_id"])).all()
    result = []
    for app in applications:
        prop = session.get(Property, app.property_id)
        app_dict = app.model_dump()
        app_dict["property_title"] = prop.title if prop else "Unknown Property"
        result.append(app_dict)
    return result

@app.patch("/api/v1/landlord/applications/{application_id}")
def update_application_status(application_id: str, data: ApplicationUpdate, user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    app = session.get(TenantApplication, application_id)
    if not app: raise HTTPException(status_code=404, detail="Application not found")
    prop = session.get(Property, app.property_id)
    if not prop or prop.landlord_id != user["user_id"]: raise HTTPException(status_code=403, detail="Not authorized")
    app.status = data.status
    session.add(app)
    session.commit()
    session.refresh(app)
    return {"message": f"Application {data.status}", "application": app.model_dump()}

# --- SERVE FRONTEND ---
@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

# --- STARTUP ---
create_db_and_tables()