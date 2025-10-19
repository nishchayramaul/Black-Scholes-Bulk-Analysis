from fastapi import APIRouter
from app.api.v1 import black_scholes, black_scholes_parallel

api_router = APIRouter()
api_router.include_router(black_scholes.router)
api_router.include_router(black_scholes_parallel.router)
