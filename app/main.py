import sys
from fastapi import FastAPI

from app.api.routes import api_v1
from app.configs.logger import run_logger
from app.exceptions.handlers import register_handlers

if 'pytest' not in sys.modules:
    run_logger('prod')

app = FastAPI(title='Wallet Service')
register_handlers(app)

app.include_router(api_v1)