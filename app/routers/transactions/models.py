from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .enums import IncomeCategory, MovementType


class TransactionData(BaseModel):
    transaction_id: int
    user: str
    group: str | None = None
    movement_type: MovementType
    amount: float
    created_at: datetime = datetime.now()
    date: datetime | None = None
    name: str
    category: str
    comments: str | None = None


class TransactionDetail(BaseModel):
    transaction_id: int
    user: str
    name: str
    amount: float
    comments: str | None = None
    category: str | None = None


class IncomeDataMonth(BaseModel):
    datetime: str
    total_income: float
    total_contributions: float
    income_source: list[TransactionDetail]


class ExpenseDataMonth(BaseModel):
    datetime: str
    total_expense: float
    total_expenses: float
    expense_detail: list[TransactionDetail]


class DebtDataMonth(BaseModel):
    datetime: str
    total_debt: float
    total_contributions_in_debt: float
    debt_detail: list[TransactionDetail]


class ParsedData(BaseModel):
    income: list[IncomeDataMonth]
    expense: list[ExpenseDataMonth]
    debt: list[DebtDataMonth]


class MarkReceiptAsPaid(BaseModel):
    group_id: str
    user_id: str
    month: str | None = None
    year: str | None = None
    name: str | None = None


class CreateNewBatchTransaction(BaseModel):
    group_id: str
    month: str
    year: str
    amount: float = 120
    category: IncomeCategory | str | None = IncomeCategory.monthly
    comments: str | None = None


class CreateNewTransaction(BaseModel):
    group_id: str
    user_id: str
    month: str
    year: str
    movement_type: MovementType
    amount: float = 120
    category: IncomeCategory | str = IncomeCategory.monthly
    comments: str | None = None
    name: str | None = None


class UpdateTransaction(BaseModel):
    amount: float | None = None
    comments: str | None = None
    name: str | None = None
    category: str | None = None


class MongoSingleGetQueryParams(BaseModel):
    filter: dict | None = Field(
        {},
        description="JSON Mongo Filter compliant with [JSON to BSON format](https://pymongo.readthedocs.io/en/stable/api/bson/json_util.html)",  # noqa: E501
    )
    projection: str | None = Field(None, description="CSV of fields to return")

    @field_validator("projection")
    @classmethod
    def validate_projection(cls, value: str | None) -> list[str] | None:
        if value:
            fields = [e.strip() for e in value.split(",") if e.strip()]
            if fields:
                return ["_id", *fields]

        return None


class GroupDetails(BaseModel):
    created_at: datetime
    size: int
    group: str
    group_members: list[str]
    # Optional calculated fields (added by parse_group_details)
    total_income: float | None = None
    total_expense: float | None = None
    total_debt: float | None = None
    total_contributions: float | None = None
    total_pending_receipts: float | None = None
    balance: float | None = None
    total_available: float | None = None
    users_with_debt: list[str] | None = None
