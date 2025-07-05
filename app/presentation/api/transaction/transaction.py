from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.domain.transaction.models import CreateTx, Transaction, TransactionsPagination
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


@router.get("/", tags=[transaction_tag])
async def get_transactions(
    di: Annotated[DependencyInjection, Depends(get_dependency_injection)],
    transaction_id: Annotated[Optional[str], Query(description="Transaction ID to search by")] = None,
    tx_hash: Annotated[Optional[str], Query(description="Transaction hash to search by")] = None,
    wallet_address: Annotated[Optional[str], Query(description="Wallet address to get transactions for")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (only used when no specific filters are provided)")] = 1,
    limit: Annotated[int, Query(ge=1, le=1000, description="Number of items to return in a page")] = 10,
) -> Transaction | TransactionsPagination:
    """
    Get transactions with flexible query parameters.
    
    - Use `transaction_id` to get a specific transaction by ID
    - Use `tx_hash` to get a specific transaction by hash
    - Use `wallet_address` to get all transactions for a wallet
    - Use `page` and `limit` to get paginated transactions (when no specific filters are provided)
    
    Only one filter should be used at a time. If multiple filters are provided, 
    the priority order is: transaction_id > tx_hash > wallet_address > pagination.
    """
    di.ensure_database_initialized()
    
    if transaction_id:
        return await di.tx_uc.get_by_id(transaction_id)
    elif tx_hash:
        return await di.tx_uc.get_by_tx_hash(tx_hash)
    elif wallet_address:
        return await di.tx_uc.get_txs(wallet_address)
    else:
        return await di.tx_uc.get_all(page=page, limit=limit)
