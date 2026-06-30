from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logging import logger
from app.models.automation import Notification


class NotificationService:
    """
    Dispatcher managing notifications via Email, Webhooks, Slack, Discord, and Teams.
    """

    def send_notification(
        self,
        db: Session,
        provider: str,
        recipient: str,
        subject: Optional[str],
        message: str,
    ) -> Notification:
        # Create database entry
        db_obj = Notification(
            provider=provider.lower(),
            recipient=recipient,
            subject=subject,
            message=message,
            status="pending",
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        try:
            prov = provider.lower()
            if prov == "email":
                success = self._send_email(
                    recipient, subject or "Ecosystem Alert", message
                )
            elif prov == "webhook":
                success = self._send_webhook(recipient, message)
            elif prov in ["slack", "discord", "teams"]:
                success = self._send_placeholder_chat(prov, recipient, message)
            else:
                logger.error(f"Unsupported notification provider: {provider}")
                success = False

            if success:
                db_obj.status = "sent"
                db_obj.sent_at = datetime.now(timezone.utc)
            else:
                db_obj.status = "failed"

            db.commit()
            db.refresh(db_obj)
        except Exception as e:
            logger.exception(f"Failed to dispatch notification via {provider}: {e}")
            db_obj.status = "failed"
            db.commit()

        return db_obj

    def _send_email(self, recipient: str, subject: str, message: str) -> bool:
        if not settings.ENABLE_EMAIL_NOTIFICATIONS:
            logger.info(
                f"[Email Simulation] To: {recipient} | Subject: {subject} | Msg: {message}"
            )
            return True

        # Simulating standard SMTP dispatch
        try:
            logger.info(f"Sending SMTP email to {recipient}...")
            # For this MVP, logging is enough, return True
            return True
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False

    def _send_webhook(self, url: str, message: str) -> bool:
        if not settings.ENABLE_WEBHOOK_NOTIFICATIONS:
            logger.info(f"[Webhook Simulation] Endpoint: {url} | Payload: {message}")
            return True

        try:
            # Send HTTP POST request
            payload = {
                "event": "automation_alert",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
            logger.info(f"Webhook successfully dispatched to {url}.")
            return True
        except Exception as e:
            logger.error(f"Webhook dispatch to {url} failed: {e}")
            return False

    def _send_placeholder_chat(
        self, platform: str, webhook_url: str, message: str
    ) -> bool:
        logger.info(
            f"[{platform.upper()} Alert Placeholder] Channel Hook: {webhook_url} | Msg: {message}"
        )

        # Real HTTP Webhook can be dispatched if configured
        if webhook_url.startswith("http"):
            try:
                # Build typical chat webhook body
                payload = {}
                if platform == "slack":
                    payload = {"text": message}
                elif platform == "discord":
                    payload = {"content": message}
                elif platform == "teams":
                    payload = {"text": message}

                with httpx.Client(timeout=5.0) as client:
                    res = client.post(webhook_url, json=payload)
                    res.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Failed to post to {platform} webhook: {e}")
                return False
        return True


notification_service = NotificationService()
