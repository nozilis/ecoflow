from fastapi import APIRouter, status, Depends, HTTPException
from dependencies import get_transaction_service
from schemas import TransactionCreate, TransactionResponse, TransactionUpdate
from services.transaction_core import TransactionService, TransactionNotFound, InvalidCategory

router = APIRouter(
    prefix='/transactions',
    tags=['transactions']
)

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate, 
    transaction_service: TransactionService = Depends(get_transaction_service)
) -> TransactionResponse:
    created_transaction = await transaction_service.create_transaction(
        amount=transaction.amount, 
        transaction_type=transaction.transaction_type,
        category=transaction.category,
        description=transaction.description,
        )
    return TransactionResponse.model_validate(created_transaction)

@router.get('/', status_code=status.HTTP_200_OK)
async def get_transactions(
    transaction_service: TransactionService = Depends(get_transaction_service),
    page: int = 1, 
    page_size: int = 20
) -> list[TransactionResponse]:
    transactions = await transaction_service.get_transactions(
        page=page, 
        page_size=page_size
        )
    return [TransactionResponse.model_validate(t) for t in transactions]

@router.delete('/{transaction_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int, 
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    try:
        await transaction_service.delete_transaction(transaction_id=transaction_id)
    except TransactionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{exc}')

@router.patch('/{transaction_id}', status_code=status.HTTP_200_OK)
async def update_transaction(
    transaction_id: int, 
    transaction_update_request: TransactionUpdate,
    transaction_service: TransactionService = Depends(get_transaction_service)
) -> TransactionResponse:
    try:
        updated_transaction = await transaction_service.update_transaction(
            transaction_id=transaction_id,
            transaction_update_request=transaction_update_request
            )
    except TransactionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{exc}')
    except InvalidCategory as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f'{exc}')
    return TransactionResponse.model_validate(updated_transaction)