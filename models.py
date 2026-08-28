from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str
    role: str

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
       status: str = "pending"
       message: str = ""  

class FundiJob(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    property_id: str
    description: str
    status: str = "available"

class UserBalance(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(unique=True, index=True)
    balance: float = 0.0