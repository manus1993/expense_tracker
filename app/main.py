import json
import os
import time
import traceback
from typing import Callable
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.routing import Match
from starlette.types import Message

from app import settings
from app.routers.transactions import transactions
from app.utils.logger import logger

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
    "http://localhost:8000",
    "http://52.0.141.128:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
async def log_request_info(request: Request, request_id: str):
    api_endpoint = None
    request_body = None
    path_params = None
    try:
        # request_body = await request.json()
        request_body = await get_body(request)
    except json.decoder.JSONDecodeError as e:
        logger.debug(e)

    routes = request.app.router.routes
    for route in routes:
        match, scope = route.matches(request)
        if match == Match.FULL:
            if scope.get("route"):
                api_endpoint = scope["route"].path
            if scope.get("path_params"):
                path_params = scope["path_params"]

    splunk_logger(
        {
            "type": "request",
            "method": request.method,
            "api": api_endpoint,
            "path_params": path_params,
            "query_params": request.query_params,
            "body": request_body,
            "request_id": request_id,
        }
    )


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


# async def set_body(request: Request):
#     """Avails the response body to be logged within a middleware as,
#     it is generally not a standard practice.

#         Arguments:
#         - request: Request
#         Returns:
#         - receive_: Receive
#     """
#     receive_ = await request._receive()

#     async def receive() -> Message:
#         return receive_

#     request._receive = receive


def exclude_endpoints_log(path: str):
    # "/v1/upgrades/CAT9K"
    EXCLUDED_ENDPOINTS = ["api-status"]
    for endpoint in EXCLUDED_ENDPOINTS:
        if path.endswith(endpoint):
            return True
    return False


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """
    Add API process time in response headers and log exceptions
    """
    request_id: str = str(uuid4())
    try:
        start_time = time.perf_counter()

        request.state.uuid = request_id
        # await set_body(request)

        if not exclude_endpoints_log(request.url.path):
            # await set_body(request)
            # await set_body(request, await request.body())
            await log_request_info(request, request_id)
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Request-ID"] = request_id
        return response
    except Exception:
        trace = traceback.format_exc()
        exc = trace.splitlines()[-1]
        logger.error(trace)
        if ENVIRONMENT != "dev":
            payload = {
                "method": request.method,
                "api": request.url.path,
                "type": "exception",
                "traceback": trace,
                "exception": exc,
                "request_id": request_id,
            }
            splunk_logger(payload)
            logger.error(payload)

        return PlainTextResponse(
            content="Internal Server Error", status_code=500
        )

'''
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
