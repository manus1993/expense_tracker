from enum import Enum

class MovementType(str, Enum):
    expense = "expense"
    income = "income"
    investment = "investment"

class GenResponseCode(str, Enum):
    created = "CREATED"
    deleted = "DELETED"
    edited = "CHANGES_APPLIED"
    failed = "FAILED"
    partial_success = "CREATED_WITH_ERRORS"

