# from app.utils.logger import logger
from datetime import datetime
from typing import Any, List, Optional

import pymongo
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.get_common import (  # CommonMongoSingleGetQueryParams,
    CommonMongoGetQueryParams,
)
from app.utils.logger import logger
from app.utils.token import validate_access_token

from .common_functions import (
    add_movement,
    get_group_definition,
    get_last_transaction_id,
    query_actions,
    simple_query,
    update_movement,
)
from .enums import MovementType
from .models import TransactionData
from .operations import parse_data, parse_group_details

# from app.utils.token import validate_access_token
# from .models import BugQuery, BugResponse


router = APIRouter()
security = HTTPBearer()


def validate_scope(
    group_id: str,
    access_token_details: dict = Depends(validate_access_token),
) -> bool:
    """
    Validate the scope
    """
    if group_id not in access_token_details["scope"]:
        raise HTTPException(status_code=403, detail="Insufficient scope")
    return True


def build_aqe_list_from_mongo_docs(
    document_list: list | pymongo.typings._DocumentType,
) -> list[TransactionData]:
    """
    Make a list of the result from pymongo
    """
    ret = [TransactionData(**doc) for doc in document_list]
    return ret


@router.get("/parsed-data", response_model=Any)
async def get_parsed_data(
    group_id: Optional[str] = None,
    user_id: Optional[str] = None,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> Any:
    """
    For a given group or user, get the parsed data
    """
    validate_scope(group_id, access_token_details)
    filter_group = {"group": group_id}
    group_details = get_group_definition(filter_group)
    if not group_details:
        raise HTTPException(status_code=400, detail="group not found")
    if user_id:
        filter_group["user"] = user_id
    data = simple_query(filter_group)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")

    parsed_data = parse_data(data, group_details)

    return {
        "group_details": parse_group_details(group_details, parsed_data),
        "parsed_data": parsed_data,
    }


@router.get("", response_model=List[TransactionData])
async def get_transaction(
    mongo_params: CommonMongoGetQueryParams = Depends(
        CommonMongoGetQueryParams
    ),
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> list[TransactionData]:
    """
    Get items from database actions
    Allow: Mongo Query and Projection
    """
    results = query_actions(mongo_params=mongo_params)
    if not results:
        raise HTTPException(status_code=404, detail="Actions not found")

    return build_aqe_list_from_mongo_docs(results)


@router.post("/create-receipt-batch")
async def create_receipt_batch(
    group_id: str,
    month: str,
    year: str,
    amount: Optional[int] = 120,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> str:
    """
    Get items from database actions
    Allow: Mongo Query and Projection
    """
    validate_scope(group_id, access_token_details)
    filter_group = {"group": group_id}
    group_details = get_group_definition(filter_group)
    if not group_details:
        raise HTTPException(status_code=400, detail="group not found")

    date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")

    if len(group_details["group_members"]) > 0:
        for member in group_details["group_members"]:
            if simple_query(
                {
                    "group": group_id,
                    "user": member,
                    "date": date,
                    "movement_type": MovementType.income,
                    "category": "MONTLY_INCOME",
                }
            ):
                logger.info(f"Receipt already paid for {member}")
                continue

            transaction = {
                "transaction_id": 9999,
                "user": member,
                "group": group_id,
                "amount": amount,
                "name": f"APORTACION {month} {year}",
                "created_at": datetime.now(),
                "date": date,
                "comments": None,
                "movement_type": MovementType.income,
                "category": "VENCIDO",
            }
            add_movement(transaction)

    return "Completado"


@router.post("/mark-receipt-as-paid")
async def mark_receipt_as_paid(
    group_id: str,
    user_id: str,
    month: str,
    year: str,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> str:
    validate_scope(group_id, access_token_details)
    query = {
        "transaction_id": 9999,
        "group": group_id,
        "user": user_id,
        "date": datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d"),
        "movement_type": MovementType.income,
        "category": "VENCIDO",
    }

    event = simple_query(query)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_movement(query)

    return event


@router.post("/create-new-transaction")
async def create_new_transaction(
    group_id: str,
    user_id: str,
    month: str,
    year: str,
    movement_type: MovementType = MovementType.income,
    amount: Optional[int] = 120,
    category: Optional[str] = "MONTLY_INCOME",
    comments: Optional[str] = None,
    name: Optional[str] = None,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> TransactionData:
    validate_scope(group_id, access_token_details)
    query = {
        "group": group_id,
        "user": user_id,
        "date": datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d"),
        "movement_type": movement_type,
        "category": category,
    }
    if name:
        query["name"] = name
    if simple_query(query):
        raise HTTPException(
            status_code=400, detail="Transaction already exists"
        )

    if not name:
        name = f"APORTACION {month} {year}"

    transaction = {
        "transaction_id": get_last_transaction_id(user_id, group_id) + 1,
        "user": user_id,
        "group": group_id,
        "amount": amount,
        "name": name,
        "created_at": datetime.now(),
        "date": datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d"),
        "comments": comments,
        "movement_type": movement_type,
        "category": category,
    }
    add_movement(transaction)

    return TransactionData(**transaction)
