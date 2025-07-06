from fastapi import APIRouter

from .health import router as health_router
from .transaction import router as transaction_router
from .wallet import router as wallet_router

api_router = APIRouter(prefix="/api")
api_router.include_router(wallet_router)
api_router.include_router(transaction_router)
api_router.include_router(health_router)
