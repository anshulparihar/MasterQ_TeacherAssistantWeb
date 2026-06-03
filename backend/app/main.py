import structlog
import traceback
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import api_router
from .core.events import create_start_app_handler, create_stop_app_handler
from .core.cache_middleware import CacheMiddleware

logger = structlog.get_logger(__name__)

app = FastAPI(title="MasterQ Platform API", version="1.0.0")

# Custom Middlewares
app.add_middleware(CacheMiddleware)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    logger.info(
        "http_request",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )
    return response

# Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=403,
        content={"detail": "You do not have permission to access this resource."},
    )

@app.exception_handler(FileNotFoundError)
async def not_found_error_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception caught", path=request.url.path, exc_info=exc, traceback=traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Routers
app.include_router(api_router)

# Lifecycle hooks
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")
    handler = create_start_app_handler(app)
    await handler()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")
    handler = create_stop_app_handler(app)
    await handler()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
