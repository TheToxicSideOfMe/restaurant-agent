from fastapi import APIRouter

router = APIRouter()

router.get("/orders")
async def getchat():
    return "healthy"