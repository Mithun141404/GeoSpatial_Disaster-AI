"""
DisasterAI Backend - Alerting Service
Handles real-time disaster alerts and notifications
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import logging
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models import (
    AnalysisResult,
    AnalysisRequest,
    TaskStatus,
    DisasterType,
    AlertLevel,
    AlertChannel,
    AlertPriority,
    DisasterEvent,
    AlertMessage
)
from logging_config import get_logger
from config import settings
from services.disaster_service import get_disaster_service


class AlertService:
    """
    Service for managing real-time disaster alerts and notifications
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.active_alerts: Dict[str, AlertMessage] = {}
        self.sent_alerts: List[AlertMessage] = []
        self.alert_callbacks: List[Callable] = []
        self.max_alert_history = 1000

    async def create_alert_from_event(self, event: DisasterEvent) -> Optional[AlertMessage]:
        """
        Create an alert message from a disaster event
        """
        self.logger.info(
            f"Creating alert for disaster event {event.event_id}",
            extra={
                'event_id': event.event_id,
                'disaster_type': event.disaster_type,
                'alert_level': event.alert_level
            }
        )

        # Determine priority based on alert level and disaster type
        priority = self._determine_priority(event.alert_level, event.disaster_type)

        # Create alert message
        message = self._generate_alert_message(event)

        # Determine appropriate channels based on severity
        channels = self._determine_channels(event.alert_level, event.disaster_type)

        alert = AlertMessage(
            alert_id=f"alert_{event.event_id}",
            event_id=event.event_id,
            disaster_type=event.disaster_type,
            location=event.location,
            coordinates=event.coordinates,
            alert_level=event.alert_level,
            priority=priority,
            message=message,
            timestamp=datetime.utcnow(),
            channels=channels,
            recipients=[]  # Will be populated based on subscriptions
        )

        # Get recipients for this alert
        disaster_service = get_disaster_service()
        subscribers = await disaster_service.alert_subscriptions.get(event.location, [])

        # If no specific location subscribers, get broader area subscribers
        if not subscribers:
            # Try to find subscribers for broader regions
            for area, area_subscribers in disaster_service.alert_subscriptions.items():
                if area.lower() in event.location.lower() or event.location.lower() in area.lower():
                    subscribers.extend(area_subscribers)

        alert.recipients = list(set(subscribers))  # Remove duplicates

        # Store alert
        self.active_alerts[alert.alert_id] = alert

        self.logger.info(
            f"Alert created for {event.disaster_type} at {event.location}",
            extra={
                'alert_id': alert.alert_id,
                'recipient_count': len(alert.recipients),
                'priority': priority
            }
        )

        return alert

    def _determine_priority(self, alert_level: AlertLevel, disaster_type: DisasterType) -> AlertPriority:
        """
        Determine alert priority based on alert level and disaster type
        """
        if alert_level == AlertLevel.BLACK:
            return AlertPriority.CRITICAL
        elif alert_level == AlertLevel.RED:
            return AlertPriority.CRITICAL
        elif alert_level == AlertLevel.ORANGE:
            return AlertPriority.HIGH
        elif alert_level == AlertLevel.YELLOW:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW

    def _generate_alert_message(self, event: DisasterEvent) -> str:
        """
        Generate human-readable alert message from disaster event
        """
        base_message = f"🚨 DISASTER ALERT 🚨\n"
        base_message += f"Type: {event.disaster_type.value.title()}\n"
        base_message += f"Location: {event.location}\n"
        base_message += f"Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        base_message += f"Severity: {event.alert_level.value.upper()}\n"

        if event.magnitude:
            base_message += f"Magnitude: {event.magnitude}\n"

        if event.description:
            base_message += f"Details: {event.description}\n"

        base_message += f"\nStay safe and follow local emergency instructions."

        return base_message

    def _determine_channels(self, alert_level: AlertLevel, disaster_type: DisasterType) -> List[AlertChannel]:
        """
        Determine which channels to use based on alert level and disaster type
        """
        channels = [AlertChannel.WEBHOOK]  # Always send to webhook for system integration

        if alert_level in [AlertLevel.RED, AlertLevel.BLACK]:
            # Critical alerts use all channels
            channels.extend([AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.MOBILE_PUSH])
        elif alert_level == AlertLevel.ORANGE:
            # High alerts use email and mobile push
            channels.extend([AlertChannel.EMAIL, AlertChannel.MOBILE_PUSH])
        elif alert_level == AlertLevel.YELLOW:
            # Medium alerts use email and webhook
            channels.append(AlertChannel.EMAIL)
        else:
            # Low alerts only use webhook
            pass

        return channels

    async def send_alert(self, alert: AlertMessage) -> bool:
        """
        Send an alert through all specified channels
        """
        self.logger.info(
            f"Sending alert {alert.alert_id} via {len(alert.channels)} channels",
            extra={
                'alert_id': alert.alert_id,
                'channels': [ch.value for ch in alert.channels],
                'recipient_count': len(alert.recipients)
            }
        )

        success = True

        for channel in alert.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_alert(alert)
                elif channel == AlertChannel.MOBILE_PUSH:
                    await self._send_mobile_push_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert)
                elif channel == AlertChannel.PUSH:
                    await self._send_push_notification_alert(alert)

                self.logger.debug(
                    f"Alert sent successfully via {channel}",
                    extra={'alert_id': alert.alert_id, 'channel': channel.value}
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to send alert via {channel}: {str(e)}",
                    extra={
                        'alert_id': alert.alert_id,
                        'channel': channel.value,
                        'error': str(e)
                    }
                )
                success = False

        # Move alert to sent alerts
        self.sent_alerts.append(alert)
        if alert.alert_id in self.active_alerts:
            del self.active_alerts[alert.alert_id]

        # Keep alert history manageable
        if len(self.sent_alerts) > self.max_alert_history:
            self.sent_alerts = self.sent_alerts[-self.max_alert_history:]

        # Trigger callbacks
        await self._trigger_callbacks(alert, success)

        return success

    async def _send_email_alert(self, alert: AlertMessage) -> bool:
        """
        Send alert via email
        """
        if not settings.SMTP_SERVER:
            self.logger.warning("SMTP server not configured, skipping email alert")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL or "alerts@disasterai.com"
            msg['Subject'] = f"[DISASTER ALERT] {alert.disaster_type.value.title()} - {alert.alert_level.value.upper()}"

            msg.attach(MIMEText(alert.message, 'plain'))

            # In a real implementation, you would send the email here
            # For now, we'll just log it
            self.logger.info(
                f"Email alert prepared for {len(alert.recipients)} recipients",
                extra={'alert_id': alert.alert_id}
            )

            return True
        except Exception as e:
            self.logger.error(f"Error preparing email alert: {str(e)}")
            return False

    async def _send_sms_alert(self, alert: AlertMessage) -> bool:
        """
        Send alert via SMS
        """
        # Placeholder for SMS implementation
        # In a real system, you would integrate with an SMS provider
        self.logger.info(
            f"SMS alert would be sent to {len(alert.recipients)} recipients",
            extra={'alert_id': alert.alert_id}
        )
        return True

    async def _send_mobile_push_alert(self, alert: AlertMessage) -> bool:
        """
        Send alert via mobile push notification
        """
        # Placeholder for push notification implementation
        # In a real system, you would integrate with Firebase Cloud Messaging, APNs, etc.
        self.logger.info(
            f"Mobile push alert would be sent to {len(alert.recipients)} recipients",
            extra={'alert_id': alert.alert_id}
        )
        return True

    async def _send_webhook_alert(self, alert: AlertMessage) -> bool:
        """
        Send alert via webhook to registered endpoints
        """
        import httpx

        # Get webhook URLs from configuration or database
        webhook_urls = getattr(settings, 'ALERT_WEBHOOK_URLS', [])

        if not webhook_urls:
            self.logger.warning("No webhook URLs configured, skipping webhook alert")
            return False

        success = True
        for url in webhook_urls:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json=alert.__dict__,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code != 200:
                        self.logger.warning(
                            f"Webhook returned status {response.status_code}",
                            extra={'webhook_url': url, 'alert_id': alert.alert_id}
                        )
                        success = False
            except Exception as e:
                self.logger.error(
                    f"Error sending webhook alert: {str(e)}",
                    extra={'webhook_url': url, 'alert_id': alert.alert_id}
                )
                success = False

        return success

    async def _send_push_notification_alert(self, alert: AlertMessage) -> bool:
        """
        Send push notification alert
        """
        # Placeholder for generic push notification
        self.logger.info(
            f"Push notification alert would be sent to {len(alert.recipients)} recipients",
            extra={'alert_id': alert.alert_id}
        )
        return True

    async def _trigger_callbacks(self, alert: AlertMessage, success: bool) -> None:
        """
        Trigger registered callbacks for alert delivery
        """
        for callback in self.alert_callbacks:
            try:
                await callback(alert, success)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")

    def register_callback(self, callback: Callable) -> None:
        """
        Register a callback function to be called when alerts are delivered
        """
        self.alert_callbacks.append(callback)

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as acknowledged
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            return True
        elif any(a.alert_id == alert_id for a in self.sent_alerts):
            for alert in self.sent_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.utcnow()
                    break
            return True
        return False

    async def get_alert_status(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific alert
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            return {
                'alert_id': alert.alert_id,
                'status': 'active',
                'acknowledged': alert.acknowledged,
                'sent_at': alert.timestamp.isoformat(),
                'channels': [ch.value for ch in alert.channels]
            }
        elif any(a.alert_id == alert_id for a in self.sent_alerts):
            for alert in self.sent_alerts:
                if alert.alert_id == alert_id:
                    return {
                        'alert_id': alert.alert_id,
                        'status': 'sent',
                        'acknowledged': alert.acknowledged,
                        'sent_at': alert.timestamp.isoformat(),
                        'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                        'channels': [ch.value for ch in alert.channels]
                    }
        return None

    async def get_active_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get active alerts
        """
        alerts = list(self.active_alerts.values())
        alerts.sort(key=lambda a: a.priority, reverse=True)  # Higher priority first
        return [self._alert_to_dict(alert) for alert in alerts[:limit]]

    async def get_sent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get sent alerts
        """
        alerts = self.sent_alerts[-limit:]  # Most recent first
        alerts.reverse()
        return [self._alert_to_dict(alert) for alert in alerts]

    def _alert_to_dict(self, alert: AlertMessage) -> Dict[str, Any]:
        """
        Convert AlertMessage to dictionary for API response
        """
        return {
            'alert_id': alert.alert_id,
            'event_id': alert.event_id,
            'disaster_type': alert.disaster_type.value,
            'location': alert.location,
            'coordinates': alert.coordinates,
            'alert_level': alert.alert_level.value,
            'priority': alert.priority,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'channels': [ch.value for ch in alert.channels],
            'recipient_count': len(alert.recipients),
            'acknowledged': alert.acknowledged,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        }

    async def process_new_disaster_event(self, event: DisasterEvent) -> Optional[AlertMessage]:
        """
        Process a new disaster event and create/send appropriate alerts
        """
        # Create alert from event
        alert = await self.create_alert_from_event(event)

        if alert:
            # Send the alert
            await self.send_alert(alert)
            return alert

        return None


# Singleton instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get or create alert service instance"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service