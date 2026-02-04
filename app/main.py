"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1 import stocks, signals, markets, backtest, ml_training, system
from app.database import Base, engine

# Create database tables (only if database exists)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"⚠️  Warning: Could not create database tables: {e}")
    print("   Database may not exist yet. Run migrations: alembic upgrade head")

# Initialize FastAPI app
app = FastAPI(
    title="SignalIQ Backend API",
    description="AI-powered investment intelligence platform for US and NGX stocks",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router, prefix=f"{settings.api_v1_prefix}/stocks", tags=["stocks"])
app.include_router(signals.router, prefix=f"{settings.api_v1_prefix}/signals", tags=["signals"])
app.include_router(markets.router, prefix=f"{settings.api_v1_prefix}/markets", tags=["markets"])
app.include_router(backtest.router, prefix=f"{settings.api_v1_prefix}/backtest", tags=["backtest"])
app.include_router(ml_training.router, prefix=f"{settings.api_v1_prefix}/ml", tags=["ml-training"])
app.include_router(system.router, prefix=f"{settings.api_v1_prefix}/system", tags=["system"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "SignalIQ Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "signaliq-backend"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
                "details": {},
            },
        },
    )
