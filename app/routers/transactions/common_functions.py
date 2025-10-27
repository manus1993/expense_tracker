from datetime import datetime

from pydantic import TypeAdapter

from app.utils.db import expenses_db
from app.utils.get_common import (
    CommonMongoGetQueryParams,
    get_records,
)

from .models import GroupDetails, TransactionData


def query_actions(
    mongo_params: CommonMongoGetQueryParams,
) -> list[TransactionData]:
    """
    Query the Overwatching Actions DB by a given filter and projection
    """
    mongo_params.filter = mongo_params.filter or {}
    mongo_params.filter["removed"] = {"$exists": False}
    results = get_records(expenses_db, "Movements", mongo_params, True)
    transaction_list_adapter = TypeAdapter(list[TransactionData])
    return transaction_list_adapter.validate_python(results)


def get_group_definition(group_filter: dict) -> GroupDetails | None:
    result = expenses_db.Groups.find_one(group_filter, {"_id": 0})
    if result is not None:
        # Validate result using GroupDetails TypeAdapter
        group_adapter = TypeAdapter(GroupDetails)
        return group_adapter.validate_python(result)
    return None


def simple_query(query_filter: dict) -> list[TransactionData]:
    results = list(expenses_db.Movements.find(query_filter, {"_id": 0}))
    transaction_list_adapter = TypeAdapter(list[TransactionData])
    return transaction_list_adapter.validate_python(results)


def add_movement(movement_data: TransactionData) -> None:
    expenses_db.Movements.insert_one(movement_data)


def update_db(query: dict, update: dict) -> None:
    expenses_db.Movements.update_one(query, update)


def delete_db(query: dict) -> None:
    expenses_db.Movements.delete_one(query)


def get_last_transaction_id(
    user_id: str,
    group: str,
    movement_type: str,  # 'income' or 'expense'
) -> int:
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

    last_id: int = last_tx["transaction_id"]

    # For non-management users, ensure continuity (avoid overlaps)
    if user_id == last_tx.get("user") and user_id != "DEPTO 0":
        return last_id - 1

    return last_id


def update_movement(query_filter: dict) -> None:
    expenses_db.Movements.update_one(
        query_filter,
        {
            "$set": {
                "transaction_id": get_last_transaction_id(
                    query_filter["user"], query_filter["group"], movement_type="income"
                )
                + 1,
                "created_at": datetime.now(),
                "category": "MONTHLY_INCOME",
            }
        },
    )
