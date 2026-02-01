"""
DisasterAI Backend Package
"""

from .main import app
from .config import settings
from .models import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisResponse,
    ExtractedEntity,
    EntityLabel,
    SeverityLevel,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    TaskStatus,
    TaskInfo
)

__version__ = "1.0.0"
__all__ = [
    "app",
    "settings",
    "AnalysisRequest",
    "AnalysisResult", 
    "AnalysisResponse",
    "ExtractedEntity",
    "EntityLabel",
    "SeverityLevel",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "TaskStatus",
    "TaskInfo"
]
