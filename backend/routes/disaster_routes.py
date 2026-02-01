"""
DisasterAI Backend - Disaster Monitoring Routes
API endpoints for disaster monitoring and alerting
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from models import (
    DisasterType,
    AlertLevel,
    AlertChannel,
    AlertPriority,
    DisasterEvent,
    AlertMessage
)
from services.disaster_service import get_disaster_service, DisasterMonitoringService
from services.alert_service import get_alert_service, AlertService
from services.external_data_service import get_external_data_service, fetch_live_disasters
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/disasters/types", tags=["Disasters"])
async def get_disaster_types():
    """Get all supported disaster types"""
    return [{"type": dt.value, "description": dt.value.replace('_', ' ').title()} for dt in DisasterType]


@router.get("/disasters/live", tags=["Disasters"])
async def get_live_disasters(
    source: Optional[str] = Query(None, description="Filter by source: usgs, gdacs"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to return")
):
    """
    Get LIVE disaster data from external sources (USGS Earthquakes, GDACS)
    
    This fetches real-time data from:
    - USGS: Real-time earthquake data worldwide
    - GDACS: Global Disaster Alert and Coordination System
    """
    try:
        events = await fetch_live_disasters()
        
        # Filter by source if specified
        if source:
            events = [e for e in events if e.source.lower() == source.lower()]
        
        # Limit results
        events = events[:limit]
        
        logger.info(f"Returning {len(events)} live disaster events")
        
        return [{
            "event_id": event.event_id,
            "disaster_type": event.disaster_type.value,
            "location": event.location,
            "coordinates": event.coordinates,
            "timestamp": event.timestamp.isoformat(),
            "alert_level": event.alert_level.value,
            "status": event.status,
            "magnitude": event.magnitude,
            "description": event.description,
            "source": event.source
        } for event in events]
        
    except Exception as e:
        logger.error(f"Error fetching live disasters: {str(e)}")
        raise HTTPException(500, f"Failed to fetch live disaster data: {str(e)}")


@router.get("/disasters/active", tags=["Disasters"])
async def get_active_disasters(
    disaster_type: Optional[str] = Query(None, description="Filter by disaster type"),
    alert_level: Optional[str] = Query(None, description="Filter by alert level"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return")
):
    """Get currently active disasters"""
    disaster_service = get_disaster_service()

    dt_enum = None
    al_enum = None

    if disaster_type:
        try:
            dt_enum = DisasterType(disaster_type.lower())
        except ValueError:
            raise HTTPException(400, f"Invalid disaster type: {disaster_type}")

    if alert_level:
        try:
            al_enum = AlertLevel(alert_level.lower())
        except ValueError:
            raise HTTPException(400, f"Invalid alert level: {alert_level}")

    events = await disaster_service.get_active_events(dt_enum, al_enum)
    events = events[:limit]

    return [{
        "event_id": event.event_id,
        "disaster_type": event.disaster_type.value,
        "location": event.location,
        "coordinates": event.coordinates,
        "timestamp": event.timestamp.isoformat(),
        "alert_level": event.alert_level.value,
        "status": event.status,
        "magnitude": event.magnitude,
        "description": event.description
    } for event in events]


@router.get("/disasters/historical", tags=["Disasters"])
async def get_historical_disasters(
    days_back: int = Query(30, ge=1, le=365, description="Number of days back to look"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return")
):
    """Get historical disasters"""
    disaster_service = get_disaster_service()
    events = await disaster_service.get_historical_events(days_back)
    events = events[:limit]

    return [{
        "event_id": event.event_id,
        "disaster_type": event.disaster_type.value,
        "location": event.location,
        "coordinates": event.coordinates,
        "timestamp": event.timestamp.isoformat(),
        "alert_level": event.alert_level.value,
        "status": event.status,
        "magnitude": event.magnitude,
        "description": event.description
    } for event in events]


@router.get("/disasters/location/{location}", tags=["Disasters"])
async def get_location_timeline(location: str):
    """Get disaster timeline for a specific location"""
    disaster_service = get_disaster_service()
    events = await disaster_service.get_event_timeline(location)

    return [{
        "event_id": event.event_id,
        "disaster_type": event.disaster_type.value,
        "location": event.location,
        "coordinates": event.coordinates,
        "timestamp": event.timestamp.isoformat(),
        "alert_level": event.alert_level.value,
        "status": event.status,
        "magnitude": event.magnitude,
        "description": event.description
    } for event in events]


@router.get("/disasters/stats", tags=["Disasters"])
async def get_disaster_statistics():
    """Get disaster statistics and summaries"""
    disaster_service = get_disaster_service()
    
    # Get internal stats
    internal_stats = await disaster_service.get_summary_statistics()
    
    # Get live data stats
    try:
        live_events = await fetch_live_disasters()
        
        # Calculate live stats
        total_active = len(live_events)
        
        # Distribution
        type_dist = internal_stats.get("disaster_type_distribution", {})
        alert_dist = internal_stats.get("current_alert_levels", {})
        
        for event in live_events:
            # Update type distribution
            d_type = event.disaster_type.value
            type_dist[d_type] = type_dist.get(d_type, 0) + 1
            
            # Update alert level distribution
            a_level = event.alert_level.value
            alert_dist[a_level] = alert_dist.get(a_level, 0) + 1
            
        # Update response
        internal_stats["total_active_events"] = internal_stats.get("total_active_events", 0) + total_active
        internal_stats["recent_activity"] = internal_stats.get("recent_activity", 0) + total_active
        internal_stats["disaster_type_distribution"] = type_dist
        internal_stats["current_alert_levels"] = alert_dist
        
    except Exception as e:
        logger.error(f"Error merging live stats: {e}")
        # Return internal stats only on failure to avoid breaking the UI
        
    return internal_stats


@router.post("/disasters/subscribe", tags=["Alerts"])
async def subscribe_to_alerts(area: str, user_id: str):
    """Subscribe to alerts for a specific area"""
    disaster_service = get_disaster_service()
    success = await disaster_service.subscribe_to_alerts(area, user_id)

    if success:
        logger.info(
            f"User {user_id} subscribed to alerts for area {area}",
            extra={'user_id': user_id, 'area': area}
        )
        return {"success": True, "message": f"Subscribed to alerts for {area}"}
    else:
        return {"success": True, "message": f"Already subscribed to alerts for {area}"}


@router.post("/disasters/unsubscribe", tags=["Alerts"])
async def unsubscribe_from_alerts(area: str, user_id: str):
    """Unsubscribe from alerts for a specific area"""
    disaster_service = get_disaster_service()
    success = await disaster_service.unsubscribe_from_alerts(area, user_id)

    if success:
        logger.info(
            f"User {user_id} unsubscribed from alerts for area {area}",
            extra={'user_id': user_id, 'area': area}
        )
        return {"success": True, "message": f"Unsubscribed from alerts for {area}"}
    else:
        raise HTTPException(404, f"Not subscribed to alerts for {area}")


@router.get("/alerts/active", tags=["Alerts"])
async def get_active_alerts(limit: int = Query(50, ge=1, le=1000)):
    """Get active alerts"""
    alert_service = get_alert_service()
    alerts = await alert_service.get_active_alerts(limit)
    return alerts


@router.get("/alerts/sent", tags=["Alerts"])
async def get_sent_alerts(limit: int = Query(50, ge=1, le=1000)):
    """Get sent alerts"""
    alert_service = get_alert_service()
    alerts = await alert_service.get_sent_alerts(limit)
    return alerts


@router.get("/alerts/{alert_id}", tags=["Alerts"])
async def get_alert_status(alert_id: str):
    """Get status of a specific alert"""
    alert_service = get_alert_service()
    status = await alert_service.get_alert_status(alert_id)

    if not status:
        raise HTTPException(404, f"Alert not found: {alert_id}")

    return status


@router.post("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(alert_id: str):
    """Acknowledge receipt of an alert"""
    alert_service = get_alert_service()
    success = await alert_service.acknowledge_alert(alert_id)

    if success:
        logger.info(
            f"Alert {alert_id} acknowledged",
            extra={'alert_id': alert_id}
        )
        return {"success": True, "message": "Alert acknowledged"}
    else:
        raise HTTPException(404, f"Alert not found: {alert_id}")


@router.get("/alerts/channels", tags=["Alerts"])
async def get_alert_channels():
    """Get all available alert channels"""
    return [{"channel": ac.value, "description": ac.value.replace('_', ' ').title()} for ac in AlertChannel]


@router.get("/alerts/priorities", tags=["Alerts"])
async def get_alert_priorities():
    """Get all available alert priorities"""
    return [{"priority": ap.value, "description": ap.name.title()} for ap in AlertPriority]


@router.get("/alerts/stats", tags=["Alerts"])
async def get_alert_statistics():
    """Get alert statistics"""
    alert_service = get_alert_service()

    active_count = len(alert_service.active_alerts)
    sent_count = len(alert_service.sent_alerts)

    # Get recent activity
    recent_sent = [a for a in alert_service.sent_alerts[-24:] if a.timestamp > datetime.utcnow() - timedelta(hours=24)]

    return {
        "active_alerts": active_count,
        "total_sent_alerts": sent_count,
        "recent_24h_alerts": len(recent_sent),
        "last_updated": datetime.utcnow().isoformat()
    }