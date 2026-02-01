"""
DisasterAI Backend - Disaster Monitoring Service
Handles multi-hazard disaster detection, classification, and tracking
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import logging
import uuid
from dataclasses import dataclass

from models import (
    AnalysisResult,
    AnalysisRequest,
    GeoJSONFeatureCollection,
    GeoJSONFeature,
    GeoJSONGeometry,
    GeoJSONProperties,
    ExtractedEntity,
    EntityLabel,
    SeverityLevel,
    TaskStatus
)
from models import DisasterType, AlertLevel, DisasterEvent, AlertMessage
from logging_config import get_logger
from config import settings


class DisasterMonitoringService:
    """
    Service for monitoring, detecting, and tracking various types of disasters
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.active_events: Dict[str, DisasterEvent] = {}
        self.historical_events: List[DisasterEvent] = []
        self.alert_subscriptions: Dict[str, List[str]] = {}  # area -> [user_ids]

    async def detect_disaster_from_analysis(self, analysis_result: AnalysisResult) -> List[DisasterEvent]:
        """
        Detect potential disaster events from an analysis result
        """
        self.logger.info(
            f"Detecting disasters from analysis result {analysis_result.taskId}",
            extra={'task_id': analysis_result.taskId}
        )

        events = []

        # Extract disaster-related entities and patterns
        disaster_entities = self._extract_disaster_entities(analysis_result)

        # Analyze geospatial features for disaster patterns
        geospatial_events = self._analyze_geospatial_features(analysis_result)

        # Combine all detected events
        events.extend(disaster_entities)
        events.extend(geospatial_events)

        # Validate and categorize events
        validated_events = await self._validate_events(events, analysis_result)

        # Add to active events
        for event in validated_events:
            self.active_events[event.event_id] = event
            self.logger.info(
                f"Detected disaster event: {event.disaster_type} at {event.location}",
                extra={
                    'event_id': event.event_id,
                    'disaster_type': event.disaster_type,
                    'alert_level': event.alert_level
                }
            )

        return validated_events

    def _extract_disaster_entities(self, analysis_result: AnalysisResult) -> List[DisasterEvent]:
        """
        Extract potential disaster events from named entities in analysis
        """
        events = []

        # Look for disaster-related entities
        disaster_keywords = {
            DisasterType.EARTHQUAKE: ['earthquake', 'seismic', 'quake', 'magnitude', 'richter'],
            DisasterType.FLOOD: ['flood', 'flooding', 'inundation', 'overflow', 'water level'],
            DisasterType.WILDFIRE: ['wildfire', 'fire', 'burn', 'smoke', 'flame', 'forest fire'],
            DisasterType.HURRICANE: ['hurricane', 'cyclone', 'typhoon', 'storm', 'wind'],
            DisasterType.TSUNAMI: ['tsunami', 'wave', 'ocean', 'coastal', 'tidal'],
            DisasterType.VOLCANIC: ['volcano', 'eruption', 'ash', 'lava', 'magma'],
            DisasterType.DROUGHT: ['drought', 'dry', 'arid', 'water shortage', 'desertification'],
            DisasterType.LANDSLIDE: ['landslide', 'mudslide', 'rockfall', 'slope failure'],
            DisasterType.BLIZZARD: ['blizzard', 'snow', 'ice', 'winter storm'],
            DisasterType.HEAT_WAVE: ['heat wave', 'temperature', 'hot', 'scorching'],
            DisasterType.AIR_QUALITY: ['pollution', 'smog', 'air quality', 'toxic gas']
        }

        # Check entities for disaster-related keywords
        for entity in analysis_result.entities:
            entity_lower = entity.text.lower()

            for disaster_type, keywords in disaster_keywords.items():
                if any(keyword in entity_lower for keyword in keywords):
                    # Try to extract coordinates from geospatial data
                    coords = self._extract_coordinates_from_geospatial(analysis_result, entity.text)

                    if coords:
                        event = DisasterEvent(
                            event_id=f"evt_{uuid.uuid4().hex[:12]}",
                            disaster_type=disaster_type,
                            location=entity.text,
                            coordinates=coords,
                            timestamp=analysis_result.timestamp,
                            alert_level=self._determine_alert_level(analysis_result.riskScore),
                            description=f"Potential {disaster_type.value} detected in {entity.text}",
                            magnitude=self._extract_magnitude(analysis_result, entity.text)
                        )
                        events.append(event)

        return events

    def _analyze_geospatial_features(self, analysis_result: AnalysisResult) -> List[DisasterEvent]:
        """
        Analyze geospatial features for disaster patterns
        """
        events = []

        for feature in analysis_result.geospatialData.features:
            # Look for patterns that indicate disasters
            if "damage" in feature.properties.description.lower() or \
               "emergency" in feature.properties.description.lower() or \
               "warning" in feature.properties.description.lower():

                # Determine disaster type based on description and severity
                disaster_type = self._infer_disaster_type(feature.properties.description)

                # Extract coordinates from geometry
                if feature.geometry.type == "Polygon" and feature.geometry.coordinates:
                    # Take center of polygon as coordinates
                    coords = self._polygon_center(feature.geometry.coordinates[0])
                else:
                    continue

                event = DisasterEvent(
                    event_id=f"geo_evt_{uuid.uuid4().hex[:12]}",
                    disaster_type=disaster_type,
                    location=feature.properties.name,
                    coordinates=coords,
                    timestamp=analysis_result.timestamp,
                    alert_level=feature.properties.severity.lower(),
                    description=feature.properties.description,
                    affected_area=feature.properties.confidence
                )
                events.append(event)

        return events

    def _infer_disaster_type(self, description: str) -> DisasterType:
        """
        Infer disaster type from description text
        """
        desc_lower = description.lower()

        if any(word in desc_lower for word in ['earthquake', 'seismic', 'quake']):
            return DisasterType.EARTHQUAKE
        elif any(word in desc_lower for word in ['flood', 'inundation', 'water']):
            return DisasterType.FLOOD
        elif any(word in desc_lower for word in ['fire', 'wildfire', 'burn']):
            return DisasterType.WILDFIRE
        elif any(word in desc_lower for word in ['hurricane', 'cyclone', 'typhoon', 'storm']):
            return DisasterType.HURRICANE
        elif any(word in desc_lower for word in ['tsunami', 'wave', 'ocean']):
            return DisasterType.TSUNAMI
        elif any(word in desc_lower for word in ['volcano', 'eruption', 'ash']):
            return DisasterType.VOLCANIC
        elif any(word in desc_lower for word in ['drought', 'dry', 'water shortage']):
            return DisasterType.DROUGHT
        elif any(word in desc_lower for word in ['landslide', 'mudslide', 'rockfall']):
            return DisasterType.LANDSLIDE
        elif any(word in desc_lower for word in ['blizzard', 'snow', 'ice']):
            return DisasterType.BLIZZARD
        elif any(word in desc_lower for word in ['heat wave', 'temperature']):
            return DisasterType.HEAT_WAVE
        elif any(word in desc_lower for word in ['pollution', 'smog', 'air quality']):
            return DisasterType.AIR_QUALITY
        else:
            return DisasterType.OTHER

    def _extract_coordinates_from_geospatial(self, analysis_result: AnalysisResult, location_name: str) -> Optional[Tuple[float, float]]:
        """
        Extract coordinates for a location from geospatial data
        """
        for feature in analysis_result.geospatialData.features:
            if location_name.lower() in feature.properties.name.lower():
                # For polygons, take the center of the first ring
                if feature.geometry.type == "Polygon" and feature.geometry.coordinates:
                    coords_ring = feature.geometry.coordinates[0]
                    center = self._polygon_center(coords_ring)
                    return center
        return None

    def _polygon_center(self, coords: List[List[float]]) -> Tuple[float, float]:
        """
        Calculate the center of a polygon
        """
        lon_sum = sum(coord[0] for coord in coords)
        lat_sum = sum(coord[1] for coord in coords)
        n = len(coords)
        return (lon_sum / n, lat_sum / n)

    def _determine_alert_level(self, risk_score: int) -> AlertLevel:
        """
        Determine alert level based on risk score
        """
        if risk_score >= 80:
            return AlertLevel.RED
        elif risk_score >= 60:
            return AlertLevel.ORANGE
        elif risk_score >= 40:
            return AlertLevel.YELLOW
        else:
            return AlertLevel.GREEN

    def _extract_magnitude(self, analysis_result: AnalysisResult, location: str) -> Optional[float]:
        """
        Extract magnitude value from analysis if available
        """
        # Look for magnitude indicators in summary or indicators
        summary_lower = analysis_result.summary.lower()

        import re
        # Look for magnitude patterns like "magnitude 7.2" or "7.2 magnitude"
        magnitude_pattern = r'(?:magnitude|mag\.?)\s*(\d+(?:\.\d+)?)'
        match = re.search(magnitude_pattern, summary_lower)

        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return None

    async def _validate_events(self, events: List[DisasterEvent], analysis_result: AnalysisResult) -> List[DisasterEvent]:
        """
        Validate and refine detected events
        """
        validated_events = []

        for event in events:
            # Apply additional validation rules
            if self._is_valid_disaster_event(event, analysis_result):
                validated_events.append(event)

        return validated_events

    def _is_valid_disaster_event(self, event: DisasterEvent, analysis_result: AnalysisResult) -> bool:
        """
        Validate if a detected event is likely a real disaster
        """
        # Basic validation rules
        if not event.location or len(event.location.strip()) < 2:
            return False

        # Check if coordinates are reasonable
        lon, lat = event.coordinates
        if abs(lon) > 180 or abs(lat) > 90:
            return False

        # For certain disaster types, validate magnitude ranges
        if event.disaster_type == DisasterType.EARTHQUAKE and event.magnitude:
            if event.magnitude < 1.0 or event.magnitude > 10.0:  # Richter scale bounds
                return False

        # Check if the alert level makes sense with the disaster type
        if event.disaster_type == DisasterType.DROUGHT and event.alert_level == AlertLevel.GREEN:
            # Droughts typically have longer-term impacts, so lower alert might be valid
            pass

        return True

    async def get_active_events(self, disaster_type: Optional[DisasterType] = None,
                               alert_level: Optional[AlertLevel] = None) -> List[DisasterEvent]:
        """
        Get active disaster events, optionally filtered by type or alert level
        """
        events = list(self.active_events.values())

        if disaster_type:
            events = [e for e in events if e.disaster_type == disaster_type]

        if alert_level:
            events = [e for e in events if e.alert_level == alert_level]

        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events

    async def get_historical_events(self, days_back: int = 30) -> List[DisasterEvent]:
        """
        Get historical disaster events
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        historical = [e for e in self.historical_events if e.timestamp >= cutoff_date]
        historical.sort(key=lambda e: e.timestamp, reverse=True)
        return historical

    async def get_event_timeline(self, location: str) -> List[DisasterEvent]:
        """
        Get timeline of events for a specific location
        """
        events = [e for e in self.active_events.values() if location.lower() in e.location.lower()]
        events.extend([e for e in self.historical_events if location.lower() in e.location.lower()])
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    async def subscribe_to_alerts(self, area: str, user_id: str) -> bool:
        """
        Subscribe a user to alerts for a specific area
        """
        if area not in self.alert_subscriptions:
            self.alert_subscriptions[area] = []

        if user_id not in self.alert_subscriptions[area]:
            self.alert_subscriptions[area].append(user_id)
            return True

        return False

    async def unsubscribe_from_alerts(self, area: str, user_id: str) -> bool:
        """
        Unsubscribe a user from alerts for a specific area
        """
        if area in self.alert_subscriptions and user_id in self.alert_subscriptions[area]:
            self.alert_subscriptions[area].remove(user_id)
            return True
        return False

    async def update_event_status(self, event_id: str, new_status: str) -> bool:
        """
        Update the status of a disaster event
        """
        if event_id in self.active_events:
            self.active_events[event_id].status = new_status
            if new_status in ['concluded', 'false_alarm']:
                # Move to historical if concluded
                event = self.active_events.pop(event_id)
                self.historical_events.append(event)
            return True
        return False

    async def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for all monitored events
        """
        active_events = list(self.active_events.values())
        historical_events = self.historical_events

        # Count by disaster type
        type_counts = {}
        for event in active_events + historical_events[-365:]:  # Last year
            disaster_type = event.disaster_type.value
            type_counts[disaster_type] = type_counts.get(disaster_type, 0) + 1

        # Count by alert level
        alert_counts = {}
        for event in active_events:
            alert_level = event.alert_level.value
            alert_counts[alert_level] = alert_counts.get(alert_level, 0) + 1

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_events = [e for e in active_events if e.timestamp >= yesterday]

        return {
            "total_active_events": len(active_events),
            "total_historical_events": len(historical_events),
            "disaster_type_distribution": type_counts,
            "current_alert_levels": alert_counts,
            "recent_activity": len(recent_events),
            "last_updated": datetime.utcnow().isoformat()
        }


# Singleton instance
_disaster_service: Optional[DisasterMonitoringService] = None


def get_disaster_service() -> DisasterMonitoringService:
    """Get or create disaster monitoring service instance"""
    global _disaster_service
    if _disaster_service is None:
        _disaster_service = DisasterMonitoringService()
    return _disaster_service