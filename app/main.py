from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base, get_db
from app.api import chat, orders
from app.services.rag_service import load_restaurant_data
from app.api.telegram import build_telegram_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables + seed knowledge base
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        load_restaurant_data(db)
    finally:
        db.close()

    # Start Telegram bot polling in the background
    telegram_app = build_telegram_app()
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

    yield

    # Graceful shutdown
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(
    title="Restaurant Agent API",
    lifespan=lifespan
)

app.include_router(chat.router, prefix="/api")
app.include_router(orders.router, prefix="/api")