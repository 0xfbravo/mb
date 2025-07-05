from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.transaction.models import CreateTx, Transaction
from app.utils.di import DependencyInjection, get_dependency_injection

# Tags
transaction_tag = "💰 Transaction"

router = APIRouter(prefix="/tx", tags=[transaction_tag])


@router.post("/", tags=[transaction_tag])
async def create_tx(
    tx: CreateTx, di: Annotated[DependencyInjection, Depends(get_dependency_injection)]
) -> Transaction:
    """
    Create a new transaction.
    """
    di.ensure_database_initialized()
    return await di.tx_uc.create(tx)


@router.get("/{transaction_id}", tags=[transaction_tag])
async def get_transaction(
    transaction_id: str,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> Transaction:
    """
    Get transaction by ID.
    """
    di.ensure_database_initialized()
    return await di.tx_uc.get_by_id(transaction_id)


@router.get("/{tx_hash}", tags=[transaction_tag])
async def get_transaction_by_tx_hash(
    tx_hash: str, di: Annotated[DependencyInjection, Depends(get_dependency_injection)]
) -> Transaction:
    """
    Get transaction by transaction hash.
    """
    di.ensure_database_initialized()
    return await di.tx_uc.get_by_tx_hash(tx_hash)


@router.get("/wallet/{wallet_address}", tags=[transaction_tag])
async def get_wallet_transactions(
    wallet_address: str,
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
) -> list[Transaction]:
    """
    Get all transactions for a wallet.
    """
    di.ensure_database_initialized()
    return await di.tx_uc.get_txs(wallet_address)
