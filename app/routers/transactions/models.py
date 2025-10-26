from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from app.utils.logger import logger

from .enums import IncomeCategory, MovementType


class TransactionData(BaseModel):
    transaction_id: int
    user: str
    group: Optional[str] = None
    movement_type: MovementType
    amount: float
    created_at: Optional[datetime] = None
    date: Optional[datetime] = None
    name: str
    category: str
    comments: Optional[str] = None


class GroupDetailsResult(BaseModel):
    group: str
    size: int
    balance: float
    total_available: float
    total_income: float
    total_expense: float
    total_debt: float
    total_contributions: float
    total_pending_receipts: float
    users_with_debt: list[str]


class TransactionDetail(BaseModel):
    transaction_id: int
    user: str
    name: str
    amount: float
    comments: Optional[str] = None
    category: Optional[str] = None


class IncomeDataMonth(BaseModel):
    datetime: str
    total_income: float
    total_contributions: float
    income_source: List[TransactionDetail]


class ExpenseDataMonth(BaseModel):
    datetime: str
    total_expense: float
    total_expenses: float
    expense_detail: List[TransactionDetail]


class DebtDataMonth(BaseModel):
    datetime: str
    total_debt: float
    total_contributions_in_debt: float
    debt_detail: List[TransactionDetail]


class ParsedData(BaseModel):
    income: List[IncomeDataMonth]
    expense: List[ExpenseDataMonth]
    debt: List[DebtDataMonth]


class MarkReceiptAsPaid(BaseModel):
    group_id: str
    user_id: str
    month: Optional[str] = None
    year: Optional[str] = None
    name: Optional[str] = None


class CreateNewBatchTransaction(BaseModel):
    group_id: str
    month: str
    year: str
    amount: Optional[float] = 120
    category: Optional[IncomeCategory] | str = IncomeCategory.montly
    comments: Optional[str] = None


class CreateNewTransaction(BaseModel):
    group_id: str
    user_id: str
    month: str
    year: str
    movement_type: MovementType
    amount: Optional[float] = 120
    category: Optional[IncomeCategory] | str = IncomeCategory.montly
    comments: Optional[str] = None
    name: Optional[str] = None


class UpdateTransaction(BaseModel):
    amount: Optional[float] = None
    comments: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None


class MongoGetQueryParams(BaseModel):
    filter: Optional[Dict] = Field(
        {},
        description="JSON Mongo Filter compliant with [JSON to BSON format](https://pymongo.readthedocs.io/en/stable/api/bson/json_util.html)",  # noqa: E501
    )
    projection: Optional[Union[str, Dict]] = Field(
        None,
        description="CSV of fields to return or a JSON projection object",
    )
    limit: Optional[int] = Field(
        200, gt=0, le=2000, description="Number of items to return"
    )
    skip: Optional[int] = Field(0, ge=0, description="Number of items to skip")
    sort_key: Optional[str] = Field(None, description="Field to sort on")
    sort_ascending: Optional[bool] = Field(False, description="Sort direction")

    @validator("projection")
    def validate_projection(cls, value):
        if value:
            if isinstance(value, dict):
                logger.debug(f"projection was JSON: {value}")
                return value
            """
            TODO: we should do better about santizing nonsense here
            """
            logger.info(f"projection was not JSON: {value}")
            fields = {e.strip(): 1 for e in value.split(",") if e.strip()}
            if fields:
                p = {"_id": 1, **fields}
                logger.debug(f"projection was csv, here is what we got: {p}")
                return p
        return None


class MongoSingleGetQueryParams(BaseModel):
    filter: Optional[Dict] = Field(
        {},
        description="JSON Mongo Filter compliant with [JSON to BSON format](https://pymongo.readthedocs.io/en/stable/api/bson/json_util.html)",  # noqa: E501
    )
    projection: Optional[str] = Field(None, description="CSV of fields to return")

    @validator("projection")
    def validate_projection(cls, value):
        if value:
            fields = [e.strip() for e in value.split(",") if e.strip()]
            if fields:
                return ["_id", *fields]

        return None
