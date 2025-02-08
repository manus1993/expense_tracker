from pydantic import BaseModel


class ReceiptsRequest(BaseModel):
    begin: int
    end: int
    group: str
