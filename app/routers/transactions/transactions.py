import random

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Optional
from app.utils.db import expenses_db
from app.utils.logger import logger
from datetime import datetime

from .models import TransactionData, TransactionDataIn
from .enums import MovementType, GenResponseCode
# from app.utils.token import validate_access_token
# from .models import BugQuery, BugResponse

router = APIRouter()
security = HTTPBearer()

def fetch_transaction(query: dict = {}):
    return list(expenses_db.Movements.find(query, {'_id': False}))

def save_transaction(payload):
    logger.info(f"Adding to db: {payload}")
    expenses_db.Movements.insert_one({**payload})

def delete_transaction_from_db(transaction_id, user):
    logger.info(f"deleting from db: {transaction_id}")
    expenses_db.Movements.delete_one({
        "transaction_id": transaction_id,
        "user": user
    })



@router.get("", response_model=List[TransactionData])
async def get_transaction(
    user: str,
    movement_type: MovementType,
    transaction_id: Optional[int] = None,
    # query: dict
    # access_token: HTTPAuthorizationCredentials = Security(security),
    # access_token_details: dict = Depends(validate_access_token),
):
    """
    Get a transaction INCOME/OUTCOME/INVESTMENT
    """
    query = {"movement_type": movement_type, "user": user}
    if transaction_id:
        query["transaction_id"] = transaction_id
    result = fetch_transaction(query)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=("NO_TRANSACTION_FOUND"),
        )
    return result

@router.post("", response_model=GenResponseCode)
async def post_transaction(
    payload: TransactionDataIn
    # access_token: HTTPAuthorizationCredentials = Security(security),
    # access_token_details: dict = Depends(validate_access_token),
):
    """
    Post a transaction INCOME/OUTCOME/INVESTMENT
    """
    data = payload.dict()
    data["transaction_id"] = random.randrange(1,10000,1)
    while fetch_transaction({
        "transaction_id": data["transaction_id"], "user": data["user"]
    }):
        logger.info(f"transaction_id is used {data['transaction_id']}")
        data["transaction_id"] = random.randrange(1,10000,1)
    if not data["date"]:
        data["date"] = datetime.now()
    save_transaction(payload=data)
    return GenResponseCode.created

@router.delete("", response_model=GenResponseCode)
async def delete_transaction(
    transaction_id: int,
    user: str
    # access_token: HTTPAuthorizationCredentials = Security(security),
    # access_token_details: dict = Depends(validate_access_token),
):
    """
    Post a transaction INCOME/OUTCOME/INVESTMENT
    """
    if not fetch_transaction({
        "transaction_id": transaction_id,
        "user":user
    }):
        raise HTTPException(
            status_code=404,
            detail=("TRANSACTION_DOES_NOT_EXIST"),
        )
    delete_transaction_from_db(transaction_id=transaction_id, user=user)
    return GenResponseCode.deleted



