from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base, get_db
from app.api import chat, orders
from app.services.rag_service import load_restaurant_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup
    Base.metadata.create_all(bind=engine)

    # Load restaurant data into pgvector if not already loaded
    db = next(get_db())
    try:
        load_restaurant_data(db)
    finally:
        db.close()

    yield
    # anything after yield runs on shutdown — nothing needed here


app = FastAPI(
    title="Restaurant Agent API",
    lifespan=lifespan
)

app.include_router(chat.router, prefix="/api")
app.include_router(orders.router, prefix="/api")