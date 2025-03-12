from pydantic import BaseModel


class ReceiptsRequest(BaseModel):
    start_at: int
    end_at: int
    group: str


class BalanceRequest(BaseModel):
    year: str
    month: str
    group: str
