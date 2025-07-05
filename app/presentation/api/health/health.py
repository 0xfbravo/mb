from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
health_tag = "💊 Health check"
router = APIRouter(prefix="/health", tags=[health_tag])


@router.get("/", tags=[health_tag])
async def health(di: Annotated[DependencyInjection, Depends(get_dependency_injection)]):
    """
    Health check.
    """
    # Check if database is initialized first
    if not di.is_database_initialized():
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        # Get pool statistics for monitoring
        pool_stats = await di.db_manager.get_pool_stats()

        return {
            "message": "Healthy",
            "database": {"status": "healthy", "pool_stats": pool_stats},
        }
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the error but return a more generic error message
        di.logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection error")
