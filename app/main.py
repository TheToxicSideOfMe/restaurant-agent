from fastapi import FastAPI
from app.database import engine, Base
from app.api import Orders, chat
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Restaurant Ai Agent",
    description="AI-powered Restaurant customer service agent",
    version="1.0.0"
)

app.include_router(Orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

@app.get("/health")
def health():
    return {"status": "ok"}