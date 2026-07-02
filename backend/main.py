import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.journal import router as journal_router

# Setup structured logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mindspace")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager controlling the lifecycle environment checks at boot."""
    logger.info("Initializing MindSpace API server bootstrap...")
    # Environment variables are loaded and validated automatically by Pydantic Settings.
    # We log a confirmation or raise a fail-fast error.
    try:
        db_url = settings.DATABASE_URL
        secret = settings.JWT_SECRET_KEY
        if not db_url or not secret:
            raise ValueError("Required DATABASE_URL or JWT_SECRET_KEY variables are empty.")
        logger.info("Server environment configurations successfully verified and validated.")
    except Exception as e:
        logger.critical(f"Fail-Fast Error: Critical startup environment validation failed! Detail: {e}")
        raise e
    yield
    logger.info("MindSpace API server shutdown complete.")

app = FastAPI(
    title="MindSpace API",
    description="Backend API for MindSpace - AI-Powered Reflection & Journaling Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits cross-origin local requests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount authentication and journal routers
app.include_router(auth_router)
app.include_router(journal_router)

# Centralized global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Intercept HTTP exceptions and log the warnings."""
    logger.warning(f"HTTP exception on {request.method} {request.url.path}: {exc.detail} (Status {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Intercept Pydantic validation errors and format into clean fields."""
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"][1:])
        errors.append(f"{loc}: {error['msg']}")
    detail = "; ".join(errors)
    logger.warning(f"Validation error on {request.method} {request.url.path}: {detail}")
    return JSONResponse(
        status_code=422,
        content={"detail": f"Validation failed: {detail}"}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Intercept unhandled system errors, logs traces, and returns a unified 500 error page."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please contact support."}
    )

@app.get("/")
async def root():
    """Simple API health-check endpoint."""
    return {
        "message": "Welcome to MindSpace API",
        "status": "healthy",
        "version": "1.0.0"
    }
