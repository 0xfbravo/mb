from fastapi import APIRouter

# Tags
health_tag = "💊 Health check"

router = APIRouter(prefix="/health", tags=[health_tag])


@router.get("/", tags=[health_tag])
async def health():
    """
    Health check.
    """
    return {"message": "OK"}
