"""
DisasterAI Backend - Database Module
Handles database operations for persistent task storage
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from contextlib import contextmanager
from typing import Generator, Optional
import json
from datetime import datetime

from .models import TaskDB, TaskStatus, AnalysisRequest, AnalysisResult

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./disasterai_tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class TaskORM(Base):
    """SQLAlchemy ORM model for tasks"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    progress = Column(Integer, default=0)
    request_data = Column(Text, nullable=False)  # JSON string
    result_data = Column(Text)  # JSON string
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# Create tables
Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session() -> Generator:
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_task_in_db(task_db: TaskDB) -> TaskDB:
    """Create a new task in the database"""
    with get_db_session() as db:
        db_task = TaskORM(
            task_id=task_db.task_id,
            status=task_db.status.value if hasattr(task_db.status, 'value') else task_db.status,
            progress=task_db.progress,
            request_data=task_db.request_data,
            result_data=task_db.result_data,
            error_message=task_db.error_message
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        return TaskDB(
            id=db_task.id,
            task_id=db_task.task_id,
            status=TaskStatus(db_task.status),
            progress=db_task.progress,
            request_data=db_task.request_data,
            result_data=db_task.result_data,
            error_message=db_task.error_message,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )


def get_task_from_db(task_id: str) -> Optional[TaskDB]:
    """Retrieve a task from the database by task_id"""
    with get_db_session() as db:
        db_task = db.query(TaskORM).filter(TaskORM.task_id == task_id).first()
        if not db_task:
            return None

        return TaskDB(
            id=db_task.id,
            task_id=db_task.task_id,
            status=TaskStatus(db_task.status),
            progress=db_task.progress,
            request_data=db_task.request_data,
            result_data=db_task.result_data,
            error_message=db_task.error_message,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )


def update_task_in_db(
    task_id: str,
    status: Optional[TaskStatus] = None,
    progress: Optional[int] = None,
    result_data: Optional[str] = None,
    error_message: Optional[str] = None
) -> Optional[TaskDB]:
    """Update a task in the database"""
    with get_db_session() as db:
        db_task = db.query(TaskORM).filter(TaskORM.task_id == task_id).first()
        if not db_task:
            return None

        if status is not None:
            db_task.status = status.value if hasattr(status, 'value') else status
        if progress is not None:
            db_task.progress = progress
        if result_data is not None:
            db_task.result_data = result_data
        if error_message is not None:
            db_task.error_message = error_message

        db_task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_task)

        return TaskDB(
            id=db_task.id,
            task_id=db_task.task_id,
            status=TaskStatus(db_task.status),
            progress=db_task.progress,
            request_data=db_task.request_data,
            result_data=db_task.result_data,
            error_message=db_task.error_message,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )


def delete_task_from_db(task_id: str) -> bool:
    """Delete a task from the database"""
    with get_db_session() as db:
        db_task = db.query(TaskORM).filter(TaskORM.task_id == task_id).first()
        if not db_task:
            return False

        db.delete(db_task)
        db.commit()
        return True


def list_tasks_from_db(limit: int = 50) -> list[TaskDB]:
    """List recent tasks from the database"""
    with get_db_session() as db:
        db_tasks = db.query(TaskORM).order_by(TaskORM.created_at.desc()).limit(limit).all()

        return [
            TaskDB(
                id=db_task.id,
                task_id=db_task.task_id,
                status=TaskStatus(db_task.status),
                progress=db_task.progress,
                request_data=db_task.request_data,
                result_data=db_task.result_data,
                error_message=db_task.error_message,
                created_at=db_task.created_at,
                updated_at=db_task.updated_at
            )
            for db_task in db_tasks
        ]


def cleanup_old_tasks_from_db(max_age_hours: int = 24) -> int:
    """Remove tasks older than max_age_hours from the database"""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    with get_db_session() as db:
        deleted_count = db.query(TaskORM).filter(TaskORM.created_at < cutoff).delete()
        db.commit()
        return deleted_count