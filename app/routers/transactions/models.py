from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from .enums import MovementType

class TransactionData(BaseModel):
    transaction_id: Optional[int] = 0
    user: str
    movement_type: MovementType
    amount: int
    date: Optional[datetime] = None
    name: str
    category: str

class TransactionDataIn(BaseModel):
    user: str
    movement_type: MovementType
    amount: int
    date: Optional[datetime] = None
    name: str
    category: str