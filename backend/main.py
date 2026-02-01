"""
DisasterAI Backend - FastAPI Application
Main entry point for the API server
"""

import os
import time
import traceback
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from models import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisResponse,
    HealthCheck,
    ServiceStatus,
    TaskInfo,
    TaskCreateResponse,
    TaskStatus,
    GeocodingRequest,
    BatchGeocodingRequest,
    GeocodingResult,
    BatchGeocodingResult,
    NERRequest,
    NERResult,
    AnalysisConfig
)
from config import settings, validate_settings
from tasks import (
    create_analysis_task,
    get_task_status,
    cancel_analysis_task,
    task_store
)
from logging_config import get_logger, log_api_call, log_task_event


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

start_time: float = 0
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global start_time
    start_time = time.time()

    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    validate_settings()

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"📁 Upload directory ensured: {settings.UPLOAD_DIR}")

    yield

    # Shutdown
    logger.info("👋 Shutting down...")
    task_store.cleanup_old_tasks(max_age_hours=1)
    logger.info("🧹 Old tasks cleaned up")


# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered multimodal geospatial intelligence analysis for disaster response",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests"""
    start_time = time.time()
    request_id = str(uuid4())

    # Get client IP
    client_host = request.client.host if request.client else "unknown"

    # Log the incoming request
    logger.info(
        f"Received {request.method} {request.url.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': client_host,
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )

    try:
        response = await call_next(request)
    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time

        # Log the error
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'duration_ms': round(duration * 1000, 2),
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        raise

    # Calculate duration
    duration = time.time() - start_time

    # Log the response
    log_api_call(
        logger,
        endpoint=request.url.path,
        method=request.method,
        duration_ms=round(duration * 1000, 2),
        status_code=response.status_code,
        user_agent=request.headers.get('user-agent'),
        ip_address=client_host
    )

    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors"""
    logger.warning(
        f"Validation error: {exc}",
        extra={'validation_errors': exc.errors()}
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            'exception_type': type(exc).__name__,
            'traceback': traceback.format_exc(),
            'url': str(request.url),
            'method': request.method
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "detail": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - start_time

    # Check service availability
    services = {
        "gemini_api": bool(settings.GEMINI_API_KEY),
        "database": True,  # Assuming database is available if we reach here
        "geocoding": True,
        "ner_model": True,
        "task_queue": True,
        "file_storage": os.path.exists(settings.UPLOAD_DIR)
    }

    # Perform actual database connectivity check
    try:
        from db import get_db_session
        with get_db_session() as db:
            # Try to query something simple
            db.execute("SELECT 1")
        services["database"] = True
    except Exception as e:
        services["database"] = False
        logger.error(f"Database connectivity check failed: {str(e)}")

    # Check disk space in upload directory
    try:
        import shutil
        _, _, free_space = shutil.disk_usage(settings.UPLOAD_DIR)
        free_space_mb = free_space / (1024 * 1024)
        services["disk_space"] = free_space_mb > 100  # At least 100MB free
    except Exception:
        services["disk_space"] = False

    status = "healthy"
    if not all(services.values()):
        status = "degraded"

    health_data = HealthCheck(
        status=status,
        version=settings.APP_VERSION,
        uptime_seconds=uptime,
        services=services
    )

    logger.info(
        f"Health check performed - Status: {status}",
        extra={
            'uptime_seconds': uptime,
            'services_status': services
        }
    )

    return health_data


@app.get("/config", response_model=AnalysisConfig, tags=["Health"])
async def get_config():
    """Get current configuration"""
    return AnalysisConfig(
        default_analysis_mode="comprehensive",
        max_file_size_mb=settings.MAX_FILE_SIZE_MB,
        gemini_model=settings.GEMINI_MODEL,
        enable_caching=settings.CACHE_ENABLED,
        cache_ttl_seconds=settings.CACHE_TTL
    )


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_document(request: AnalysisRequest):
    """
    Analyze a document synchronously.

    For large documents or when you need progress tracking,
    use the async endpoint `/api/analyze/async` instead.
    """
    request_id = str(uuid4())
    logger.info(
        "Starting synchronous document analysis",
        extra={'request_id': request_id}
    )

    try:
        from services.gemini_service import get_gemini_service

        service = get_gemini_service()
        result = await service.analyze_document(request)

        logger.info(
            "Document analysis completed successfully",
            extra={'request_id': request_id, 'task_id': result.taskId}
        )

        return AnalysisResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(
            f"Document analysis failed: {str(e)}",
            extra={
                'request_id': request_id,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        return AnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )


@app.post("/api/analyze/async", response_model=TaskCreateResponse, tags=["Analysis"])
async def analyze_document_async(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start an async document analysis task.

    Returns a task ID that can be used to check progress and retrieve results.
    """
    request_id = str(uuid4())
    logger.info(
        "Creating asynchronous document analysis task",
        extra={'request_id': request_id}
    )

    try:
        task_id = create_analysis_task(request)

        logger.info(
            "Asynchronous analysis task created",
            extra={'request_id': request_id, 'task_id': task_id}
        )

        log_task_event(
            logger,
            task_id,
            "Task created successfully",
            extra_data={'request_id': request_id}
        )

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Analysis task created. Use /api/tasks/{task_id} to check status."
        )
    except Exception as e:
        logger.error(
            f"Failed to create analysis task: {str(e)}",
            extra={
                'request_id': request_id,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        raise HTTPException(status_code=500, detail=f"Failed to create analysis task: {str(e)}")


@app.post("/api/analyze/upload", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    analysis_mode: str = Form(default="comprehensive"),
    include_geocoding: bool = Form(default=True)
):
    """
    Upload and analyze a file directly.

    Accepts PDF, PNG, JPG, WEBP, and TIFF files.
    """
    request_id = str(uuid4())
    logger.info(
        f"Uploading and analyzing file: {file.filename}",
        extra={'request_id': request_id, 'filename': file.filename}
    )

    import base64

    # Validate file type
    if file.content_type not in [
        "image/png", "image/jpeg", "image/webp", "image/tiff", "application/pdf"
    ]:
        logger.warning(
            f"Unsupported file type uploaded: {file.content_type}",
            extra={'request_id': request_id, 'filename': file.filename}
        )
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    # Read and encode file
    contents = await file.read()

    # Check file size
    file_size_mb = len(contents) / (1024 * 1024)
    if len(contents) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        logger.warning(
            f"File too large: {file_size_mb:.2f}MB (max: {settings.MAX_FILE_SIZE_MB}MB)",
            extra={'request_id': request_id, 'filename': file.filename, 'size_mb': file_size_mb}
        )
        raise HTTPException(400, f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB")

    logger.info(
        f"File uploaded successfully: {file_size_mb:.2f}MB",
        extra={'request_id': request_id, 'filename': file.filename, 'size_mb': file_size_mb}
    )

    encoded = base64.b64encode(contents).decode("utf-8")

    # Create request
    request = AnalysisRequest(
        document_data=encoded,
        mime_type=file.content_type,
        analysis_mode=analysis_mode,
        include_geocoding=include_geocoding
    )

    # Process
    from services.gemini_service import get_gemini_service

    try:
        service = get_gemini_service()
        result = await service.analyze_document(request)

        logger.info(
            "File analysis completed successfully",
            extra={'request_id': request_id, 'task_id': result.taskId}
        )

        return AnalysisResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(
            f"File analysis failed: {str(e)}",
            extra={
                'request_id': request_id,
                'filename': file.filename,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        return AnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )


# ============================================================================
# TASK MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/tasks/{task_id}", response_model=TaskInfo, tags=["Tasks"])
async def get_task(task_id: str):
    """Get the status and result of an analysis task"""
    request_id = str(uuid4())
    logger.info(
        "Retrieving task status",
        extra={'request_id': request_id, 'task_id': task_id}
    )

    task_info = get_task_status(task_id)

    if not task_info:
        logger.warning(
            "Task not found",
            extra={'request_id': request_id, 'task_id': task_id}
        )
        raise HTTPException(404, f"Task not found: {task_id}")

    logger.info(
        f"Task retrieved - Status: {task_info.status}",
        extra={'request_id': request_id, 'task_id': task_id, 'status': task_info.status}
    )

    return task_info


@app.delete("/api/tasks/{task_id}", tags=["Tasks"])
async def cancel_task(task_id: str):
    """Cancel a running task"""
    request_id = str(uuid4())
    logger.info(
        "Attempting to cancel task",
        extra={'request_id': request_id, 'task_id': task_id}
    )

    if cancel_analysis_task(task_id):
        logger.info(
            "Task cancelled successfully",
            extra={'request_id': request_id, 'task_id': task_id}
        )
        log_task_event(
            logger,
            task_id,
            "Task cancelled by user",
            level="WARNING"
        )
        return {"success": True, "message": f"Task {task_id} cancelled"}

    logger.warning(
        "Attempted to cancel non-existent or completed task",
        extra={'request_id': request_id, 'task_id': task_id}
    )
    raise HTTPException(404, f"Task not found or already completed: {task_id}")


@app.get("/api/tasks", response_model=list[TaskInfo], tags=["Tasks"])
async def list_tasks(limit: int = Query(default=50, le=100)):
    """List recent analysis tasks"""
    request_id = str(uuid4())
    logger.info(
        f"Listing tasks (limit: {limit})",
        extra={'request_id': request_id, 'limit': limit}
    )

    tasks = task_store.list_tasks(limit=limit)

    logger.info(
        f"Returned {len(tasks)} tasks",
        extra={'request_id': request_id, 'returned_count': len(tasks)}
    )

    return tasks


# ============================================================================
# GEOCODING ENDPOINTS
# ============================================================================

@app.post("/api/geocode", response_model=Optional[GeocodingResult], tags=["Geocoding"])
async def geocode_location(request: GeocodingRequest):
    """Geocode a single location name to coordinates"""
    from services.geocoding_service import get_geocoding_service
    
    service = get_geocoding_service()
    result = await service.geocode_location(request.location_name, request.context)
    
    if not result:
        raise HTTPException(404, f"Location not found: {request.location_name}")
    
    return result


@app.post("/api/geocode/batch", response_model=BatchGeocodingResult, tags=["Geocoding"])
async def batch_geocode(request: BatchGeocodingRequest):
    """Geocode multiple locations at once"""
    from services.geocoding_service import get_geocoding_service
    
    service = get_geocoding_service()
    return await service.batch_geocode(request.locations, request.context)


# ============================================================================
# NER ENDPOINTS
# ============================================================================

@app.post("/api/ner", response_model=NERResult, tags=["NER"])
async def extract_entities(request: NERRequest):
    """Extract named entities from text"""
    from services.ner_service import get_ner_service
    
    service = get_ner_service()
    return service.extract_entities(request.text, request.labels)


@app.post("/api/ner/locations", tags=["NER"])
async def extract_locations(text: str = Form(...)):
    """Extract only location entities from text"""
    from services.ner_service import get_ner_service
    
    service = get_ner_service()
    locations = service.extract_locations(text)
    
    return {"locations": locations, "count": len(locations)}


# ============================================================================
# IMPORT AND INCLUDE ROUTERS
# ============================================================================

from monitoring import router as monitoring_router
app.include_router(monitoring_router, prefix="/api")

from routes.disaster_routes import router as disaster_router
app.include_router(disaster_router, prefix="/api")

from routes.realtime_routes import router as realtime_router
app.include_router(realtime_router, prefix="/api")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS
    )
