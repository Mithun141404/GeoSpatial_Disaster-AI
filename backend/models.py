"""
DisasterAI Backend - Pydantic Models
Data validation and serialization for the API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EntityLabel(str, Enum):
    """Entity labels for NER extraction"""
    LOCATION = "LOC"
    ORGANIZATION = "ORG"
    DAMAGE_TYPE = "DMG"
    URGENCY = "URG"
    TECH = "TECH"
    PERSON = "PER"
    DATE = "DATE"
    EVENT = "EVENT"


class SeverityLevel(str, Enum):
    """Severity levels for geospatial features"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TaskStatus(str, Enum):
    """Status of background tasks"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# GEOSPATIAL MODELS
# ============================================================================

class GeoJSONGeometry(BaseModel):
    """GeoJSON Geometry object"""
    type: Literal["Point", "Polygon", "LineString", "MultiPolygon"]
    coordinates: List[Any]  # Can be nested lists of coordinates


class GeoJSONProperties(BaseModel):
    """Properties for a GeoJSON feature"""
    name: str
    confidence: str = Field(default="0%", description="Confidence percentage as string")
    severity: SeverityLevel
    description: str
    source_text: Optional[str] = None
    category: Optional[str] = None


class GeoJSONFeature(BaseModel):
    """A single GeoJSON feature"""
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    """Collection of GeoJSON features"""
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)


# ============================================================================
# ENTITY MODELS
# ============================================================================

class ExtractedEntity(BaseModel):
    """A named entity extracted from text"""
    text: str
    label: EntityLabel
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    confidence: Optional[float] = None


# ============================================================================
# ANALYSIS MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request payload for document analysis"""
    document_data: Optional[str] = Field(None, description="Base64 encoded document data")
    document_url: Optional[str] = Field(None, description="URL to fetch document from")
    mime_type: str = Field(..., description="MIME type of the document")
    analysis_mode: Literal["quick", "comprehensive", "exhaustive"] = "comprehensive"
    include_geocoding: bool = True
    max_locations: int = Field(default=50, ge=1, le=200)


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    task_id: str = Field(..., alias="taskId")
    document_id: str = Field(..., alias="documentId")
    summary: str
    risk_score: int = Field(..., ge=0, le=100, alias="riskScore")
    entities: List[ExtractedEntity]
    indicators: List[str]
    geospatial_data: GeoJSONFeatureCollection = Field(..., alias="geospatialData")
    timestamp: datetime
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None

    class Config:
        populate_by_name = True


class AnalysisResponse(BaseModel):
    """API response wrapper for analysis"""
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None
    task_id: Optional[str] = None


# ============================================================================
# TASK MODELS
# ============================================================================

class TaskInfo(BaseModel):
    """Information about a background task"""
    task_id: str
    status: TaskStatus
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime
    updated_at: Optional[datetime] = None
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class TaskCreateResponse(BaseModel):
    """Response when creating a new background task"""
    task_id: str
    status: TaskStatus
    message: str


# ============================================================================
# GEOCODING MODELS
# ============================================================================

class GeocodingRequest(BaseModel):
    """Request for geocoding a location"""
    location_name: str
    context: Optional[str] = None  # Additional context like country/region


class GeocodingResult(BaseModel):
    """Result of geocoding a location"""
    location_name: str
    latitude: float
    longitude: float
    confidence: float
    formatted_address: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None


class BatchGeocodingRequest(BaseModel):
    """Request for batch geocoding multiple locations"""
    locations: List[str]
    context: Optional[str] = None


class BatchGeocodingResult(BaseModel):
    """Result of batch geocoding"""
    results: List[GeocodingResult]
    failed: List[str] = Field(default_factory=list)


# ============================================================================
# NER MODELS
# ============================================================================

class NERRequest(BaseModel):
    """Request for Named Entity Recognition"""
    text: str
    labels: Optional[List[EntityLabel]] = None  # Filter by specific labels


class NERResult(BaseModel):
    """Result of NER extraction"""
    entities: List[ExtractedEntity]
    text_length: int
    processing_time_ms: int


# ============================================================================
# HEALTH & STATUS MODELS
# ============================================================================

class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    services: Dict[str, bool]


class ServiceStatus(BaseModel):
    """Status of individual services"""
    gemini_api: bool = False
    geocoding: bool = False
    ner_model: bool = False
    task_queue: bool = False


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class AnalysisConfig(BaseModel):
    """Configuration for analysis behavior"""
    default_analysis_mode: str = "comprehensive"
    max_file_size_mb: int = 50
    supported_mime_types: List[str] = [
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/tiff",
        "application/pdf"
    ]
    gemini_model: str = "gemini-2.0-flash"
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600


# ============================================================================
# DATABASE MODELS
# ============================================================================

class TaskDB(BaseModel):
    """Database model for tasks"""
    id: Optional[int] = Field(None, description="Database ID")
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    request_data: str = Field(..., description="JSON string of request data")
    result_data: Optional[str] = Field(None, description="JSON string of result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            TaskStatus: lambda ts: ts.value
        }

    def to_analysis_request(self) -> AnalysisRequest:
        """Convert request_data JSON string back to AnalysisRequest"""
        import json
        return AnalysisRequest.model_validate(json.loads(self.request_data))

    def to_analysis_result(self) -> Optional[AnalysisResult]:
        """Convert result_data JSON string back to AnalysisResult"""
        import json
        if self.result_data:
            return AnalysisResult.model_validate(json.loads(self.result_data))
        return None

    @classmethod
    def from_request(cls, task_id: str, request: AnalysisRequest) -> 'TaskDB':
        """Create TaskDB from task_id and AnalysisRequest"""
        import json
        return cls(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0,
            request_data=request.model_dump_json(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
