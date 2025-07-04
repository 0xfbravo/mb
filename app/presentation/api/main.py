from fastapi import APIRouter

from app.presentation.api.health import router as health_router
from app.presentation.api.transaction import router as transaction_router
from app.presentation.api.wallet import router as wallet_router

router = APIRouter(prefix="/api")

# Include the separate routers
router.include_router(wallet_router)
router.include_router(transaction_router)
router.include_router(health_router)
