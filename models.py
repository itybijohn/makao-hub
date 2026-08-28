from sqlmodel import SQLModel, Field
import uuid

# 1. Landlord Module
class Property(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    location: str
    rent_amount: float
    bedrooms: int
    deposit: float = 0.0
    description: str = ""
    virtual_tour_url: str = ""
    status: str = "active"
    landlord_id: str = "landlord_123"

# 2. Tenant Module
class TenantApplication(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    property_id: str
    tenant_name: str
    status: str = "pending"
    credit_score: int = 0

# 3. Financial Module
class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    payer_id: str
    payee_id: str = ""
    amount: float
    transaction_type: str
    status: str = "held_in_escrow"
    created_at: str

class UserBalance(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(unique=True)
    balance: float = 0.0

# 4. Fundi Module
class FundiJob(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    property_id: str
    issue: str
    budget: float
    status: str = "available"
    fundi_id: str = ""
    evidence: str = ""

# 5. Gatekeeper Module
class Visitor(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    role: str
    destination: str
    gate_code: str = "MAKAO123"
    status: str = "expected"
    entry_time: str = ""

# 6. Shop Module
class Product(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    price: float
    stock: int

class ShopOrder(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str
    product_name: str
    quantity: int
    total_amount: float
    status: str = "pending"
    created_at: str

# 7. Delivery Module
class DeliveryJob(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    order_id: str
    customer_address: str
    total_amount: float
    status: str = "pending"
    agent_id: str = ""
    proof: str = ""

# 8. Auth Module
class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(unique=True)
    password: str
    role: str