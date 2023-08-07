from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.logger import logger
# from app.utils.token import validate_access_token
# from .models import BugQuery, BugResponse

router = APIRouter()
security = HTTPBearer()


@router.post("")
async def post_transaction(
    query: dict
    # access_token: HTTPAuthorizationCredentials = Security(security),
    # access_token_details: dict = Depends(validate_access_token),
):
    """
    Post a new transaction INCOME/OUTCOME
    """
    return "hola mundo"
