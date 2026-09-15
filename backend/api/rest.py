from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "jarvis", "version": "0.1.0"}
