from fastapi import FastAPI

from app.api.routes import api_v1
from app.exceptions.handlers import register_handlers

app = FastAPI(title='Wallet Service')
register_handlers(app)

app.include_router(api_v1)