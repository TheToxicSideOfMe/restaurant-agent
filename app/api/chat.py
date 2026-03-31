from fastapi import APIRouter

router = APIRouter()

router.get("/chat")
async def getchat():
    return "healthy"