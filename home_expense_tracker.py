import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

from starlette import status

from logging_context import correlation_id_context
import models
from database import db_engine
from router import expenses, users, auth


rest_api_app = FastAPI(title="Home Expense Tracker")

'''
To a web browser, an "Origin" consists of three strict parts:
The Protocol (http:// vs https://)
The Domain (localhost vs google.com)
The Port (:8081, :3000, :8000)
If any of those three things are different between your UI and your API, 
the browser considers it a "Cross-Origin" request.
CORS - Cross-Origin Resource Sharing
By adding this, FastAPI will automatically attach a special hidden header to every response 
that tells your web browser to let the data through.
'''
rest_api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://localhost:8080","http://localhost:3000","http://localhost:8000",
                   "https://home-expense-tracker-ui.onrender.com"
                  ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger(__name__)
'''
This will only be run if our db does not exist.
If we make any enhancement to the model, this will not run an automatically
It's easier just to delete our DB and then recreate it if we add anything extra to our DB Model
'''
models.DB_Handle.metadata.create_all(bind=db_engine)


@rest_api_app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    request_id = str(uuid4())
    logger.debug(f'Request ID Generated {request_id}')
    token = correlation_id_context.set(request_id)
    logger.debug(f'Token {token}')
    try:
        response = await call_next(request)
        response.headers["X-CORRELATION-ID"] = request_id
        return response
    finally:
        correlation_id_context.reset(token)


@rest_api_app.get("/home", summary="HomeExpenseTracker Home", status_code=status.HTTP_200_OK)
async def home_page():
    logger.debug("Home Page /home invoked")
    return {"message": "Welcome to Home Expense Tracker"}

rest_api_app.include_router(expenses.expenses_endpoint)
rest_api_app.include_router(users.users_endpoint)
rest_api_app.include_router(auth.auth_end_point)
