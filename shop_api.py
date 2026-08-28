from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from sqlmodel import Session, select
from database import get_session
from models import Product, ShopOrder
from datetime import datetime

app = FastAPI(title="Makao Digital Hub - Shop Module (DB Edition)")

class OrderRequest(BaseModel):
    tenant_id: str
    product_id: str
    quantity: int = Field(..., gt=0)

@app.get("/api/v1/shop/products", response_model=List[Product])
def list_products(session: Session = Depends(get_session)):
    return session.exec(select(Product)).all()

@app.post("/api/v1/shop/orders", status_code=201)
def place_order(req: OrderRequest, session: Session = Depends(get_session)):
    product = session.get(Product, req.product_id)
    if not product or product.stock < req.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    product.stock -= req.quantity
    session.add(product)
    
    order = ShopOrder(
        tenant_id=req.tenant_id, product_name=product.name, 
        quantity=req.quantity, total_amount=product.price * req.quantity,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    session.add(order)
    session.commit()
    return {"message": "Order placed", "total": order.total_amount}