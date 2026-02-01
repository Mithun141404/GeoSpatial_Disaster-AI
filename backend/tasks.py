"""
DisasterAI Backend - Background Tasks
Celery tasks and async job processing
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import json

from .models import (
    AnalysisRequest,
    AnalysisResult,
    TaskStatus,
    TaskInfo,
    TaskDB
)
from .config import settings
from .db import (
    create_task_in_db,
    get_task_from_db,
    update_task_in_db,
    delete_task_from_db,
    list_tasks_from_db,
    cleanup_old_tasks_from_db
)


# ============================================================================
# PERSISTENT TASK STORE (using database for production)
# ============================================================================

class TaskStore:
    """
    Persistent task store using database for production.
    Falls back to in-memory store if database is unavailable.
    """

    def __init__(self):
        self._fallback_tasks: Dict[str, TaskDB] = {}
        self.use_fallback = False

    def create_task(self, request: AnalysisRequest) -> str:
        """Create a new task and return its ID"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        # Create TaskDB object
        task_db = TaskDB.from_request(task_id, request)

        try:
            # Try to save to database
            created_task = create_task_in_db(task_db)
            return created_task.task_id
        except Exception as e:
            # Fallback to in-memory storage if DB fails
            print(f"Database error, falling back to in-memory: {e}")
            self.use_fallback = True

            # Store in memory
            self._fallback_tasks[task_id] = task_db
            return task_id

    def get_task(self, task_id: str) -> Optional[TaskDB]:
        """Get a task by ID"""
        if self.use_fallback:
            return self._fallback_tasks.get(task_id)

        try:
            return get_task_from_db(task_id)
        except Exception as e:
            print(f"Database error, checking fallback: {e}")
            return self._fallback_tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        result: Optional[AnalysisResult] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update a task's status"""
        if self.use_fallback:
            task = self._fallback_tasks.get(task_id)
            if not task:
                return False

            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result_data = result.model_dump_json()
            if error is not None:
                task.error_message = error

            task.updated_at = datetime.utcnow()
            return True

        try:
            # Convert result to JSON string if provided
            result_data = None
            if result:
                result_data = result.model_dump_json()

            updated_task = update_task_in_db(
                task_id=task_id,
                status=status,
                progress=progress,
                result_data=result_data,
                error_message=error
            )
            return updated_task is not None
        except Exception as e:
            print(f"Database error updating task, checking fallback: {e}")
            # Try fallback storage
            task = self._fallback_tasks.get(task_id)
            if not task:
                return False

            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if result is not None:
                task.result_data = result.model_dump_json()
            if error is not None:
                task.error_message = error

            task.updated_at = datetime.utcnow()
            return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if self.use_fallback:
            if task_id in self._fallback_tasks:
                del self._fallback_tasks[task_id]
                return True
            return False

        try:
            return delete_task_from_db(task_id)
        except Exception as e:
            print(f"Database error deleting task, checking fallback: {e}")
            if task_id in self._fallback_tasks:
                del self._fallback_tasks[task_id]
                return True
            return False

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task info for API response"""
        task = self.get_task(task_id)
        if not task:
            return None

        # Convert stored result data back to AnalysisResult if available
        result = None
        if task.result_data:
            try:
                result = AnalysisResult.model_validate(json.loads(task.result_data))
            except Exception:
                result = None

        return TaskInfo(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            created_at=task.created_at,
            updated_at=task.updated_at,
            result=result,
            error=task.error_message
        )

    def list_tasks(self, limit: int = 50) -> list[TaskInfo]:
        """List recent tasks"""
        if self.use_fallback:
            # Sort fallback tasks by creation date
            sorted_tasks = sorted(
                self._fallback_tasks.values(),
                key=lambda t: t.created_at,
                reverse=True
            )[:limit]

            result_list = []
            for task in sorted_tasks:
                # Convert stored result data back to AnalysisResult if available
                result = None
                if task.result_data:
                    try:
                        result = AnalysisResult.model_validate(json.loads(task.result_data))
                    except Exception:
                        result = None

                result_list.append(TaskInfo(
                    task_id=task.task_id,
                    status=task.status,
                    progress=task.progress,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    result=result,
                    error=task.error_message
                ))
            return result_list

        try:
            tasks = list_tasks_from_db(limit=limit)
            result_list = []
            for task in tasks:
                # Convert stored result data back to AnalysisResult if available
                result = None
                if task.result_data:
                    try:
                        result = AnalysisResult.model_validate(json.loads(task.result_data))
                    except Exception:
                        result = None

                result_list.append(TaskInfo(
                    task_id=task.task_id,
                    status=task.status,
                    progress=task.progress,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    result=result,
                    error=task.error_message
                ))
            return result_list
        except Exception as e:
            print(f"Database error listing tasks, using fallback: {e}")
            # Sort fallback tasks by creation date
            sorted_tasks = sorted(
                self._fallback_tasks.values(),
                key=lambda t: t.created_at,
                reverse=True
            )[:limit]

            result_list = []
            for task in sorted_tasks:
                # Convert stored result data back to AnalysisResult if available
                result = None
                if task.result_data:
                    try:
                        result = AnalysisResult.model_validate(json.loads(task.result_data))
                    except Exception:
                        result = None

                result_list.append(TaskInfo(
                    task_id=task.task_id,
                    status=task.status,
                    progress=task.progress,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    result=result,
                    error=task.error_message
                ))
            return result_list

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Remove tasks older than max_age_hours"""
        if self.use_fallback:
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

            to_delete = [
                task_id for task_id, task in self._fallback_tasks.items()
                if task.created_at < cutoff
            ]

            for task_id in to_delete:
                del self._fallback_tasks[task_id]

            return len(to_delete)

        try:
            return cleanup_old_tasks_from_db(max_age_hours=max_age_hours)
        except Exception as e:
            print(f"Database error cleaning up tasks, using fallback: {e}")
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

            to_delete = [
                task_id for task_id, task in self._fallback_tasks.items()
                if task.created_at < cutoff
            ]

            for task_id in to_delete:
                del self._fallback_tasks[task_id]

            return len(to_delete)


# Global task store instance
task_store = TaskStore()


# ============================================================================
# ASYNC TASK PROCESSOR
# ============================================================================

class TaskProcessor:
    """
    Async task processor for handling background analysis jobs.
    """
    
    def __init__(self, store: TaskStore):
        self.store = store
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def process_analysis(self, task_id: str) -> None:
        """
        Process an analysis task asynchronously.
        
        Args:
            task_id: ID of the task to process
        """
        task = self.store.get_task(task_id)
        if not task or not task.request:
            return
        
        try:
            # Update status to processing
            self.store.update_task(task_id, status=TaskStatus.PROCESSING, progress=10)
            
            # Import service here to avoid circular imports
            from .services.gemini_service import get_gemini_service
            
            service = get_gemini_service()
            
            # Update progress
            self.store.update_task(task_id, progress=30)
            
            # Perform analysis
            result = await service.analyze_document(task.request, task_id)
            
            # Update with result
            self.store.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                result=result
            )
            
        except Exception as e:
            self.store.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
    
    def submit_task(self, task_id: str) -> None:
        """
        Submit a task for background processing.
        
        Args:
            task_id: ID of the task to process
        """
        # Create async task
        async_task = asyncio.create_task(self.process_analysis(task_id))
        self._running_tasks[task_id] = async_task
        
        # Cleanup when done
        async_task.add_done_callback(
            lambda t: self._running_tasks.pop(task_id, None)
        )
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled
        """
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            self.store.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error="Task cancelled by user"
            )
            return True
        return False


# Global task processor instance
task_processor = TaskProcessor(task_store)


# ============================================================================
# CELERY CONFIGURATION (for production use)
# ============================================================================

try:
    from celery import Celery
    
    celery_app = Celery(
        "disasterai",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=settings.TASK_TIMEOUT,
        worker_prefetch_multiplier=1,
    )
    
    @celery_app.task(bind=True, max_retries=3)
    def celery_analyze_document(self, task_id: str, request_dict: dict):
        """
        Celery task for document analysis.
        
        Args:
            task_id: Task ID for tracking
            request_dict: Serialized AnalysisRequest
        """
        import asyncio
        
        request = AnalysisRequest(**request_dict)
        
        try:
            # Update status
            self.update_state(state="PROCESSING", meta={"progress": 10})
            
            # Run async analysis in sync context
            from .services.gemini_service import get_gemini_service
            service = get_gemini_service()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    service.analyze_document(request, task_id)
                )
            finally:
                loop.close()
            
            return result.model_dump()
            
        except Exception as e:
            self.retry(exc=e, countdown=5)
    
    CELERY_AVAILABLE = True
    
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None
    celery_analyze_document = None


# ============================================================================
# TASK API FUNCTIONS
# ============================================================================

def create_analysis_task(
    request: AnalysisRequest,
    use_celery: bool = False
) -> str:
    """
    Create and submit an analysis task.
    
    Args:
        request: Analysis request
        use_celery: Whether to use Celery (if available)
        
    Returns:
        Task ID
    """
    task_id = task_store.create_task(request)
    
    if use_celery and CELERY_AVAILABLE:
        # Submit to Celery
        celery_analyze_document.delay(task_id, request.model_dump())
    else:
        # Use async processor
        task_processor.submit_task(task_id)
    
    return task_id


def get_task_status(task_id: str) -> Optional[TaskInfo]:
    """
    Get the status of a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        TaskInfo or None
    """
    return task_store.get_task_info(task_id)


def cancel_analysis_task(task_id: str) -> bool:
    """
    Cancel a running task.
    
    Args:
        task_id: Task ID
        
    Returns:
        True if task was cancelled
    """
    return task_processor.cancel_task(task_id)
