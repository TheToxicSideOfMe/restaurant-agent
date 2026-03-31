from sqlalchemy import Column, String, Float, DateTime, Text
from app.database import Base
from datetime import datetime
import uuid

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_address = Column(String, nullable=False)
    items = Column(Text,nullable=False)
    total_price = Column(Float)
    status = Column(String, default="pending")  # pending, confirmed, delivered
    created_at = Column(DateTime, default=datetime.utcnow)