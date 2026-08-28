from sqlmodel import SQLModel, Field
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str
    role: str
    phone: str = ""
    email: str = ""

class Property(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    location: str
    rent_amount: float
    bedrooms: int
    deposit: float = 0.0
    description: str = ""
    virtual_tour_url: str = ""
    status: str = "active"
    landlord_id: str = "landlord_123"

class TenantApplication(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    property_id: str
    tenant_id: str
    status: str = "pending"  # pending, approved, rejected
    message: str = ""