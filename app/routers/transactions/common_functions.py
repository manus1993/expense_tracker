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

def get_last_transaction_id():
    # Exclude transaction_id == 9999 and transaction_id > 10000

    last_transaction_id = expenses_db.Movements.find_one(
        {"transaction_id": {"$nin": [9999], "$lt": 10000}},
        sort=[("transaction_id", -1)],
    )
    return last_transaction_id["transaction_id"]

def update_movement(query):
    expenses_db.Movements.update_one(
        query, 
        {"$set": {
            "transaction_id": get_last_transaction_id() + 1,
            "created_at": datetime.now(),
            "category": "MONTLY_INCOME",
            }
        }
    )

    return True