from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config.settings import settings
from app.core.lifespan import lifespan
from app.core.exceptions import APIException
from app.core.logging import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    logger.error(f"API Error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled system exception:")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

@app.get("/", tags=["root"])
def read_root():
    return {
        "project": settings.PROJECT_NAME,
        "description": settings.DESCRIPTION,
        "version": settings.VERSION,
        "status": "running",
        "documentation_url": "/docs"
    }
