import asyncio
import time
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.core.logging import logger

PRIORITY_MAP = {
    "CRITICAL": 0,
    "HIGH": 1,
    "NORMAL": 2,
    "LOW": 3,
}


class InMemoryPriorityTaskQueue:
    """
    Ecosystem background priority task execution queue.
    """

    def __init__(self):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, Dict[str, Any]] = (
            {}
        )  # execution_uuid -> task details
        self.workers: list = []
        self._executor_callback = None
        self._is_running = False
        self.loop = None

    def set_executor_callback(self, callback):
        self._executor_callback = callback

    def start(self):
        if self._is_running:
            return
        self._is_running = True
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None
        max_workers = settings.MAX_PARALLEL_JOBS
        for i in range(max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker)
        logger.info(f"Task queue started with {max_workers} parallel workers.")

    async def stop(self):
        self._is_running = False
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        logger.info("Task queue stopped successfully.")

    def enqueue(
        self,
        job_id: int,
        execution_uuid: str,
        priority: str,
        variables: Dict[str, Any],
        trigger_source: str,
    ):
        priority_val = PRIORITY_MAP.get(priority.upper(), 2)  # default NORMAL
        item = (
            priority_val,
            time.time(),
            execution_uuid,
            job_id,
            variables,
            trigger_source,
        )
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.queue.put_nowait, item)
        else:
            self.queue.put_nowait(item)

        # Initialize running metadata in Pending state
        self.running_tasks[execution_uuid] = {
            "job_id": job_id,
            "status": "Queued",
            "percentage": 0,
            "current_step": "Enqueued in task queue",
            "started_at": time.time(),
            "updated_at": time.time(),
            "asyncio_task": None,
        }
        logger.info(
            f"Job {job_id} (Execution: {execution_uuid}) enqueued with priority {priority}."
        )

    async def _worker_loop(self, worker_id: int):
        while self._is_running:
            try:
                # Get next task from priority queue
                (
                    priority_val,
                    enqueue_time,
                    execution_uuid,
                    job_id,
                    variables,
                    trigger_source,
                ) = await self.queue.get()

                if not self._is_running:
                    self.queue.task_done()
                    break

                # Check if already cancelled
                task_meta = self.running_tasks.get(execution_uuid)
                if task_meta and task_meta["status"] == "Cancelled":
                    self.queue.task_done()
                    continue

                # Prepare for running
                self.running_tasks[execution_uuid]["status"] = "Running"
                self.running_tasks[execution_uuid][
                    "current_step"
                ] = f"Worker {worker_id} assigned"
                self.running_tasks[execution_uuid]["updated_at"] = time.time()

                # Create wrapper task so we can cancel it if requested
                if self._executor_callback:
                    # Run execution callback
                    run_coro = self._executor_callback(
                        execution_uuid, job_id, variables, trigger_source
                    )
                    run_task = asyncio.create_task(run_coro)
                    self.running_tasks[execution_uuid]["asyncio_task"] = run_task

                    try:
                        await asyncio.wait_for(
                            run_task, timeout=float(settings.JOB_TIMEOUT_SECONDS)
                        )
                    except asyncio.TimeoutError:
                        logger.error(
                            f"Execution {execution_uuid} timed out after {settings.JOB_TIMEOUT_SECONDS}s."
                        )
                        run_task.cancel()
                        if execution_uuid in self.running_tasks:
                            self.running_tasks[execution_uuid]["status"] = "Failed"
                            self.running_tasks[execution_uuid][
                                "current_step"
                            ] = "Execution timed out"
                    except asyncio.CancelledError:
                        logger.info(f"Execution {execution_uuid} was cancelled.")
                    except Exception as e:
                        logger.exception(
                            f"Execution {execution_uuid} encountered error in worker: {e}"
                        )
                    finally:
                        # Clean up task
                        if execution_uuid in self.running_tasks:
                            if (
                                self.running_tasks[execution_uuid]["status"]
                                == "Running"
                            ):
                                self.running_tasks[execution_uuid][
                                    "status"
                                ] = "Completed"
                                self.running_tasks[execution_uuid]["percentage"] = 100
                            self.running_tasks[execution_uuid][
                                "updated_at"
                            ] = time.time()

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} loop encountered error: {e}")
                await asyncio.sleep(1)

    def cancel_task(self, execution_uuid: str) -> bool:
        task_meta = self.running_tasks.get(execution_uuid)
        if not task_meta:
            return False

        task_meta["status"] = "Cancelled"
        task_meta["current_step"] = "Cancelled by user request"
        task_meta["updated_at"] = time.time()

        asyncio_task = task_meta.get("asyncio_task")
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            logger.info(
                f"Active task for execution {execution_uuid} has been cancelled."
            )
            return True
        return False

    def update_progress(self, execution_uuid: str, percentage: int, current_step: str):
        if execution_uuid in self.running_tasks:
            self.running_tasks[execution_uuid]["percentage"] = percentage
            self.running_tasks[execution_uuid]["current_step"] = current_step
            self.running_tasks[execution_uuid]["updated_at"] = time.time()

    def get_progress(self, execution_uuid: str) -> Optional[Dict[str, Any]]:
        task_meta = self.running_tasks.get(execution_uuid)
        if not task_meta:
            return None

        elapsed = time.time() - task_meta["started_at"]
        pct = task_meta["percentage"]

        # Estimate remaining time
        est_remaining = 0.0
        if pct > 0 and pct < 100:
            est_remaining = (elapsed / pct) * (100 - pct)

        return {
            "status": task_meta["status"],
            "percentage": pct,
            "current_step": task_meta["current_step"],
            "elapsed_seconds": round(elapsed, 2),
            "estimated_remaining_seconds": round(est_remaining, 2),
            "last_updated": task_meta["updated_at"],
        }

    def get_queue_size(self) -> int:
        return self.queue.qsize()

    def get_active_workers_count(self) -> int:
        # Number of running tasks that have status "Running"
        return sum(1 for t in self.running_tasks.values() if t["status"] == "Running")


# Global singleton instance of TaskQueue
task_queue = InMemoryPriorityTaskQueue()
