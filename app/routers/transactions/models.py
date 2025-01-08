from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from app.utils.logger import logger

from .enums import MovementType


class TransactionData(BaseModel):
    transaction_id: int
    user: str
    group: Optional[str] = None
    movement_type: MovementType
    amount: int
    created_at: Optional[datetime] = None
    date: Optional[datetime] = None
    name: str
    category: str
    comments: Optional[str] = None


class GroupDetailsResult(BaseModel):
    group: str
    size: int
    balance: int
    total_available: int
    total_income: int
    total_expense: int
    total_debt: int
    total_contributions: int
    total_pending_receipts: int
    users_with_debt: list[str]


class TransactionDetail(BaseModel):
    transaction_id: int
    user: str
    name: str
    amount: int
    comments: Optional[str] = None


class IncomeDataMonth(BaseModel):
    datetime: str
    total_income: int
    total_contributions: int
    income_source: List[TransactionDetail]


class ExpenseDataMonth(BaseModel):
    datetime: str
    total_expense: int
    total_expenses: int
    expense_detail: List[TransactionDetail]


class DebtDataMonth(BaseModel):
    datetime: str
    total_debt: int
    total_contributions_in_debt: int
    debt_detail: List[TransactionDetail]


class ParsedData(BaseModel):
    income: List[IncomeDataMonth]
    expense: List[ExpenseDataMonth]
    debt: List[DebtDataMonth]


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
    projection: Optional[str] = Field(
        None, description="CSV of fields to return"
    )

    @validator("projection")
    def validate_projection(cls, value):
        if value:
            fields = [e.strip() for e in value.split(",") if e.strip()]
            if fields:
                return ["_id", *fields]

        return None
