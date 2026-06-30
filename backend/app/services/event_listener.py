from typing import Any, Dict

from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.automation import AutomationJob


class EventListener:
    """
    Subscribes to central system events and triggers matching automation jobs.
    """

    def __init__(self):
        self._automation_service = None

    def set_automation_service(self, service):
        self._automation_service = service

    def notify_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Receives an ecosystem event and triggers matching enabled event-based automation jobs.
        """
        logger.info(
            f"[EventListener] Received event: {event_type} | Payload: {payload}"
        )

        if not self._automation_service:
            logger.warning(
                "AutomationService has not been registered in EventListener."
            )
            return

        db = SessionLocal()
        try:
            # Query enabled jobs matching this event_type (stored in cron_expression for trigger_type='event')
            matching_jobs = (
                db.query(AutomationJob)
                .filter(
                    AutomationJob.enabled,
                    AutomationJob.trigger_type == "event",
                    AutomationJob.cron_expression == event_type,
                )
                .all()
            )

            for job in matching_jobs:
                logger.info(
                    f"Event {event_type} matches Automation Job {job.id} ({job.name}). Triggering execution..."
                )
                # Merge variables with event payload
                import json

                vars_dict = {}
                if job.variables:
                    try:
                        vars_dict = json.loads(job.variables)
                    except Exception:
                        pass

                # Create merged execution context variables
                merged_vars = {**vars_dict, **payload}

                # Trigger job execution asynchronously
                self._automation_service.trigger_job(
                    db,
                    job_id=job.id,
                    trigger_source="event",
                    override_variables=merged_vars,
                )
        except Exception as e:
            logger.exception(
                f"Error handling event trigger for event {event_type}: {e}"
            )
        finally:
            db.close()


event_listener = EventListener()
