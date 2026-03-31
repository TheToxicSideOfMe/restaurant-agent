from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json

from app.database import get_db
from app.models.order import Order

router = APIRouter()


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    customer_address: str
    items: list
    total_price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/orders", response_model=list[OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()

    # Deserialize items JSON string → list before returning
    for order in orders:
        if isinstance(order.items, str):
            order.items = json.loads(order.items)

    return orders