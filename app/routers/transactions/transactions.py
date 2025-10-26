# from app.utils.logger import logger
from datetime import datetime, timedelta
from typing import Any, Optional

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
    delete_db,
    get_group_definition,
    get_last_transaction_id,
    query_actions,
    simple_query,
    update_db,
    update_movement,
)
from .enums import GenResponseCode, IncomeCategory, MovementType
from .models import (
    CreateNewBatchTransaction,
    CreateNewTransaction,
    MarkReceiptAsPaid,
    TransactionData,
    UpdateTransaction,
)
from .operations import parse_data, parse_group_details

# from app.utils.token import validate_access_token
# from .models import BugQuery, BugResponse


router = APIRouter()
security = HTTPBearer()


def validate_scope(
    group_id: str,
    access_token_details: dict = Depends(validate_access_token),
    admin: bool = False,
) -> bool:
    """
    Validate the scope
    """

    if group_id not in access_token_details["scope"]:
        raise HTTPException(status_code=403, detail="Insufficient scope")
    if admin and not access_token_details["token_type"] == "admin":
        raise HTTPException(status_code=403, detail="Admin token required")
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
    date: Optional[str] = "",
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
    if date:
        start_date = datetime.strptime(date, "%Y-%m")
        end_date = start_date.replace(day=1) + timedelta(days=32)
        end_date = end_date.replace(day=1)
        filter_group["date"] = {"$gte": start_date, "$lt": end_date}

    data = simple_query(filter_group)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")

    parsed_data = parse_data(data, group_details)

    return {
        "group_details": parse_group_details(group_details, parsed_data),
        "parsed_data": parsed_data,
    }


@router.get("", response_model=list[TransactionData])
async def get_transaction(
    mongo_params: CommonMongoGetQueryParams = Depends(CommonMongoGetQueryParams),
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
    payload: CreateNewBatchTransaction,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> str:
    """
    Get items from database actions
    Allow: Mongo Query and Projection
    """

    validate_scope(payload.group_id, access_token_details, admin=True)
    filter_group = {"group": payload.group_id}
    group_details = get_group_definition(filter_group)
    if not group_details:
        raise HTTPException(status_code=400, detail="group not found")

    date = datetime.strptime(f"{payload.year}-{payload.month}-01", "%Y-%m-%d")

    if len(group_details["group_members"]) > 0:
        for member in group_details["group_members"]:
            if simple_query(
                {
                    "group": payload.group_id,
                    "user": member,
                    "date": date,
                    "movement_type": MovementType.income,
                    "category": payload.category,
                }
            ):
                logger.info(f"Receipt already paid for {member}")
                continue
            name = f"APORTACION {payload.month} {payload.year}"
            if payload.category == IncomeCategory.extraordinary:
                name = name + " EXTRAORDINARIA"
            transaction = {
                "transaction_id": 9999,
                "user": member,
                "group": payload.group_id,
                "amount": payload.amount,
                "name": name,
                "created_at": datetime.now(),
                "date": date,
                "comments": payload.comments,
                "movement_type": MovementType.income,
                "category": "VENCIDO",
            }
            add_movement(transaction)

    return "Completado"


@router.post("/mark-receipt-as-paid")
async def mark_receipt_as_paid(
    payload: MarkReceiptAsPaid,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> TransactionData:
    validate_scope(payload.group_id, access_token_details, admin=True)
    query = {
        "transaction_id": 9999,
        "group": payload.group_id,
        "user": payload.user_id,
        "movement_type": MovementType.income,
        "category": "VENCIDO",
    }
    if payload.name:
        query["name"] = payload.name
    elif payload.month and payload.year:
        query["date"] = datetime.strptime(
            f"{payload.year}-{payload.month}-01", "%Y-%m-%d"
        )
    else:
        raise HTTPException(
            status_code=400, detail="Month and year or name are required"
        )

    event = simple_query(query)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_movement(query)

    return event[0]


@router.post("/create-new-transaction")
async def create_new_transaction(
    payload: CreateNewTransaction,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> TransactionData:
    validate_scope(payload.group_id, access_token_details, admin=True)
    query = {
        "group": payload.group_id,
        "user": payload.user_id,
        "date": datetime.strptime(f"{payload.year}-{payload.month}-01", "%Y-%m-%d"),
        "movement_type": payload.movement_type,
        "category": payload.category,
    }
    if payload.name:
        query["name"] = payload.name
    if simple_query(query):
        raise HTTPException(status_code=400, detail="Transaction already exists")

    name = payload.name
    if not name:
        name = f"APORTACION {payload.month} {payload.year}"

    transaction = {
        "transaction_id": get_last_transaction_id(
            payload.user_id, payload.group_id, movement_type=payload.movement_type
        )
        + 1,
        "user": payload.user_id,
        "group": payload.group_id,
        "amount": payload.amount,
        "name": name,
        "created_at": datetime.now(),
        "date": datetime.strptime(f"{payload.year}-{payload.month}-01", "%Y-%m-%d"),
        "comments": payload.comments,
        "movement_type": payload.movement_type,
        "category": payload.category,
    }
    add_movement(transaction)

    return TransactionData(**transaction)


@router.put("/update-transaction/{group_id}/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    group_id: str,
    name: str,
    payload: UpdateTransaction,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> dict:
    validate_scope(group_id, access_token_details, admin=True)
    query = {
        "transaction_id": transaction_id,
        "group": group_id,
    }
    if name:
        query["name"] = name
    event = simple_query(query)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if len(event) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple events found, use name to get a unique event",
        )
    payload: dict = payload.dict(exclude_unset=True)
    update = {"$set": payload}
    update_db(query, update)

    return {"status": GenResponseCode.edited}


@router.delete("/delete-transaction/{group_id}/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    group_id: str,
    name: str,
    access_token: HTTPAuthorizationCredentials = Security(security),
    access_token_details: dict = Depends(validate_access_token),
) -> dict:
    """
    Delete a transaction
    """
    validate_scope(group_id, access_token_details, admin=True)
    query = {
        "transaction_id": transaction_id,
        "group": group_id,
    }
    if name:
        query["name"] = name
    event = simple_query(query)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if len(event) > 1:
        raise HTTPException(
            status_code=400,
            detail="Multiple events found, use name to get a unique event",
        )
    logger.info("Deleting the transaction")
    delete_db(query)

    return {"status": "deleted"}
