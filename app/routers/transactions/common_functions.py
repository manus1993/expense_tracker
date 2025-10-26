from datetime import datetime

from app.utils.db import expenses_db
from app.utils.get_common import (
    CommonMongoGetQueryParams,
    CommonMongoSingleGetQueryParams,
    get_record,
    get_records,
)
from app.utils.logger import logger

from .models import MongoGetQueryParams, MongoSingleGetQueryParams


def query_actions(
    mongo_params: CommonMongoGetQueryParams | MongoGetQueryParams,
):
    """
    Query the Overwatching Actions DB by a given filter and projection
    """
    mongo_params.filter = mongo_params.filter or {}
    mongo_params.filter["removed"] = {"$exists": False}
    return get_records(expenses_db, "Movements", mongo_params, True)


def query_single_action_by_uuid(
    mongo_params: CommonMongoSingleGetQueryParams | MongoSingleGetQueryParams,
    uuid_val: str,
):
    """
    Query the Overwatching Actions by a given UUID
    """
    logger.info(f"Fetching overwatching action {uuid_val}")
    mongo_params.filter = {
        **mongo_params.filter,
        **{
            "removed": {"$exists": False},
            "uuid": uuid_val,
        },
    }
    return get_record(expenses_db, "Movements", mongo_params, True)


def get_group_definition(filter):
    return expenses_db.Groups.find_one(filter, {"_id": 0})


def simple_query(filter):
    return list(expenses_db.Movements.find(filter, {"_id": 0}))


def add_movement(movement_data):
    return expenses_db.Movements.insert_one(movement_data)


def update_db(query, update) -> None:
    expenses_db.Movements.update_one(query, update)


def delete_db(query) -> None:
    expenses_db.Movements.delete_one(query)


def get_last_transaction_id(
    user_id: str,
    group: str,
    movement_type: str,  # 'income' or 'expense'
):
    """
    Returns the last valid transaction_id for a user and group,
    considering the following rules:

    - Pending (transaction_id == 9999) are ignored.
    - Incomes have ID < 10000.
    - Expenses have ID > 10000.
    - 'DEPTO 0' (management) can now have both incomes and expenses.
    - For 'DEPTO 0' incomes, we look for IDs < 10000 as usual.
    """

    # Define query range based on movement type
    if movement_type == "income":
        id_query = {"$lt": 10000, "$nin": [9999]}
    elif movement_type == "expense":
        id_query = {"$gt": 10000, "$nin": [9999]}
    else:
        raise ValueError("movement_type must be either 'income' or 'expense'")

    # Fetch last transaction for this group and user type
    last_tx = expenses_db.Movements.find_one(
        {"transaction_id": id_query, "group": group},
        sort=[("transaction_id", -1)],
    )

    # Default values when nothing found
    if not last_tx:
        return 10000 if movement_type == "expense" else 0

    last_id = last_tx["transaction_id"]

    # For non-management users, ensure continuity (avoid overlaps)
    if user_id == last_tx.get("user") and user_id != "DEPTO 0":
        return last_id - 1

    return last_id


def update_movement(query):
    expenses_db.Movements.update_one(
        query,
        {
            "$set": {
                "transaction_id": get_last_transaction_id(
                    query["user"], query["group"], movement_type='income'
                )
                + 1,
                "created_at": datetime.now(),
                "category": "MONTLY_INCOME",
            }
        },
    )

    return True
