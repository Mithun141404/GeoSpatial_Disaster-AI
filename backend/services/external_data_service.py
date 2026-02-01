"""
DisasterAI Backend - External Data Sources
Fetches real-time disaster data from public APIs
"""

import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import logging

from models import DisasterType, AlertLevel, DisasterEvent
from logging_config import get_logger

logger = get_logger(__name__)

# USGS Earthquake API
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"

# GDACS API (Global Disaster Alert and Coordination System)
GDACS_API_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist"


class ExternalDataService:
    """Service for fetching real-time disaster data from external APIs"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.client = httpx.AsyncClient(timeout=30.0)
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes cache
        self._last_fetch: Dict[str, datetime] = {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid"""
        if key not in self._last_fetch:
            return False
        return (datetime.now(timezone.utc) - self._last_fetch[key]).seconds < self._cache_ttl
    
    async def fetch_usgs_earthquakes(self, timeframe: str = "day") -> List[DisasterEvent]:
        """
        Fetch earthquake data from USGS API
        
        Args:
            timeframe: 'hour', 'day', 'week', or 'month'
        
        Returns:
            List of DisasterEvent objects
        """
        cache_key = f"usgs_{timeframe}"
        
        if self._is_cache_valid(cache_key) and cache_key in self._cache:
            return self._cache[cache_key]
        
        events = []
        
        try:
            # USGS provides different feeds based on magnitude and timeframe
            # all_hour, all_day, all_week, all_month for all magnitudes
            url = f"{USGS_API_URL}/all_{timeframe}.geojson"
            
            self.logger.info(f"Fetching USGS earthquake data: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            features = data.get("features", [])
            
            self.logger.info(f"Retrieved {len(features)} earthquakes from USGS")
            
            for feature in features[:50]:  # Limit to 50 most recent
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [0, 0, 0])
                
                # Determine alert level based on magnitude
                magnitude = props.get("mag", 0)
                alert_level = self._magnitude_to_alert_level(magnitude)
                
                # Parse timestamp
                timestamp_ms = props.get("time", 0)
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                
                event = DisasterEvent(
                    event_id=f"usgs_{feature.get('id', '')}",
                    disaster_type=DisasterType.EARTHQUAKE,
                    location=props.get("place", "Unknown location"),
                    coordinates=(coords[0], coords[1]),  # lon, lat
                    timestamp=timestamp,
                    alert_level=alert_level,
                    magnitude=magnitude,
                    description=f"Magnitude {magnitude} earthquake. Depth: {coords[2]:.1f} km. {props.get('title', '')}",
                    source="USGS",
                    status="active" if props.get("status") != "reviewed" else "verified"
                )
                events.append(event)
            
            # Cache results
            self._cache[cache_key] = events
            self._last_fetch[cache_key] = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error fetching USGS data: {str(e)}")
        
        return events
    
    def _magnitude_to_alert_level(self, magnitude: float) -> AlertLevel:
        """Convert earthquake magnitude to alert level"""
        if magnitude >= 7.0:
            return AlertLevel.BLACK
        elif magnitude >= 6.0:
            return AlertLevel.RED
        elif magnitude >= 5.0:
            return AlertLevel.ORANGE
        elif magnitude >= 4.0:
            return AlertLevel.YELLOW
        else:
            return AlertLevel.GREEN
    
    async def fetch_gdacs_events(self) -> List[DisasterEvent]:
        """
        Fetch disaster events from GDACS API
        
        Returns:
            List of DisasterEvent objects
        """
        cache_key = "gdacs_all"
        
        if self._is_cache_valid(cache_key) and cache_key in self._cache:
            return self._cache[cache_key]
        
        events = []
        
        try:
            # GDACS RSS feed as fallback (more reliable than their API)
            url = "https://www.gdacs.org/xml/rss.xml"
            
            self.logger.info(f"Fetching GDACS disaster data")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse XML RSS feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            for item in root.findall(".//item")[:30]:  # Limit to 30 events
                try:
                    title = item.find("title")
                    title_text = title.text if title is not None else "Unknown Event"
                    
                    description = item.find("description")
                    desc_text = description.text if description is not None else ""
                    
                    pub_date = item.find("pubDate")
                    
                    # Parse disaster type from title
                    disaster_type = self._parse_disaster_type(title_text)
                    
                    # Try to extract coordinates from georss:point if available
                    coords = (0.0, 0.0)
                    point = item.find("{http://www.georss.org/georss}point")
                    if point is not None and point.text:
                        parts = point.text.strip().split()
                        if len(parts) >= 2:
                            coords = (float(parts[1]), float(parts[0]))  # lon, lat
                    
                    # Extract alert level from gdacs:alertlevel if available
                    alert_elem = item.find("{http://www.gdacs.org}alertlevel")
                    alert_level = AlertLevel.YELLOW
                    if alert_elem is not None and alert_elem.text:
                        alert_map = {
                            "Red": AlertLevel.RED,
                            "Orange": AlertLevel.ORANGE,
                            "Green": AlertLevel.GREEN
                        }
                        alert_level = alert_map.get(alert_elem.text, AlertLevel.YELLOW)
                    
                    # Parse timestamp
                    timestamp = datetime.now(timezone.utc)
                    if pub_date is not None and pub_date.text:
                        try:
                            from email.utils import parsedate_to_datetime
                            timestamp = parsedate_to_datetime(pub_date.text)
                            if timestamp.tzinfo is None:
                                timestamp = timestamp.replace(tzinfo=timezone.utc)
                        except:
                            pass
                    
                    event = DisasterEvent(
                        event_id=f"gdacs_{hash(title_text) % 1000000}",
                        disaster_type=disaster_type,
                        location=title_text,
                        coordinates=coords,
                        timestamp=timestamp,
                        alert_level=alert_level,
                        description=desc_text[:500] if desc_text else title_text,
                        source="GDACS",
                        status="active"
                    )
                    events.append(event)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing GDACS item: {e}")
                    continue
            
            # Cache results
            self._cache[cache_key] = events
            self._last_fetch[cache_key] = datetime.now(timezone.utc)
            
            self.logger.info(f"Retrieved {len(events)} events from GDACS")
            
        except Exception as e:
            self.logger.error(f"Error fetching GDACS data: {str(e)}")
        
        return events
    
    def _parse_disaster_type(self, title: str) -> DisasterType:
        """Parse disaster type from event title"""
        title_lower = title.lower()
        
        if "earthquake" in title_lower or "quake" in title_lower:
            return DisasterType.EARTHQUAKE
        elif "flood" in title_lower:
            return DisasterType.FLOOD
        elif "cyclone" in title_lower:
            return DisasterType.CYCLONE
        elif "hurricane" in title_lower:
            return DisasterType.HURRICANE
        elif "typhoon" in title_lower:
            return DisasterType.TYPHOON
        elif "tsunami" in title_lower:
            return DisasterType.TSUNAMI
        elif "volcano" in title_lower or "volcanic" in title_lower:
            return DisasterType.VOLCANIC
        elif "storm" in title_lower:
            return DisasterType.STORM
        elif "drought" in title_lower:
            return DisasterType.DROUGHT
        elif "fire" in title_lower or "wildfire" in title_lower:
            return DisasterType.WILDFIRE
        elif "tornado" in title_lower:
            return DisasterType.TORNADO
        else:
            return DisasterType.OTHER
    
    async def fetch_all_disasters(self) -> List[DisasterEvent]:
        """
        Fetch disasters from all available sources
        
        Returns:
            Combined list of DisasterEvent objects
        """
        all_events = []
        
        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.fetch_usgs_earthquakes("day"),
            self.fetch_gdacs_events(),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error fetching data: {result}")
        
        # Sort by timestamp (most recent first)
        all_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return all_events


# Singleton instance
_external_service: Optional[ExternalDataService] = None


def get_external_data_service() -> ExternalDataService:
    """Get or create external data service instance"""
    global _external_service
    if _external_service is None:
        _external_service = ExternalDataService()
    return _external_service


async def fetch_live_disasters() -> List[DisasterEvent]:
    """Convenience function to fetch all live disasters"""
    service = get_external_data_service()
    return await service.fetch_all_disasters()
