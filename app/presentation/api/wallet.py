from fastapi import APIRouter, Body

from app.domain.wallet.models import Wallet

# Tags
wallet_tag = "🔐 Wallet"

router = APIRouter(prefix="/wallet", tags=[wallet_tag])


@router.post("/", tags=[wallet_tag])
async def create_wallet(wallet_name: str = Body(...)) -> Wallet:
    """
    This endpoint is responsible for creating multiple wallets,
    returning the address, private keys and public keys.
    """
    return Wallet(address="", name=wallet_name, balance=0.0)


@router.get("/{wallet_address}/balance", tags=[wallet_tag])
async def get_wallet_balance(wallet_address: str) -> float:
    """
    Get the balance of a given wallet address.
    """
    return 0.0
