"""
DisasterAI Backend - Monitoring and Metrics
Provides detailed metrics and monitoring endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
import psutil
import time
import os
from datetime import datetime
import asyncio

from config import settings
from tasks import task_store
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

start_time = time.time()


class SystemMetrics(BaseModel):
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: float
    load_average: List[float]


class TaskMetrics(BaseModel):
    """Task-related metrics"""
    total_tasks: int
    pending_tasks: int
    processing_tasks: int
    completed_tasks: int
    failed_tasks: int


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    system: SystemMetrics
    tasks: TaskMetrics
    timestamp: datetime


@router.get("/metrics/system", tags=["Monitoring"])
async def get_system_metrics():
    """Get system resource metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        # Load average (Unix-like systems only)
        try:
            load_avg = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]
        except AttributeError:
            # Windows doesn't have getloadavg, return zeros
            load_avg = [0, 0, 0]

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            uptime_seconds=time.time() - start_time,
            load_average=load_avg
        )

        logger.info("System metrics retrieved", extra=metrics.dict())

        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise


@router.get("/metrics/tasks", tags=["Monitoring"])
async def get_task_metrics():
    """Get task-related metrics"""
    try:
        # For this implementation, we'll use the task store to get metrics
        # In a production environment, you'd want to query the database directly
        # or maintain counters for better performance

        # Since we don't have a direct way to get all tasks with statuses,
        # we'll simulate by getting recent tasks and counting
        recent_tasks = task_store.list_tasks(limit=1000)  # Get last 1000 tasks

        total_tasks = len(recent_tasks)
        pending_tasks = sum(1 for t in recent_tasks if t.status == "pending")
        processing_tasks = sum(1 for t in recent_tasks if t.status == "processing")
        completed_tasks = sum(1 for t in recent_tasks if t.status == "completed")
        failed_tasks = sum(1 for t in recent_tasks if t.status == "failed")

        metrics = TaskMetrics(
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            processing_tasks=processing_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks
        )

        logger.info("Task metrics retrieved", extra=metrics.dict())

        return metrics
    except Exception as e:
        logger.error(f"Error getting task metrics: {str(e)}")
        raise


@router.get("/metrics/performance", response_model=PerformanceMetrics, tags=["Monitoring"])
async def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        system_metrics = await get_system_metrics()
        task_metrics = await get_task_metrics()

        performance_metrics = PerformanceMetrics(
            system=system_metrics,
            tasks=task_metrics,
            timestamp=datetime.utcnow()
        )

        logger.info("Performance metrics retrieved")

        return performance_metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise


@router.get("/metrics/health-detailed", tags=["Monitoring"])
async def detailed_health_check():
    """Detailed health check with multiple service verifications"""
    try:
        health_checks = {
            "api_server": True,
            "database_connection": False,
            "gemini_api": bool(settings.GEMINI_API_KEY),
            "upload_directory": os.path.exists(settings.UPLOAD_DIR),
            "disk_space_available": False,
            "memory_available": True,
        }

        # Check database connection
        try:
            from db import get_db_session
            with get_db_session() as db:
                db.execute("SELECT 1")
            health_checks["database_connection"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")

        # Check disk space
        try:
            import shutil
            _, _, free_space = shutil.disk_usage(settings.UPLOAD_DIR)
            free_space_mb = free_space / (1024 * 1024)
            health_checks["disk_space_available"] = free_space_mb > 100  # At least 100MB
        except Exception:
            health_checks["disk_space_available"] = False

        # Check memory
        memory = psutil.virtual_memory()
        health_checks["memory_available"] = memory.percent < 90  # Less than 90% used

        overall_status = "healthy" if all(health_checks.values()) else "degraded"

        detailed_health = {
            "status": overall_status,
            "checks": health_checks,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION
        }

        logger.info(f"Detailed health check - Status: {overall_status}")

        return detailed_health
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        raise