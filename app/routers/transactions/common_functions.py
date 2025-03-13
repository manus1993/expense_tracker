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
):
    # Exclude transaction_id == 9999 and transaction_id > 10000

    user_cond = "$gt" if user_id == "DEPTO 0" else "$lt"
    last_transaction_id = expenses_db.Movements.find_one(
        {
            "transaction_id": {"$nin": [9999], user_cond: 10000},
            "group": group,
        },
        sort=[("transaction_id", -1)],
    )
    if not last_transaction_id:
        if user_id == "DEPTO 0":
            return 10000
        return 0

    if user_id == last_transaction_id["user"] and user_id != "DEPTO 0":
        return last_transaction_id["transaction_id"] - 1
    return last_transaction_id["transaction_id"]


def update_movement(query):
    expenses_db.Movements.update_one(
        query,
        {
            "$set": {
                "transaction_id": get_last_transaction_id(
                    query["user"], query["group"]
                )
                + 1,
                "created_at": datetime.now(),
                "category": "MONTLY_INCOME",
            }
        },
    )

    return True
