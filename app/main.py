from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title="Black-Scholes Calculator API",
    description="A production-grade FastAPI application for Black-Scholes option pricing calculations",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "your-domain.com"]
    )

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Black-Scholes Calculator API",
        "version": "1.0.0",
        "description": "API for calculating Black-Scholes option prices and Greeks",
        "endpoints": {
            "single_calculation": "/api/v1/black-scholes/calculate",
            "excel_processing": "/api/v1/black-scholes/process-excel",
            "example_format": "/api/v1/black-scholes/example-excel"
        },
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
