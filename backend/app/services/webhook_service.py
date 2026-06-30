import json
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.mcp_models import WebhookEndpoint, WebhookEvent, WebhookDelivery


class WebhookService:
    def create_endpoint(
        self, db: Session, *, workspace_id: int, url: str, secret_token: str, event_types: List[str]
    ) -> WebhookEndpoint:
        endpoint = WebhookEndpoint(
            workspace_id=workspace_id,
            url=url,
            secret_token=secret_token,
            enabled=True
        )
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)

        for event in event_types:
            db_event = WebhookEvent(endpoint_id=endpoint.id, event_type=event)
            db.add(db_event)
        db.commit()
        return endpoint

    def dispatch_event(self, db: Session, *, workspace_id: int, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Scans all registered webhooks for matching event type and dispatches payload.
        Logs delivery status codes and outcomes in the DB.
        """
        endpoints = (
            db.query(WebhookEndpoint)
            .join(WebhookEvent)
            .filter(
                WebhookEndpoint.workspace_id == workspace_id,
                WebhookEndpoint.enabled == True,
                WebhookEvent.event_type == event_type,
            )
            .all()
        )

        for end in endpoints:
            # Dispatch
            status_code = None
            response_body = None
            try:
                # Perform outgoing request
                res = httpx.post(
                    end.url,
                    json=payload,
                    headers={"x-webhook-signature": end.secret_token, "Content-Type": "application/json"},
                    timeout=5.0
                )
                status_code = res.status_code
                response_body = res.text[:500]  # Truncate large body
            except Exception as e:
                response_body = f"Delivery Error: {str(e)}"

            # Record delivery attempt log
            delivery = WebhookDelivery(
                endpoint_id=end.id,
                event_type=event_type,
                status_code=status_code,
                response_body=response_body,
                delivered_at=datetime.utcnow()
            )
            db.add(delivery)
        db.commit()


webhook_service = WebhookService()
