"""
DisasterAI Backend - Geocoding Service
Handles location name to coordinates resolution
"""

import math
import random
from typing import Optional, List, Dict, Tuple
from functools import lru_cache

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from tenacity import retry, stop_after_attempt, wait_exponential

from models import (
    GeocodingResult,
    BatchGeocodingResult,
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONProperties,
    SeverityLevel
)
from config import settings


class GeocodingService:
    """
    Service for geocoding location names to coordinates.
    Uses Nominatim (OpenStreetMap) for geocoding.
    """
    
    def __init__(self):
        self.geocoder = Nominatim(
            user_agent=settings.GEOCODING_USER_AGENT,
            timeout=10
        )
        self._cache: Dict[str, GeocodingResult] = {}
    
    def _get_cache_key(self, location: str, context: Optional[str]) -> str:
        """Generate cache key for location"""
        return f"{location.lower().strip()}:{context or ''}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def geocode_location(
        self,
        location_name: str,
        context: Optional[str] = None
    ) -> Optional[GeocodingResult]:
        """
        Geocode a single location name.
        
        Args:
            location_name: Name of the location to geocode
            context: Optional context like country/region for disambiguation
            
        Returns:
            GeocodingResult or None if not found
        """
        cache_key = self._get_cache_key(location_name, context)
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Build query with context
            query = location_name
            if context:
                query = f"{location_name}, {context}"
            
            # Perform geocoding
            location = self.geocoder.geocode(query, exactly_one=True)
            
            if location:
                result = GeocodingResult(
                    location_name=location_name,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    confidence=0.9,  # Nominatim doesn't provide confidence
                    formatted_address=location.address
                )
                
                # Extract country/region from address
                address_parts = location.address.split(", ")
                if len(address_parts) >= 2:
                    result.country = address_parts[-1]
                    if len(address_parts) >= 3:
                        result.region = address_parts[-2]
                
                # Cache result
                self._cache[cache_key] = result
                return result
            
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error for {location_name}: {e}")
            return None
    
    async def batch_geocode(
        self,
        locations: List[str],
        context: Optional[str] = None
    ) -> BatchGeocodingResult:
        """
        Geocode multiple locations.
        
        Args:
            locations: List of location names
            context: Optional context for all locations
            
        Returns:
            BatchGeocodingResult with results and failed locations
        """
        results = []
        failed = []
        
        for location in locations:
            result = await self.geocode_location(location, context)
            if result:
                results.append(result)
            else:
                failed.append(location)
        
        return BatchGeocodingResult(results=results, failed=failed)
    
    def generate_polygon(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float = 1.0,
        num_vertices: int = 8
    ) -> List[List[float]]:
        """
        Generate an organic-looking polygon around a center point.
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Approximate radius in kilometers
            num_vertices: Number of polygon vertices (8-12 recommended)
            
        Returns:
            List of [lon, lat] coordinates forming a closed polygon
        """
        # Convert radius to approximate degrees
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude varies with latitude
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        coordinates = []
        for i in range(num_vertices):
            angle = 2 * math.pi * i / num_vertices
            
            # Add organic variation
            variation = 0.7 + random.random() * 0.6  # 0.7 to 1.3 multiplier
            
            lat = center_lat + lat_offset * math.sin(angle) * variation
            lon = center_lon + lon_offset * math.cos(angle) * variation
            
            coordinates.append([round(lon, 6), round(lat, 6)])
        
        # Close the polygon
        coordinates.append(coordinates[0])
        
        return coordinates
    
    async def create_geojson_feature(
        self,
        location_name: str,
        severity: SeverityLevel = SeverityLevel.LOW,
        description: str = "",
        confidence: str = "90%",
        context: Optional[str] = None,
        radius_km: float = 1.0
    ) -> Optional[GeoJSONFeature]:
        """
        Create a GeoJSON feature for a location.
        
        Args:
            location_name: Name of the location
            severity: Severity level for the feature
            description: Description of the location status
            confidence: Confidence percentage string
            context: Optional geocoding context
            radius_km: Radius for the polygon
            
        Returns:
            GeoJSONFeature or None if geocoding fails
        """
        geocode_result = await self.geocode_location(location_name, context)
        
        if not geocode_result:
            return None
        
        polygon_coords = self.generate_polygon(
            geocode_result.latitude,
            geocode_result.longitude,
            radius_km=radius_km
        )
        
        return GeoJSONFeature(
            geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[polygon_coords]
            ),
            properties=GeoJSONProperties(
                name=location_name,
                confidence=confidence,
                severity=severity,
                description=description or f"Location: {geocode_result.formatted_address}"
            )
        )


# Known locations cache for common disaster-prone areas
KNOWN_LOCATIONS: Dict[str, Tuple[float, float]] = {
    "chennai": (13.0827, 80.2707),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "bhubaneswar": (20.2961, 85.8245),
    "vishakhapatnam": (17.6868, 83.2185),
    "kochi": (9.9312, 76.2673),
    "thiruvananthapuram": (8.5241, 76.9366),
    "guwahati": (26.1445, 91.7362),
}


def get_quick_coordinates(location_name: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for known locations without API call.
    
    Args:
        location_name: Name of the location
        
    Returns:
        Tuple of (lat, lon) or None
    """
    normalized = location_name.lower().strip()
    
    # Check direct match
    if normalized in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[normalized]
    
    # Check partial match
    for name, coords in KNOWN_LOCATIONS.items():
        if name in normalized or normalized in name:
            return coords
    
    return None


# Singleton instance
_service: Optional[GeocodingService] = None


def get_geocoding_service() -> GeocodingService:
    """Get or create geocoding service instance"""
    global _service
    if _service is None:
        _service = GeocodingService()
    return _service
