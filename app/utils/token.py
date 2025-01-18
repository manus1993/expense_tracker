import os

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.utils.db import expenses_db
from app.utils.logger import logger

security = HTTPBearer()
STATIC_TOKEN = os.getenv("STATIC_TOKEN")


class Token(BaseModel):
    token_owner: str
    access_token: str
    scope: list[str]


def validate_access_token(
    access_token: HTTPAuthorizationCredentials = Security(security),
):
    """
    Validate Access Token
    """
    token_details = find_user_from_token(access_token.credentials)
    if not token_details:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    logger.info("User: %s" % token_details["token_owner"])
    return token_details


def find_user_from_token(token: str) -> Token:
    """
    Find user from token
    """
    user = expenses_db.Owners.find_one({"access_token": token})
    if not user:
        return {}
    return user
