# Job Scheduler Service

The Scheduler Service is built around **APScheduler**'s `AsyncIOScheduler` to manage time-based triggers.

## Trigger Types

1. **Cron**: Triggers runs based on standard cron tab format strings (e.g. `*/5 * * * *`).
2. **Interval**: Triggers runs at fixed frequencies in seconds.
3. **Manual**: Executed manually on request.
4. **Event**: Triggered when a matching system event is published.

## Restart Recovery Routine

On application boot (within the lifespan events context), the scheduler:
1. Identifies any executions left in `Pending`, `Queued`, or `Running` states from the previous run.
2. Automatically transitions them to `Failed` with error message `Ecosystem restart: Execution interrupted`.
3. Loads all enabled scheduled jobs from the database and inserts them into APScheduler.
