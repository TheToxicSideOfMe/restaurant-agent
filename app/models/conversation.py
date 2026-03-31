from sqlalchemy import Column, String, Float, DateTime, Text
from pgvector.sqlalchemy import Vector
from app.database import Base
from datetime import datetime
import uuid

class Conversation(Base):
    __tablename__="conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, unique=True)
    messages = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)