"""Webhook service for external integrations."""
import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from sqlalchemy.orm import Session

from models import Webhook, WebhookLog, WebhookEventType


class WebhookService:
    """Service for managing and triggering webhooks."""

    @staticmethod
    def create_signature(payload: str, secret: str) -> str:
        """Create HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def trigger_webhook(
        self,
        db: Session,
        event_type: WebhookEventType,
        payload_data: Dict[str, Any]
    ):
        """Trigger all webhooks subscribed to this event type."""
        # Get all active webhooks for this event
        webhooks = db.query(Webhook).filter(
            Webhook.is_active == True,
            Webhook.events.contains(event_type.value)
        ).all()

        for webhook in webhooks:
            asyncio.create_task(
                self._send_webhook(db, webhook, event_type.value, payload_data)
            )

    async def _send_webhook(
        self,
        db: Session,
        webhook: Webhook,
        event_type: str,
        payload_data: Dict[str, Any]
    ):
        """Send webhook to configured URL."""
        # Prepare payload
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload_data
        }

        payload_json = json.dumps(payload)

        # Create log entry
        log = WebhookLog(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload_json,
            triggered_at=datetime.utcnow()
        )

        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Digiskills-Webhook/1.0"
            }

            # Add signature if secret is configured
            if webhook.secret:
                signature = self.create_signature(payload_json, webhook.secret)
                headers["X-Webhook-Signature"] = signature

            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    headers=headers,
                    data=payload_json,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    log.response_status = response.status
                    log.response_body = await response.text()
                    log.delivered_at = datetime.utcnow()

                    # Update webhook last triggered time
                    webhook.last_triggered_at = datetime.utcnow()

        except asyncio.TimeoutError:
            log.error_message = "Request timeout"
        except aiohttp.ClientError as e:
            log.error_message = f"Client error: {str(e)}"
        except Exception as e:
            log.error_message = f"Unexpected error: {str(e)}"

        # Save log
        db.add(log)
        db.commit()


# Global webhook service instance
webhook_service = WebhookService()
