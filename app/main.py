import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import settings
from app.routers.transactions import transactions

# from app.utils.logger import logger
# from app.utils.splunk_logger import splunk_logger


load_dotenv()
ENVIRONMENT = os.getenv("ENVIRONMENT")

description = """
Expense Tracker API:

📝 [Source Code](https://github.com/manus1993/expense_tracker)
🐞 [Issues](https://github.com/manus1993/expense_tracker/issues)
"""  # noqa: E501,W291


app = FastAPI(
    title="Expense Tracker APIs",
    description=description,
    version=settings.VERSION,
    # openapi_prefix=settings.SCRIPT_NAME,
    root_path=settings.SCRIPT_NAME,
    # ssl_keyfile=".certs/manus-server.key",
    # ssl_certfile=".certs/manus-server.crt"
)

origins = [
    "http://localhost",
    "http://localhost:8001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://ec2-3-140-252-95.us-east-2.compute.amazonaws.com:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])

app.include_router(
    transactions.router,
    prefix="/v1/transactions",
    tags=["transactions"],
    # dependencies=[Depends(validate_access_token)],
)


@app.get("/")
async def docs():
    """
    API Documentation
    """
    return RedirectResponse(settings.root_path + "/docs")
