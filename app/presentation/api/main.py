from fastapi import APIRouter

from app.presentation.api.health import router as health_router
from app.presentation.api.transaction import router as transaction_router
from app.presentation.api.wallet import router as wallet_router

router = APIRouter(prefix="/api")
router.include_router(wallet_router)  # type: ignore
router.include_router(transaction_router)  # type: ignore
router.include_router(health_router)  # type: ignore
