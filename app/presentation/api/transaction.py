from fastapi import APIRouter

from app.domain.transaction.models import CreateTransaction, Transaction

# Tags
transaction_tag = "💰 Transaction"

router = APIRouter(prefix="/tx", tags=[transaction_tag])


@router.post("/", tags=[transaction_tag])
async def create_tx(tx: CreateTransaction):
    """
    Create a new transaction.
    """
    return {"message": "Tx created"}


@router.get("/{tx_hash}/validate", tags=[transaction_tag])
async def validate_tx(tx_hash: str, tx: Transaction):
    """
    Validate a transaction
    """
    return {"message": "Tx validated"}


@router.get("/history/{wallet_address}", tags=[transaction_tag])
async def get_wallet_tx_history(wallet_address: str) -> list[Transaction]:
    """
    Get the transaction history of a given wallet address.
    """
    return [
        Transaction(
            from_address=wallet_address,
            to_address=wallet_address,
            amount=100.0,
            gas_price=0.0001,
            gas_limit=100000,
            data="",
        )
    ]
