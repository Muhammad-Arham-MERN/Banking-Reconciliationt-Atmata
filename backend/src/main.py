# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Main FastAPI application entry point
Bank Reconciliation System Backend Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import signal
import asyncio
from datetime import datetime, timezone
from src.config import settings
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global shutdown flag
is_shutting_down = False
active_requests = 0

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Handles graceful shutdown and resource cleanup

    Critical Security Requirements:
    - Startup: Initialize upload directory and resources
    - Shutdown: Delete ALL files in uploads directory
    """
    # ==================== STARTUP ====================
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Max PDF size: {settings.MAX_PDF_SIZE / (1024*1024):.0f}MB")
    logger.info(f"Max Excel size: {settings.MAX_EXCEL_SIZE / (1024*1024):.0f}MB")
    logger.info(f"File retention: {settings.FILE_RETENTION_MINUTES} minutes (automatic cleanup)")
    logger.info("-" * 50)
    logger.info(f"CORS_ORIGINS: {repr(settings.CORS_ORIGINS)}")
    logger.info(f"Parsed origins: {[origin.strip() for origin in settings.CORS_ORIGINS.split(',')]}")
    logger.info("-" * 50)

    # Ensure upload directory exists and is writable
    from src.utils.file_helpers import ensure_upload_directory, cleanup_old_files

    if not ensure_upload_directory():
        logger.error("Failed to create upload directory!")
        raise RuntimeError("Cannot start without upload directory")

    # Initialize database connection and run migrations
    from src.services.db_service import initialize_database

    await initialize_database(dsn=settings.DATABASE_URL)
    logger.info("✅ Database initialized and migrations applied")

    # Clean up any orphaned files from previous runs
    orphaned_count = cleanup_old_files(max_age_minutes=settings.FILE_RETENTION_MINUTES)
    if orphaned_count > 0:
        logger.info(f"Cleaned up {orphaned_count} orphaned files from previous session")

    logger.info("✅ Application startup complete")

    # ==================== RUNNING ====================
    try:
        yield

    # ==================== SHUTDOWN ====================
    finally:
        global is_shutting_down
        is_shutting_down = True
        logger.info("🚨 SHUTDOWN INITIATED - Graceful shutdown in progress...")
        logger.warning("⚠️  WARNING: Server is shutting down. No new requests will be accepted.")

        # Wait for active requests to complete (max 10 seconds)
        shutdown_timeout = settings.SHUTDOWN_TIMEOUT
        elapsed = 0
        check_interval = 0.5

        logger.info(f"⏳ Waiting {shutdown_timeout}s for active requests to complete...")

        while active_requests > 0 and elapsed < shutdown_timeout:
            logger.info(f"📊 Active requests: {active_requests} (elapsed: {elapsed:.1f}s)")
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        if active_requests > 0:
            logger.warning(f"⚠️  Shutdown timeout reached. {active_requests} requests still active.")
        else:
            logger.info("✅ All active requests completed successfully.")

        # CRITICAL: Delete ALL files on shutdown
        from src.utils.file_helpers import cleanup_all_files

        try:
            deleted_count = cleanup_all_files()
            logger.info(f"🗑️  Deleted {deleted_count} files during shutdown")
        except Exception as cleanup_error:
            logger.error(f"❌ Error during file cleanup: {cleanup_error}")

        logger.info("✅ Graceful shutdown complete. Goodbye!")
        logger.warning("🔌 Server stopped. Ready for restart.")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for bank reconciliation processing",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - Dynamically from settings (comma-separated env var)
# origin.strip() for origin in settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Basic error handling middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests and responses with active request tracking"""
    global active_requests

    # Reject new requests during shutdown
    if is_shutting_down:
        logger.warning(f"❌ Request rejected during shutdown: {request.method} {request.url}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={
                "error": "service_unavailable",
                "message": "Server is shutting down. Please try again later.",
                "details": {"shutdown_in_progress": True}
            }
        )

    # Increment active requests counter
    active_requests += 1
    logger.info(f"📈 Active requests: {active_requests} | {request.method} {request.url}")

    try:
        response = await call_next(request)
        logger.info(f"✅ Response status: {response.status_code} | Active: {active_requests}")
        return response
    finally:
        # Decrement active requests counter
        active_requests -= 1
        logger.info(f"📉 Active requests: {active_requests}")

# Import API routes and middleware
from src.api.routes import router as api_router
from src.api.ai_routes import router as ai_router
from src.api.cloud_routes import router as cloud_router
from src.api.middleware import rate_limit_middleware, security_middleware
from src.api.auth_middleware import auth_middleware

# Include API routes
app.include_router(api_router, tags=["api"])
app.include_router(ai_router, tags=["ai"])
app.include_router(cloud_router)

# Add security middleware (order: auth first, then security, then rate-limit)
app.middleware("http")(auth_middleware)
app.middleware("http")(security_middleware)
app.middleware("http")(rate_limit_middleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ