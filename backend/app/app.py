from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from .router import (
    students,
    products,
    classes,
    transactions,
    subscriptions,
    auth,
    stripe,
    stripe_webhooks,
)

app = FastAPI(openapi_prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(
    students.router,
    prefix='/students',
    tags=['students'],
)

app.include_router(
    products.router,
    prefix='/products',
    tags=['products'],
)

app.include_router(
    stripe.router,
    prefix='/stripe',
    tags=['checkout'],
)

app.include_router(
    stripe_webhooks.router,
    prefix='/stripe/webhooks',
    tags=['webhooks'],
)

app.include_router(
    auth.router,
    prefix='/auth',
    tags=['auth'],
)

app.include_router(
    transactions.router,
    prefix='/transactions',
    tags=['transactions'],
)

app.include_router(
    subscriptions.router,
    prefix='/subscriptions',
    tags=['subscriptions'],
)

app.include_router(
    classes.router,
    prefix='/class',
    tags=['class'],
)