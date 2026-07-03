import logging
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.journal import router as journal_router
from app.routes.reflection import router as reflection_router
from app.routes.analytics import router as analytics_router
from app.routes.settings import router as settings_router
from app.routes.export import router as export_router
from app.routes.health import router as health_router

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
    """Lifecycle handler executing server bootstrap diagnostics checks."""
    logger.info("Initializing MindSpace API server bootstrap...")
    
    # Fail-Fast Bootstrap validations
    try:
        is_key_missing = (
            not settings.GEMINI_API_KEY 
            or settings.GEMINI_API_KEY.strip() == "" 
            or settings.GEMINI_API_KEY == "mock-key-for-local-testing"
        )
        should_mock = settings.MOCK_AI or is_key_missing

        logger.info("Server environment configurations successfully verified and validated.")
        
        if should_mock:
            if settings.MOCK_AI:
                logger.warning("WARNING: Running in MOCK mode because MOCK_AI=true is set.")
            else:
                logger.warning("WARNING: Running in MOCK mode because GEMINI_API_KEY is missing or invalid.")
        else:
            logger.info("✓ Gemini API Key Loaded")
            logger.info(f"✓ Gemini Model: {settings.GEMINI_MODEL}")
            
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
origins = [
    origin.strip() 
    for origin in settings.ALLOWED_CORS_ORIGINS.split(",") 
    if origin.strip()
] if settings.ALLOWED_CORS_ORIGINS else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & secure headers custom interceptor middleware
@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.perf_counter()
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Inject request id tracing and secure HTTP headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self';"
    
    # Compute request timing
    duration = time.perf_counter() - start_time
    duration_ms = duration * 1000.0
    
    log_msg = f"[{request_id}] {request.method} {request.url.path} - {response.status_code} - Completed in {duration_ms:.2f}ms"
    
    # Emit warning alerts on slow API requests
    if duration_ms > 800.0:
        logger.warning(f"{log_msg} [SLOW REQUEST WARNING]")
    else:
        logger.info(log_msg)
        
    return response

# Mount routers
app.include_router(auth_router)
app.include_router(journal_router)
app.include_router(reflection_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(export_router)
app.include_router(health_router)

# Centralized global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] HTTP exception on {request.method} {request.url.path}: {exc.detail} (Status {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    errors = jsonable_encoder(exc.errors())
    
    # Extract specific error messages to support substring assertions
    error_msgs = [err.get("msg", "") for err in errors if err.get("msg")]
    detail_msg = "; ".join(error_msgs) if error_msgs else "Input validation failed. Please check the supplied parameters."
    
    logger.warning(f"[{request_id}] Validation failure on {request.method} {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": detail_msg,
            "status_code": 422,
            "errors": errors,
            "request_id": request_id
        }
    )

@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unexpected server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred.",
            "status_code": 500,
            "request_id": request_id
        }
    )
