# Central Event System & Trigger Listeners

The event listener integrates central platform operations with event-driven automation.

## Supported Event Signals

- `user_registered`
- `user_deleted`
- `document_uploaded`
- `document_indexed`
- `workflow_started`
- `workflow_completed`
- `agent_finished`
- `tool_executed`
- `plugin_installed`
- `plugin_updated`

## Webhook Dispatch & Reception

1. **Incoming Webhooks**: Triggered by sending a POST request to `/api/v1/automation/webhook`. It dispatches the custom event payload to `event_listener` to check for matching jobs.
2. **Outgoing Webhooks**: Used by the notification service to report completion status alerts to external endpoints.
