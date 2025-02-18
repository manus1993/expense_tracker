from pydantic import BaseModel


class ReceiptsRequest(BaseModel):
    transaction_id: int
    group: str
