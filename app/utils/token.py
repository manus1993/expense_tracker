import os
from enum import Enum

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.utils.db import expenses_db
from app.utils.logger import logger

security = HTTPBearer()
STATIC_TOKEN = os.getenv("STATIC_TOKEN")


class TokenType(str, Enum):
    admin = "admin"
    user = "user"


class OwnerObject(BaseModel):
    token_owner: str
    access_token: str
    scope: list[str]
    token_type: TokenType


def validate_access_token(
    access_token: HTTPAuthorizationCredentials = Security(security),
) -> OwnerObject:
    """
    Validate Access Token
    """
    token_details = find_user_from_token(access_token.credentials)
    if not token_details:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    logger.info("User: %s", token_details.token_owner)
    return token_details


def find_user_from_token(token: str) -> OwnerObject | None:
    """
    Find user from token
    """
    user = expenses_db.Owners.find_one({"access_token": token})
    if user is None:
        return None
    return OwnerObject(**user)
